"""Pure, offline request-planning contract. No HTTP, orders, processes or clocks.

The existing root/hourly task supplies UTC milliseconds and owns all reads.
Persist one checkpoint containing this scheduler and role04's virtual ledger.
Functions return copies: caller performs a revision-checked atomic replacement.
"""
from copy import deepcopy
from decimal import Decimal, localcontext, InvalidOperation
from datetime import timezone
from email.utils import parsedate_to_datetime
import re
import json
from hashlib import sha256 as hash_bytes

HOUR_MS = 3_600_000
SOURCES = ("quote_pair", "funding_history")
SCHEMA = "r21.forward-checkpoint.v1"


def new_checkpoint():
    return {
        "schema": SCHEMA, "revision": 0, "protocol_sha256": None,
        "root_lock": None, "entry": None, "ledger": None,
        "source_status": {
            k: {"last_attempt_ms": None, "inflight": None, "halted": False,
                "blocked_until_ms": None, "last_outcome": None}
            for k in SOURCES
        },
        "funding_schedule": None, "last_snapshot": None,
        "source_errors": [], "stop_requested": False,
        "first_30_review_recorded": False,
        "feasibility_failure": None,
    }


def _copy(s):
    if s.get("schema") != SCHEMA:
        raise ValueError("Unsupported checkpoint schema; explicit migration required")
    n = deepcopy(s)
    n["revision"] += 1
    return n


def lock_protocol(s, sha256, locked_at_ms, artifact_manifest_sha256=None):
    """Root-only workflow step. This is an audit contract, not authentication."""
    if not re.fullmatch(r"[a-f0-9]{64}", sha256):
        raise ValueError("Expected lowercase SHA256")
    if s["root_lock"] is not None:
        raise ValueError("Protocol lock is immutable; a new protocol needs new state")
    n = _copy(s)
    n["protocol_sha256"] = sha256
    if artifact_manifest_sha256 is not None and not re.fullmatch(r"[a-f0-9]{64}", artifact_manifest_sha256):
        raise ValueError("Invalid artifact manifest SHA256")
    n["root_lock"] = {
        "protocol_sha256": sha256, "locked_at_ms": locked_at_ms,
        "authorized_by": "root", "entry_authorized": True,
    }
    if artifact_manifest_sha256 is not None:
        n["root_lock"]["artifact_manifest_sha256"] = artifact_manifest_sha256
    return n


def validate_ledger_money(ledger):
    """Fail closed on restored money/event corruption, using role04 precision 50.

    Sum sorted settlements deterministically. Any exotic precision-order conflict
    needs reconciliation, never a tolerance-based silent cash adjustment.
    """
    def dec(value):
        try:
            x = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError("Invalid ledger decimal")
        if not x.is_finite():
            raise ValueError("Nonfinite ledger decimal")
        return x
    with localcontext() as ctx:
        ctx.prec = 50
        quantity = dec(ledger["entry"]["quantity"])
        if quantity <= 0 or set(ledger["accounts"]) != {"0.003", "0.006"}:
            raise ValueError("Invalid quantity or missing cost account")
        total = Decimal(0)
        for key, event in sorted(ledger["funding_events"].items(), key=lambda kv: int(kv[0].rsplit(":", 1)[1])):
            timestamp = int(key.rsplit(":", 1)[1])
            if event["funding_time_ms"] != timestamp:
                raise ValueError("Funding key/time mismatch")
            rate, mark, cash = dec(event["rate"]), dec(event["mark"]), dec(event["cash"])
            if mark <= 0 or cash != quantity * rate * mark:
                raise ValueError("Funding event cash mismatch")
            total += cash
        for account in ledger["accounts"].values():
            if dec(account["funding_cash"]) != total:
                raise ValueError("Account funding cash differs from event sum")


def attach_ledger(s, ledger):
    """Attach role04's validated entry, or commit its whole funding-batch update.

    No entry is manufactured from a quote or scheduler result. The role04 ledger
    owns monetary accounting and the only funding-event deduplication map.
    """
    if s["root_lock"] is None:
        raise ValueError("No root protocol lock")
    if ledger["protocol_sha256"] != s["protocol_sha256"]:
        raise ValueError("Protocol mismatch")
    if ledger["root_lock"] != s["root_lock"]:
        raise ValueError("Root-lock mismatch")
    entry = ledger["entry"]
    if entry["entry_time_ms"] < s["root_lock"]["locked_at_ms"]:
        raise ValueError("Entry precedes root lock")
    if s["entry"] is not None and entry != s["entry"]:
        raise ValueError("Cannot replace an existing virtual entry")
    old = s["ledger"] or {"funding_events": {}}
    for key, value in old["funding_events"].items():
        if ledger["funding_events"].get(key) != value:
            raise ValueError("Previously committed event changed or disappeared")
    for key in ledger["funding_events"]:
        symbol, raw_ms = key.rsplit(":", 1)
        if symbol != "ETHUSDT" or int(raw_ms) <= entry["entry_time_ms"]:
            raise ValueError("Invalid funding key or entry-boundary violation")
    last = max([entry["entry_time_ms"]] +
               [int(k.rsplit(":", 1)[1]) for k in ledger["funding_events"]])
    if ledger["last_funding_time_ms"] != last:
        raise ValueError("Ledger cursor does not match committed events")
    validate_ledger_money(ledger)
    n = _copy(s)
    n["entry"], n["ledger"] = deepcopy(entry), deepcopy(ledger)
    return n


