#!/usr/bin/env python3
import csv
import json
import math
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone

import requests

ENTRY = "quant-006"
START = datetime(2026, 10, 22, 0, 0, 0, tzinfo=timezone.utc)
END = datetime(2026, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
DECISION_HOURS = 6
TAG = "tennis"
MIN_EDGE = 0.02
MAX_SPREAD = 0.04
MAX_SHARES = 50
MAX_NOTIONAL = 50.0
MIN_SHARES = 5
MAX_OPEN = 20
MAX_OPEN_NOTIONAL = 500.0
FEE_FALLBACK = 0.05
HEADER = ["time_utc", "event_id", "market", "action", "side", "price",
          "price_source", "size", "fee", "pnl", "note"]
BASE = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE, "state.json")
LEDGER_PATH = os.path.join(BASE, "ledger.csv")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "quant-forward/1.0"})


class FetchError(Exception):
    pass


def utcnow():
    return datetime.now(timezone.utc)


def parse_dt(value):
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        out = datetime.fromisoformat(text)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
            try:
                out = datetime.strptime(text, fmt)
                break
            except ValueError:
                out = None
        if out is None:
            return None
    if out.tzinfo is None:
        out = out.replace(tzinfo=timezone.utc)
    return out.astimezone(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_json(url, params=None):
    last = None
    for attempt in range(3):
        try:
            resp = SESSION.get(url, params=params, timeout=25)
            if resp.status_code == 200:
                return resp.json()
            last = f"HTTP {resp.status_code}"
        except Exception as exc:
            last = str(exc)
        time.sleep(1.0 + attempt)
    raise FetchError(f"{url}: {last}")


def gamma_events(start, end):
    out = []
    offset = 0
    limit = 100
    for _ in range(50):
        params = {
            "tag_slug": TAG,
            "closed": "false",
            "start_time_min": iso(start),
            "start_time_max": iso(end),
            "limit": limit,
            "offset": offset,
        }
        last = None
        page = None
        for attempt in range(6):
            try:
                resp = SESSION.get("https://gamma-api.polymarket.com/events", params=params, timeout=40)
                if resp.status_code == 200:
                    page = resp.json()
                    break
                last = f"HTTP {resp.status_code}"
                if resp.status_code == 422 and limit > 50:
                    limit = 50
                time.sleep(1.5 * (attempt + 1))
            except Exception as exc:
                last = str(exc)
                time.sleep(1.5 * (attempt + 1))
        if page is None:
            raise FetchError(f"gamma events: {last}")
        if not isinstance(page, list) or not page:
            break
        out.extend(page)
        if len(page) < limit:
            break
        offset = len(out)
    return out


def gamma_event(event_id):
    data = http_json("https://gamma-api.polymarket.com/events", {"id": event_id})
    if isinstance(data, list) and data:
        return data[0]
    return None


def clob_book(token):
    book = http_json("https://clob.polymarket.com/book", {"token_id": token})
    asks = book.get("asks") or []
    bids = book.get("bids") or []
    ask = min(float(x["price"]) for x in asks) if asks else None
    bid = max(float(x["price"]) for x in bids) if bids else None
    ts = book.get("timestamp")
    return bid, ask, ts


def load_json_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            got = json.loads(value)
            return got if isinstance(got, list) else []
        except Exception:
            return []
    return []


def fee_rate(market):
    raw = market.get("feeSchedule")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = None
    if isinstance(raw, dict) and raw.get("rate") is not None:
        try:
            return float(raw["rate"])
        except Exception:
            pass
    return FEE_FALLBACK


def load_state():
    if not os.path.exists(STATE_PATH):
        return {"version": 1, "seen": {}, "last_run": None}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as fh:
            state = json.load(fh)
    except Exception:
        return {"version": 1, "seen": {}, "last_run": None}
    if not isinstance(state, dict):
        state = {}
    state.setdefault("version", 1)
    state.setdefault("seen", {})
    state.setdefault("last_run", None)
    return state


def save_state(state):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, STATE_PATH)


def ensure_ledger():
    if not os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH, "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerow(HEADER)


