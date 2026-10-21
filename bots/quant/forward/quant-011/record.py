#!/usr/bin/env python3
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

ENTRY = "quant-011"
START = datetime(2026, 10, 22, 0, 0, 0, tzinfo=timezone.utc)
END = datetime(2026, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
DECISION_HOURS = 6
TAG = "soccer"
P_HAT = 0.2546
MIN_EDGE = 0.005
MAX_SPREAD = 0.02
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
    for _ in range(40):
        page = http_json(
            "https://gamma-api.polymarket.com/events",
            {
                "tag_slug": TAG,
                "closed": "false",
                "start_time_min": iso(start),
                "start_time_max": iso(end),
                "limit": 100,
                "offset": offset,
            },
        )
        if not isinstance(page, list) or not page:
            break
        out.extend(page)
        if len(page) < 100:
            break
        offset += 100
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


def three_way_markets(event):
    base = event.get("slug") or ""
    markets = event.get("markets") or []
    draw = None
    wins = []
    for market in markets:
        slug = market.get("slug") or ""
        question = market.get("question") or ""
        if slug == base + "-draw" or "end in a draw" in question.lower():
            draw = market
        elif slug.startswith(base + "-") and re.search(r"\bwin on \d{4}-\d{2}-\d{2}\?$", question):
            wins.append(market)
    if draw is None or len(wins) != 2:
        return None, None
    return draw, wins


def decide(event, now, decision, forced=False):
    draw, wins = three_way_markets(event)
    if draw is None:
        return None, "skip_not_three_way"
    draw_out = load_json_list(draw.get("outcomes"))
    draw_tokens = load_json_list(draw.get("clobTokenIds"))
    if len(draw_out) != 2 or len(draw_tokens) != 2:
        return None, "skip_draw_shape"
    if str(draw_out[0]).lower() != "yes" or str(draw_out[1]).lower() != "no":
        return None, "skip_draw_outcomes"
    win_tokens = []
    for market in wins:
        outs = load_json_list(market.get("outcomes"))
        toks = load_json_list(market.get("clobTokenIds"))
        if len(outs) != 2 or len(toks) != 2 or str(outs[0]).lower() != "yes":
            return None, "skip_win_shape"
        win_tokens.append(toks[0])
    all_tokens = [draw_tokens[0], win_tokens[0], win_tokens[1]]
    books = []
    for token in all_tokens:
        try:
            bid, ask, ts = clob_book(token)
        except FetchError:
            raise
        if bid is None or ask is None or ts is None:
            return None, "no_book"
        books.append((bid, ask, ts))
    try:
        book_ts = datetime.fromtimestamp(min(int(x[2]) for x in books) / 1000.0, tz=timezone.utc)
    except Exception:
        return None, "bad_book_ts"
    if book_ts < decision:
        return None, "before_decision"
    if not forced and book_ts < now - timedelta(minutes=10):
        return None, "stale_book"
    draw_bid, draw_ask, _ = books[0]
    if draw_ask <= 0.01 or draw_ask >= 0.99:
        return None, "no_candidate"
    if draw_ask - draw_bid > MAX_SPREAD:
        return None, "wide_spread"
    home_ask = books[1][1]
    away_ask = books[2][1]
    denom = home_ask + draw_ask + away_ask
    if denom <= 0:
        return None, "bad_qd"
    q_d = draw_ask / denom
    if not (0.05 <= q_d <= 0.60):
        return None, "bad_qd"
    rate = fee_rate(draw)
    fee = rate * draw_ask * (1.0 - draw_ask)
    edge = P_HAT - draw_ask - fee - 0.005
    if edge <= MIN_EDGE:
        return None, "no_edge"
    size = min(MAX_SHARES, int(MAX_NOTIONAL / draw_ask))
    if size < MIN_SHARES:
        return None, "too_small"
    total_fee = fee * size
    source = f"clob_book:{iso(book_ts)}"
    note = (
        f"p_hat={P_HAT:.4f}; qD={q_d:.4f}; bid={draw_bid:.4f}; ask={draw_ask:.4f}; "
        f"spread={draw_ask-draw_bid:.4f}; edge={edge:.4f}; rate={rate:.4f}; "
        f"home_ask={home_ask:.4f}; away_ask={away_ask:.4f}; book_ts={iso(book_ts)}"
    )
    row = {
        "time_utc": iso(now),
        "event_id": str(event.get("id")),
        "market": draw.get("slug") or "",
        "action": "开",
        "side": "YES",
        "price": f"{draw_ask:.6f}",
        "price_source": source,
        "size": str(size),
        "fee": f"{total_fee:.6f}",
        "pnl": "0",
        "note": note,
    }
    position = {
        "status": "open",
        "slug": event.get("slug") or "",
        "market": draw.get("slug") or "",
        "token": draw_tokens[0],
        "entry_price": draw_ask,
        "size": size,
        "fee": total_fee,
        "entry_time": iso(now),
        "price_source": source,
        "q_d": q_d,
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
        payout = 1.0
    elif p0 == 0.0 and p1 == 1.0:
        payout = 0.0
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
        "side": "YES",
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
            got, status = decide(event, now, decision, forced=True)
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
            got, status = decide(event, now, decision)
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