def record_schedule(s, next_funding_time_ms, observed_at_ms, source_ref):
    """Use a newly observed exchange schedule; never assume eight hours forever."""
    if next_funding_time_ms <= observed_at_ms or not source_ref:
        raise ValueError("Schedule must be a future source-observed time")
    old = s["funding_schedule"]
    if old and observed_at_ms < old["observed_at_ms"]:
        raise ValueError("Do not overwrite a newer observation")
    n = _copy(s)
    n["funding_schedule"] = {
        "next_funding_time_ms": next_funding_time_ms,
        "observed_at_ms": observed_at_ms, "source_ref": source_ref,
    }
    return n


def _ready(status, now_ms):
    if status["halted"]:
        return False, "halted; root must reconcile new permission/source evidence"
    if status["inflight"] is not None:
        return False, "uncertain or pending request; reconcile before another read"
    until = status["blocked_until_ms"]
    if until is not None and now_ms < until:
        return False, f"explicit reset not reached: {until}"
    last = status["last_attempt_ms"]
    if last is not None and now_ms < last + HOUR_MS:
        return False, f"hourly request budget not due: {last + HOUR_MS}"
    return True, None


def due_work(s, now_ms):
    """Return an informational plan, never execute or initialize a virtual entry."""
    if s.get("schema") != SCHEMA:
        raise ValueError("Unsupported schema")
    result = {"actions": [], "blocked": {}, "required_information": [],
              "accepted_funding_events": 0, "review_first_30": False,
              "forced_stop": False}
    if s["stop_requested"]:
        result["blocked"]["all"] = "User stop or replacement instruction"
        result["forced_stop"] = True
        return result
    if s["root_lock"] is None:
        result["blocked"]["all"] = "Root must lock protocol before entry observations"
        return result
    ok, reason = _ready(s["source_status"]["quote_pair"], now_ms)
    if ok:
        result["actions"].append({
            "source": "quote_pair",
            "purpose": "entry_reference" if s["entry"] is None else "valuation",
            "authorization": "one public spot/perpetual paired observation only",
        })
    else:
        result["blocked"]["quote_pair"] = reason
    if s["entry"] is None:
        result["blocked"]["funding_history"] = "No validated virtual entry"
        return result
    ledger = s["ledger"]
    count = len(ledger["funding_events"])
    result["accepted_funding_events"] = count
    result["review_first_30"] = count >= 30 and not s["first_30_review_recorded"]
    schedule = s["funding_schedule"]
    last = ledger["last_funding_time_ms"]
    if schedule is None or schedule["next_funding_time_ms"] <= last:
        result["required_information"].append(
            "Obtain next funding time through a separately budgeted public schedule observation")
        return result
    if now_ms < schedule["next_funding_time_ms"]:
        result["blocked"]["funding_history"] = "Expected settlement not due"
        return result
    ok, reason = _ready(s["source_status"]["funding_history"], now_ms)
    if ok:
        result["actions"].append({
            "source": "funding_history", "symbol": "ETHUSDT",
            "startTime": last + 1, "endTime": now_ms, "limit": 1000,
            "purpose": "actual funding records conditional on virtual quantity",
        })
    else:
        result["blocked"]["funding_history"] = reason
    return result


def reserve_request(s, source, request_id, now_ms):
    """Persist this state BEFORE root invokes a read. A reservation consumes quota."""
    if source not in SOURCES or not request_id:
        raise ValueError("Unknown source or empty request id")
    allowed = {x["source"] for x in due_work(s, now_ms)["actions"]}
    if source not in allowed:
        raise ValueError("Request is not due")
    n = _copy(s)
    status = n["source_status"][source]
    status["last_attempt_ms"] = now_ms
    status["inflight"] = {"request_id": request_id, "started_at_ms": now_ms}
    return n


def parse_retry_after(value, received_at_ms):
    """HTTP delta-seconds or HTTP-date only; absent/unparseable means no retry."""
    if value is None:
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d+", text):
        return received_at_ms + int(text) * 1000
    try:
        date = parsedate_to_datetime(text)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        return max(received_at_ms, int(date.timestamp() * 1000))
    except (TypeError, ValueError, OverflowError):
        return None