def ledger_keys():
    keys = set()
    if not os.path.exists(LEDGER_PATH):
        return keys
    with open(LEDGER_PATH, "r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            keys.add((row.get("event_id", ""), row.get("action", "")))
    return keys


def append_row(row):
    ensure_ledger()
    with open(LEDGER_PATH, "a", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerow([row[k] for k in HEADER])


def norm_name(value):
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode()
    text = text.lower()
    text = re.sub(r"[^a-z ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def elo_ratings():
    out = {}
    last_init = {}
    for tour, url in (
        ("atp", "https://tennisabstract.com/reports/atp_elo_ratings.html"),
        ("wta", "https://tennisabstract.com/reports/wta_elo_ratings.html"),
    ):
        resp = SESSION.get(url, timeout=30)
        if resp.status_code != 200:
            raise FetchError(f"{url}: HTTP {resp.status_code}")
        html = resp.text
        for row_html in re.findall(r"<tr>(.*?)</tr>", html, re.S):
            cells = [
                re.sub(r"<[^>]+>", "", cell).replace("&nbsp;", " ").strip()
                for cell in re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.S)
            ]
            if len(cells) < 4 or not cells[0].isdigit():
                continue
            try:
                rating = float(cells[3])
            except Exception:
                continue
            name = norm_name(cells[1])
            out[(tour, name)] = rating
            parts = name.split()
            if len(parts) >= 2:
                key = (tour, parts[-1] + " " + parts[0][0])
                last_init.setdefault(key, []).append(rating)
    return out, last_init


def elo_lookup(ratings, last_init, tour, name, allow_both=False):
    tours = [tour]
    if allow_both or tour == "itf":
        tours = ["atp", "wta"]
    found = []
    for one in tours:
        key = (one, norm_name(name))
        if key in ratings:
            found.append(ratings[key])
    if len(found) == 1:
        return found[0]
    if len(found) > 1:
        return None
    parts = norm_name(name).split()
    if len(parts) >= 2:
        for one in tours:
            cand = last_init.get((one, parts[-1] + " " + parts[0][0]), [])
            if len(cand) == 1:
                found.append(cand[0])
    if len(found) == 1:
        return found[0]
    return None


def winner_market(event):
    slug = event.get("slug") or ""
    for market in event.get("markets") or []:
        if market.get("slug") == slug:
            return market
    return None


def decide(event, ratings, last_init, now, decision, forced=False):
    slug = event.get("slug") or ""
    if not re.match(r"^(atp|wta|itf)-", slug):
        return None, "skip_slug"
    if "doubles" in slug.lower():
        return None, "skip_doubles"
    title = event.get("title") or ""
    if " vs " not in title.lower() or "/" in title:
        return None, "skip_not_singles"
    market = winner_market(event)
    if market is None:
        return None, "skip_no_winner_market"
    outcomes = load_json_list(market.get("outcomes"))
    tokens = load_json_list(market.get("clobTokenIds"))
    if len(outcomes) != 2 or len(tokens) != 2:
        return None, "skip_market_shape"
    tour = slug.split("-")[0]
    elo_a = elo_lookup(ratings, last_init, tour, outcomes[0], allow_both=(tour == "itf"))
    elo_b = elo_lookup(ratings, last_init, tour, outcomes[1], allow_both=(tour == "itf"))
    if elo_a is None or elo_b is None:
        return None, "skip_no_elo"
    books = []
    for token in tokens:
        try:
            bid, ask, ts = clob_book(token)
        except FetchError:
            raise
        if bid is None or ask is None:
            return None, "no_book"
        books.append((bid, ask, ts))
    if books[0][2] is None or books[1][2] is None:
        return None, "no_book"
    try:
        book_ts = datetime.fromtimestamp(min(int(books[0][2]), int(books[1][2])) / 1000.0, tz=timezone.utc)
    except Exception:
        return None, "bad_book_ts"
    if book_ts < decision:
        return None, "before_decision"
    if not forced and book_ts < now - timedelta(minutes=10):
        return None, "stale_book"
    p_a = 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))
    p = [p_a, 1.0 - p_a]
    rate = fee_rate(market)
    candidates = []
    for idx in (0, 1):
        bid, ask, _ = books[idx]
        if ask <= 0.01 or ask >= 0.99:
            continue
        if ask - bid > MAX_SPREAD:
            continue
        fee = rate * ask * (1.0 - ask)
        edge = p[idx] - ask - fee
        candidates.append((edge, idx, ask, bid, fee))
    if not candidates:
        return None, "no_candidate"
    candidates.sort(reverse=True)
    edge, idx, ask, bid, fee = candidates[0]
    if edge <= MIN_EDGE:
        return None, "no_edge"
    size = min(MAX_SHARES, int(MAX_NOTIONAL / ask))
    if size < MIN_SHARES:
        return None, "too_small"
    total_fee = fee * size
    source = f"clob_book:{iso(book_ts)}"
    note = (
        f"p={p[idx]:.4f}; pA={p_a:.4f}; eloA={elo_a:.1f}; eloB={elo_b:.1f}; "
        f"bid={bid:.4f}; ask={ask:.4f}; spread={ask-bid:.4f}; edge={edge:.4f}; "
        f"rate={rate:.4f}; book_ts={iso(book_ts)}"
    )
    row = {
        "time_utc": iso(now),
        "event_id": str(event.get("id")),
        "market": slug,
        "action": "开",
        "side": outcomes[idx],
        "price": f"{ask:.6f}",
        "price_source": source,
        "size": str(size),
        "fee": f"{total_fee:.6f}",
        "pnl": "0",
        "note": note,
    }
    position = {
        "status": "open",
        "slug": slug,
        "market": slug,
        "token": tokens[idx],
        "outcome_index": idx,
        "outcome": outcomes[idx],
        "entry_price": ask,
        "size": size,
        "fee": total_fee,
        "entry_time": iso(now),
        "price_source": source,
        "decision_time": iso(now - timedelta(hours=DECISION_HOURS)) if forced else iso(now),
    }
    return (row, position), "open"


def settle_one(state, event_id, keys):
    pos = state["seen"].get(event_id)
    if not pos or pos.get("status") != "open":
        return False
    event = gamma_event(event_id)
    if not event:
        return False
    slug = pos.get("market")
    market = None
    for item in event.get("markets") or []:
        if item.get("slug") == slug:
            market = item
            break
    if market is None or not market.get("closed"):
        return False
    prices = load_json_list(market.get("outcomePrices"))
    if len(prices) != 2:
        return False
    try:
        p0 = float(prices[0])
        p1 = float(prices[1])
    except Exception:
        return False
    if p0 == 1.0 and p1 == 0.0:
        payout = 1.0 if pos["outcome_index"] == 0 else 0.0
    elif p0 == 0.0 and p1 == 1.0:
        payout = 1.0 if pos["outcome_index"] == 1 else 0.0
    elif p0 == 0.5 and p1 == 0.5:
        payout = 0.5
    else:
        return False
    if (event_id, "结算") in keys:
        old_payout = pos.get("payout")
        if old_payout is None:
            pos["status"] = "settled"
            pos["payout"] = payout
            return False
        if old_payout == payout:
            return False
        old_pnl = pos.get("pnl", 0.0)
        new_pnl = pos["size"] * (payout - pos["entry_price"]) - pos["fee"]
        row = {
            "time_utc": iso(utcnow()),
            "event_id": event_id,
            "market": slug,
            "action": "更正",
            "side": pos.get("outcome", "YES"),
            "price": f"{payout:.6f}",
            "price_source": f"gamma_outcomePrices:{event_id}",
            "size": str(pos["size"]),
            "fee": "0",
            "pnl": f"{new_pnl - old_pnl:.6f}",
            "note": (
                f"replace settlement: old_payout={old_payout:.4f}; new_payout={payout:.4f}; "
                f"old_pnl={old_pnl:.6f}; new_pnl={new_pnl:.6f}"
            ),
        }
        append_row(row)
        pos["payout"] = payout
        pos["pnl"] = new_pnl
        return True
    pnl = pos["size"] * (payout - pos["entry_price"]) - pos["fee"]
    row = {
        "time_utc": iso(utcnow()),
        "event_id": event_id,
        "market": slug,
        "action": "结算",
        "side": pos.get("outcome", ""),
        "price": f"{payout:.6f}",
        "price_source": f"gamma_outcomePrices:{event_id}",
        "size": str(pos["size"]),
        "fee": "0",
        "pnl": f"{pnl:.6f}",
        "note": (
            f"gross={pos['size']*(payout-pos['entry_price']):.6f}; "
            f"fee_on_open={pos['fee']:.6f}; entry={pos['entry_price']:.4f}; payout={payout:.4f}"
        ),
    }
    append_row(row)
    keys.add((event_id, "结算"))
    pos["status"] = "settled"
    pos["payout"] = payout
    pos["pnl"] = pnl
    return True