def complete_request(s, source, request_id, outcome, completed_at_ms,
                     response_ref=None, retry_after=None, explicit_reset_ms=None):
    """Return a proposed completion. Commit with ledger changes in ONE envelope.

    outcome: ok, empty, invalid, forbidden, rate_limited, uncertain.
    A 403 or 429 without explicit reset stays halted; no endpoint fallback.
    """
    if source not in SOURCES:
        raise ValueError("Unknown source")
    status = s["source_status"][source]
    pending = status["inflight"]
    if pending is None or pending["request_id"] != request_id:
        raise ValueError("Completion does not match reserved request")
    if completed_at_ms < pending["started_at_ms"]:
        raise ValueError("Completion precedes request")
    if outcome not in {"ok", "empty", "invalid", "forbidden", "rate_limited", "uncertain"}:
        raise ValueError("Unknown outcome")
    if outcome == "ok" and not response_ref:
        raise ValueError("Successful observation needs a persisted response reference")
    n = _copy(s)
    status = n["source_status"][source]
    status["last_outcome"] = outcome
    if outcome != "uncertain":
        status["inflight"] = None
    if outcome == "forbidden":
        status["halted"] = True
    elif outcome == "rate_limited":
        until = explicit_reset_ms
        if until is None:
            until = parse_retry_after(retry_after, completed_at_ms)
        if until is None:
            status["halted"] = True
        else:
            status["blocked_until_ms"] = max(completed_at_ms, until)
    elif outcome in {"ok", "empty", "invalid"}:
        status["blocked_until_ms"] = None
    if outcome not in {"ok", "empty"}:
        n["source_errors"].append({
            "source": source, "request_id": request_id, "outcome": outcome,
            "at_ms": completed_at_ms, "response_ref": response_ref,
            "next_allowed_ms": status["blocked_until_ms"],
        })
    if source == "quote_pair" and outcome == "ok":
        n["last_snapshot"] = {"observed_at_ms": completed_at_ms,
                              "response_ref": response_ref}
    return n


def assert_revision(current, expected_revision):
    """Caller checks immediately before atomic save; never merge stale state."""
    if current["revision"] != expected_revision:
        raise ValueError("Checkpoint changed; reread and reconcile, do not replay blindly")


def validate_restored(s):
    """Fail closed on incomplete checkpoint/ledger disagreement after restart."""
    if s.get("schema") != SCHEMA or set(s["source_status"]) != set(SOURCES):
        raise ValueError("Invalid checkpoint")
    if (s["entry"] is None) != (s["ledger"] is None):
        raise ValueError("Entry/ledger mismatch")
    if s["ledger"] is not None:
        if s["entry"] != s["ledger"]["entry"]:
            raise ValueError("Entry mirror mismatch")
        # Reuse full ledger identity/cursor checks without changing the state.
        attach_ledger(s, s["ledger"])
    return True


REQUIRED_ARTIFACTS = {
    "04-protocol/output/virtual_ledger.py", "04-protocol/output/protocol-config.json",
    "05-quotes/output/quote_audit.py", "06-scheduler/output/scheduler.py",
    "08-criteria/output/criteria.json", "08-criteria/output/criteria.py",
}


def verified_due_work(s, now_ms, manifest_bytes, artifact_bytes):
    """Production resume gate; root supplies fresh filesystem bytes, not cached hashes.

    Manifest: {"schema":"r21.forward-artifact-manifest.v1", "sha256":{path:hex}}.
    Paths are relative to the frozen r21 bundle. Exclude mutable state and manifest
    itself. This function performs no file/network reads and cannot grant root lock.
    """
    validate_restored(s)
    lock = s.get("root_lock") or {}
    expected = lock.get("artifact_manifest_sha256")
    if not expected or hash_bytes(manifest_bytes).hexdigest() != expected:
        raise ValueError("Missing or changed artifact manifest lock")
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema") != "r21.forward-artifact-manifest.v1":
        raise ValueError("Unsupported artifact manifest")
    hashes = manifest["sha256"]
    if not REQUIRED_ARTIFACTS.issubset(hashes):
        raise ValueError("Manifest does not cover required protocol artifacts")
    for path, digest in hashes.items():
        if path.startswith("/") or ".." in path.split("/"):
            raise ValueError("Artifact path outside frozen bundle")
        if path not in artifact_bytes or hash_bytes(artifact_bytes[path]).hexdigest() != digest:
            raise ValueError("Artifact missing or hash changed: " + path)
    return due_work(s, now_ms)


def record_feasibility_failure(s, observed_at_ms, evidence_ref):
    """Permanently latch observed nonpositive margin; later recovery cannot clear it.

    Root calls this only for a validated role04 nonpositive-margin observation.
    Subsequent ledger continuation is explicitly counterfactual, never feasible-path.
    """
    if s["entry"] is None or observed_at_ms < s["entry"]["entry_time_ms"] or not evidence_ref:
        raise ValueError("Failure observation requires an entry and source evidence")
    if s["feasibility_failure"] is not None:
        return deepcopy(s)
    n = _copy(s)
    n["feasibility_failure"] = {"observed_at_ms": observed_at_ms,
        "evidence_ref": evidence_ref, "reason": "observed_nonpositive_margin",
        "continuation_mode": "counterfactual_only"}
    return n