def run_dry(now):
    events = gamma_events(now, now + timedelta(hours=7))
    ratings, last_init = elo_ratings()
    rows = []
    due = 0
    for event in events:
        start = parse_dt(event.get("startTime"))
        if start is None:
            continue
        decision = start - timedelta(hours=DECISION_HOURS)
        if decision > now or start <= now:
            continue
        due += 1
        try:
            got, status = decide(event, ratings, last_init, now, decision, forced=True)
        except FetchError as exc:
            print(f"[dry-run] fetch error {event.get('slug')}: {exc}", file=sys.stderr)
            continue
        if got:
            rows.append(got[0])
    print(f"DRY RUN {ENTRY} now={iso(now)} events_in_window={len(events)} due={due} rows={len(rows)}")
    for row in rows[:20]:
        print("DRY-RUN would append:", json.dumps(row, ensure_ascii=False))
    if len(rows) > 20:
        print(f"DRY-RUN ... {len(rows)-20} more rows")
    return 0


def main():
    now = utcnow()
    if os.environ.get("FORWARD_DRY_RUN") == "1":
        return run_dry(now)
    if now < START or now >= END + timedelta(days=7):
        return 0
    state = load_state()
    keys = ledger_keys()
    try:
        ratings, last_init = elo_ratings()
    except FetchError as exc:
        print(f"[{ENTRY}] elo fetch failed: {exc}", file=sys.stderr)
        state["last_run"] = iso(now)
        save_state(state)
        return 0
    try:
        query_start = max(START, now - timedelta(hours=2))
        query_end = min(END, now + timedelta(hours=48))
        events = gamma_events(query_start, query_end)
    except FetchError as exc:
        print(f"[{ENTRY}] gamma fetch failed: {exc}", file=sys.stderr)
        state["last_run"] = iso(now)
        save_state(state)
        return 0
    for event in events:
        event_id = str(event.get("id"))
        if event_id in state["seen"]:
            continue
        start = parse_dt(event.get("startTime"))
        if start is None:
            state["seen"][event_id] = {"status": "skipped", "reason": "no_start_time"}
            continue
        decision = start - timedelta(hours=DECISION_HOURS)
        if decision > now:
            continue
        if start <= now:
            state["seen"][event_id] = {"status": "skipped", "reason": "match_started"}
            continue
        if (event_id, "开") in keys:
            continue
        open_now = [p for p in state["seen"].values() if p.get("status") == "open"]
        if len(open_now) >= MAX_OPEN:
            continue
        if sum(p.get("size", 0) * p.get("entry_price", 0) for p in open_now) >= MAX_OPEN_NOTIONAL:
            continue
        try:
            got, status = decide(event, ratings, last_init, now, decision)
        except FetchError as exc:
            print(f"[{ENTRY}] book fetch failed {event.get('slug')}: {exc}", file=sys.stderr)
            continue
        if got:
            row, pos = got
            append_row(row)
            keys.add((event_id, "开"))
            state["seen"][event_id] = pos
            save_state(state)
        elif status not in ("no_book", "stale_book", "bad_book_ts"):
            state["seen"][event_id] = {"status": "skipped", "reason": status}
    for event_id in list(state["seen"].keys()):
        try:
            if settle_one(state, event_id, keys):
                save_state(state)
        except FetchError as exc:
            print(f"[{ENTRY}] settle fetch failed {event_id}: {exc}", file=sys.stderr)
    state["last_run"] = iso(now)
    save_state(state)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[{ENTRY}] fatal: {exc}", file=sys.stderr)
        sys.exit(0)
