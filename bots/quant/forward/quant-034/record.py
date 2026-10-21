#!/usr/bin/env python3
"""quant-034 deterministic paper recorder.

Run hourly from the repository root:
    python3 bots/quant/forward/quant-034/record.py

Dry run (prints rows, writes nothing):
    FORWARD_DRY_RUN=1 python3 bots/quant/forward/quant-034/record.py

The plan is frozen in PLAN.md.  This script only reads public Polymarket
endpoints (Gamma, CLOB, data-api) and never places orders or uses a wallet.
"""

import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

START = datetime(2026, 10, 22, 0, 0, 0, tzinfo=timezone.utc)
END = datetime(2026, 11, 5, 0, 0, 0, tzinfo=timezone.utc)
DRY = os.environ.get("FORWARD_DRY_RUN") == "1"

BASE = Path(__file__).resolve().parent
LEDGER = BASE / "ledger.csv"
STATE = BASE / "state.json"
HEADER = ["time_utc", "event_id", "market", "action", "side", "price",
          "price_source", "size", "fee", "pnl", "note"]

# Registration snapshot and network fallback (2026-10-21T05:16Z): one market
# per event, chosen by the mechanical rule in PLAN.md (pool >= $20/day,
# rewards_min_size == 20, max_spread >= 3c, per-market fee rate > 0, endDate
# >= 2026-11-20, both outcome prices in [0.10,0.90]).  At the first run after
# START the recorder re-applies select_markets() to the live snapshot, stores
# up to 40 cids in state["selected"], and uses that list.  Maintenance
# threshold is $10/day.
MARKETS = [
    "0xbe91fb5f94bce3e9e0f8e1ee13033c2e3a35bb9bededbbb43de5bf28d79478b0",
    "0x3acd686a68c85bd79724db76c5f681003dd6cae2e9a033b7a27136e672926267",
    "0x3da9e515e164ecf0c795a7ee039ccdf28ab304e009b3870fbd83ce90355c03e1",
    "0x42d1fefc149165e314c36cdcb0ec3dc94abe2cc55c3914bffdd96cf764eb6eb8",
    "0x4c5399503e0f3d98161d6877f861557993317860d45d36b55870f4ea2cb74b4e",
    "0x4dd20ba2fdd0aee411252a7f1c005673086e943550fd375a616fec8c897a5371",
    "0x6a15853865d5fa9d289bdc52c68d03c7b9fa3fa116b7b96ed586845836434fe5",
    "0xc6e411dc124805a9bbe452a0fd1391b6498373747e7587049990d1df4113a9c2",
    "0xd199af947c28d67b6869dd641b9301a2819d40a2647da88e9b6d7c90b10b9dfe",
    "0x26f021f7eed8dda3b99bcb4163cf1b28d1cdd921da4c8922799fb91541da8147",
    "0x5480ecf5de966b99184a0e442103d4c7ab145855229ac073bb17861c3910af5d",
    "0xd5137800eeb19473b1cc6cfe2b5377e807519fe71b4cdd387f0c68e148b99763",
    "0xdb0eaf3f75d4f9b3f0116504e131adc0432a427bc1f74133dc0911e976330056",
    "0x8c76cbb830ac6280d44ed51400ec51baf9f166606fe4c75ebb20239b26ce2407",
    "0xea0fd6ed032120efdbad9363e022c4b334b7a01e136c981e74b96ccf26f59e7e",
    "0x9200ca2fe44fe5c867bbcee41e9437fd54acfc1706d5ceff52ae11921439c84c",
    "0xb7e7ce498a7a75240e54b210fbc656a8b6cb0b46029e33f626a566b6215a76c3",
    "0x5d55f32e24d98f7fc4604ccfa9f7fc13640fbce99df4f76bf60ed449faf8975d",
    "0x7fafeb4e1a61a52f4705bbb9b6b739d18c46d03bf8cc285ac331997f6be4f334",
    "0x1598d9ae1a10d2c1520d9dddc437b6bc32c73d580356f2760a6eb63922b75ec9",
    "0x1c7539a2a44e84e9b5971ba9937f57542e114dcec2500cb3fb862327bbf9e2fd",
    "0xa73af3849cb731ec3e16c656be32df9189629d7e41fef33dbef8ccc8e3478ada",
    "0x34346c899f1b4b117e6c400f80b36a9f30f355dc1274e8075cb0fb09c7a14603",
    "0x8652314642ea8e1b8b1f5fded33bd3deb328fff284b5f8d015ef62e0c39cae3c",
    "0xaef9dfe556082b10a374bee22470df845528e752cf74a25585131b434d2ad61c",
    "0x429ad9c277f9613720d27edbb9d7e68ef6cac4fb69d94fa91651cbdf8f786e6a",
    "0x9668e92f98ea6db7b505c54acfd5cbff6ce7e104cf51a92a459b7aa32228494c",
    "0xa9f05e47899ca6878d798795a84a7ce9b483d900d11fbf732fe8d969bb41b427",
    "0xb4625976d6318a7373c9bee1d33ef48ce5ee10ca05e4d5d20a2aa8304daadcb9",
    "0xd3162486c8aeccf42a6d4aa3ec8d21f865a0eb8cada144ddd4e284f05a093daa",
    "0xec79335bee42601d2bb8642eedf98905bef8cf028ddda91e73d8b78fb4f880aa",
    "0x65c7002c05e9ad53c34c17649c36e59d112e770c20ceeea598ccb3b92161b6d6",
    "0xc439ddda67d1d2c5275e54b01691bc947051ac9a9bfe48364fe2a4d98c593b56",
    "0x10502c298452a3301280fdacb2e3a17d88f79b773bae5ef190c67c04be662d89",
    "0x28c8f300e3c6d4d4434f5e7e3b313b9bf41ba6ae656163d1fdabb27f7eb00800",
    "0x273bfff7e975966338cf1d2c8c9485175e5c019a1d865be8a7f6ccf5bfae26bf",
    "0x7a9b9fc81b9945c6adcf6f3d731627823aa96281096533e7b40ed6d86844637b",
]

QUOTE_SIZE = 20.0
MAX_INVENTORY = 40.0
MIN_POOL = 10.0
MAX_SPREAD_MIN = 3.0
STALE_BOOK_MS = 15 * 60 * 1000


def utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt(x):
    if x is None:
        return "0"
    return f"{float(x):.6f}".rstrip("0").rstrip(".") or "0"


def http_json(method, url, **kwargs):
    last = None
    for attempt in range(3):
        try:
            resp = requests.request(method, url, timeout=30,
                                    headers={"User-Agent": "quant-034-forward/1.0"},
                                    **kwargs)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001 - network errors are data, not crashes
            last = exc
            time.sleep(1.0 + attempt)
    raise last


def uid(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:20]


def make_row(now, cid, market, action, side, price, source, size, fee, pnl, note, row_uid):
    return {
        "time_utc": iso(now),
        "event_id": cid,
        "market": market or cid,
        "action": action,
        "side": side,
        "price": fmt(price),
        "price_source": source,
        "size": fmt(size),
        "fee": fmt(fee),
        "pnl": fmt(pnl),
        "note": f"uid:{row_uid};{note}",
    }


def parse_levels(book):
    bids = sorted(((float(x["price"]), float(x["size"])) for x in book.get("bids", [])),
                  key=lambda x: -x[0])
    asks = sorted(((float(x["price"]), float(x["size"])) for x in book.get("asks", [])),
                  key=lambda x: x[0])
    return bids, asks


def floor_tick(value, tick):
    return round(int(value / tick + 1e-9) * tick, 8)


def target_quote(book, tick, max_spread, now_ms):
    if not book:
        return None
    ts = int(book.get("timestamp") or 0)
    if ts <= 0 or now_ms - ts > STALE_BOOK_MS or ts > now_ms + 60 * 1000:
        return None
    bids, asks = parse_levels(book)
    if not bids or not asks:
        return None
    best_bid, best_ask = bids[0][0], asks[0][0]
    if best_bid <= 0 or best_ask <= 0 or best_ask <= best_bid:
        return None
    mid = (best_bid + best_ask) / 2.0
    if not (0.10 <= mid <= 0.90):
        return None
    bid = floor_tick(min(best_ask - tick, mid - 0.01), tick)
    if bid <= 0:
        return None
    spread_cents = (mid - bid) * 100.0
    if spread_cents < -1e-9 or spread_cents > max_spread + 1e-9:
        return None
    return {"price": bid, "mid": mid, "spread_cents": spread_cents, "ts": ts}


def queue_ahead(book, price):
    bids, _ = parse_levels(book)
    return sum(size for p, size in bids if p >= price - 1e-9)


def score(v, s):
    if v <= 0 or s < 0 or s >= v:
        return 0.0
    return ((v - s) / v) ** 2


def q_min(q1, q2, mid):
    if 0.10 <= mid <= 0.90:
        return max(min(q1, q2), max(q1 / 3.0, q2 / 3.0))
    return min(q1, q2)


def book_mid(book):
    bids, asks = parse_levels(book)
    if not bids or not asks:
        return None
    return (bids[0][0] + asks[0][0]) / 2.0


def q_share(quotes, book_yes, book_no, max_spread):
    mid_y, mid_n = book_mid(book_yes), book_mid(book_no)
    if mid_y is None or mid_n is None:
        return 0.0
    q1 = q2 = 0.0
    for side, mid in (("yes", mid_y), ("no", mid_n)):
        q = quotes.get(side)
        if not q:
            continue
        s = (mid - q["price"]) * 100.0
        value = score(max_spread, s) * q["remaining"]
        if side == "yes":
            q1 += value
        else:
            q2 += value
    own = q_min(q1, q2, mid_y)
    yb, ya = parse_levels(book_yes)
    nb, na = parse_levels(book_no)
    other1 = other2 = 0.0
    for p, size in yb:
        other1 += score(max_spread, (mid_y - p) * 100.0) * size
    for p, size in na:
        other1 += score(max_spread, (p - mid_n) * 100.0) * size
    for p, size in ya:
        other2 += score(max_spread, (p - mid_y) * 100.0) * size
    for p, size in nb:
        other2 += score(max_spread, (mid_n - p) * 100.0) * size
    other = q_min(other1, other2, mid_y)
    total = own + other
    return own / total if total > 0 else 0.0


def new_market_state():
    return {
        "quotes": {"yes": None, "no": None},
        "inventory": {"yes": 0.0, "no": 0.0},
        "avg_cost": {"yes": 0.0, "no": 0.0},
        "filled_today": {"yes": 0.0, "no": 0.0},
        "day": None,
        "last_trade_ts": int(START.timestamp()),
        "seen": [],
        "reward_samples": {},
        "day_rebate": {},
        "pools": {},
        "finalized_days": [],
        "cfg": None,
        "config_day": None,
        "quote_seq": {"yes": 0, "no": 0},
        "last_mid": None,
        "paused_until": 0,
        "liquidated": False,
    }


def load_state():
    if STATE.exists():
        try:
            data = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    else:
        data = {}
    data.setdefault("version", 1)
    data.setdefault("markets", {})
    data.setdefault("finalized", False)
    data.setdefault("config_day", None)
    data.setdefault("selected", [])
    for cid in MARKETS:
        data["markets"].setdefault(cid, new_market_state())
    for cid in data.get("selected") or []:
        data["markets"].setdefault(cid, new_market_state())
    return data


def save_state(state):
    if DRY:
        return
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, STATE)


def append_rows(rows):
    if not rows:
        return
    existing = set()
    if LEDGER.exists() and LEDGER.stat().st_size:
        with LEDGER.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                for token in (row.get("note") or "").split(";"):
                    if token.startswith("uid:"):
                        existing.add(token[4:])
    new_rows = [r for r in rows if r["note"].split("uid:", 1)[1].split(";", 1)[0] not in existing]
    if not new_rows:
        return
    if DRY:
        writer = csv.DictWriter(sys.stdout, fieldnames=HEADER)
        for row in new_rows:
            writer.writerow({k: row[k] for k in HEADER})
        return
    if not (LEDGER.exists() and LEDGER.stat().st_size):
        with LEDGER.open("w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerow(HEADER)
    with LEDGER.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADER)
        for row in new_rows:
            writer.writerow({k: row[k] for k in HEADER})


def fetch_books(tokens):
    if not tokens:
        return {}
    try:
        data = http_json("POST", "https://clob.polymarket.com/books",
                         json=[{"token_id": t} for t in tokens])
        if isinstance(data, list):
            return {str(b.get("asset_id")): b for b in data}
    except Exception as exc:  # noqa: BLE001
        print(f"books batch failed: {exc}", file=sys.stderr)
    out = {}
    for token in tokens:
        try:
            out[token] = http_json("GET", "https://clob.polymarket.com/book",
                                   params={"token_id": token})
        except Exception as exc:  # noqa: BLE001
            print(f"book {token[:12]} failed: {exc}", file=sys.stderr)
    return out


def gamma_configs(cids):
    out = {}
    for i in range(0, len(cids), 20):
        chunk = cids[i:i + 20]
        params = [("condition_ids", c) for c in chunk]
        try:
            data = http_json("GET", "https://gamma-api.polymarket.com/markets", params=params)
            if isinstance(data, list):
                for m in data:
                    out[m.get("conditionId")] = m
        except Exception as exc:  # noqa: BLE001
            print(f"gamma chunk {i} failed: {exc}", file=sys.stderr)
    return out


def select_markets(now):
    """Apply the PLAN rule to the current public snapshot and return up to 40 cids."""
    rows = []
    cursor = ""
    while True:
        params = {"next_cursor": cursor} if cursor else None
        data = http_json("GET", "https://clob.polymarket.com/rewards/markets/current",
                         params=params)
        rows.extend(data.get("data") or [])
        cursor = data.get("next_cursor")
        if not cursor or cursor == "LTE=":
            break
    candidates = [r for r in rows
                  if (r.get("total_daily_rate") or 0) >= 20
                  and r.get("rewards_min_size") == 20
                  and (r.get("rewards_max_spread") or 0) >= 3]
    candidates.sort(key=lambda r: -(r.get("total_daily_rate") or 0))
    ids = [r["condition_id"] for r in candidates]
    gamma = gamma_configs(ids)
    by_id = {r["condition_id"]: r for r in rows}

    def prices(m):
        try:
            return [float(x) for x in json.loads(m.get("outcomePrices") or "[]")]
        except Exception:
            return []

    eligible = []
    for cid in ids:
        m, r = gamma.get(cid), by_id.get(cid)
        if not m or not r:
            continue
        if not (m.get("active") and not m.get("closed") and m.get("enableOrderBook")):
            continue
        if str(m.get("endDate") or "") < "2026-11-20":
            continue
        p = prices(m)
        if len(p) != 2 or not all(0.10 <= x <= 0.90 for x in p):
            continue
        fee = m.get("feeSchedule") or {}
        if float(fee.get("rate") or 0) <= 0:
            continue
        try:
            tokens = json.loads(m.get("clobTokenIds") or "[]")
        except Exception:
            tokens = []
        if len(tokens) < 2:
            continue
        event = (m.get("events") or [{}])[0].get("slug") or cid
        eligible.append((cid, float(r.get("total_daily_rate") or 0), event))
    seen = set()
    selected = []
    for cid, _rate, event in eligible:
        if event in seen:
            continue
        seen.add(event)
        selected.append(cid)
    return selected[:40]


def reward_config(cid):
    data = http_json("GET", f"https://clob.polymarket.com/rewards/markets/{cid}",
                     params={"sponsored": "true"})
    rows = data.get("data") if isinstance(data, dict) else data
    return rows[0] if rows else None


def refresh_configs(state, now, selected):
    day = now.date().isoformat()
    pending = [cid for cid in selected
               if state["markets"][cid].get("config_day") != day]
    if not pending:
        return
    gamma = gamma_configs(pending)
    for cid in pending:
        ms = state["markets"][cid]
        try:
            rw = reward_config(cid)
        except Exception as exc:  # noqa: BLE001
            print(f"rewards {cid[:10]} failed: {exc}", file=sys.stderr)
            rw = None
        gm = gamma.get(cid)
        if rw is None or gm is None:
            if ms.get("cfg"):
                ms["cfg"]["eligible"] = False
            continue
        rates = []
        for cfg in rw.get("rewards_config") or []:
            start = str(cfg.get("start_date") or "")
            end = str(cfg.get("end_date") or "2500-12-31")
            if (not start or start <= day) and day <= end:
                rates.append(float(cfg.get("rate_per_day") or 0))
        fee = gm.get("feeSchedule") or {}
        try:
            prices = [float(x) for x in json.loads(gm.get("outcomePrices") or "[]")]
        except Exception:
            prices = []
        try:
            tokens = json.loads(gm.get("clobTokenIds") or "[]")
        except Exception:
            tokens = []
        if len(tokens) < 2 and gm.get("positionIds"):
            tokens = gm.get("positionIds")
        cfg = {
            "pool_rate": sum(rates),
            "min_size": float(rw.get("rewards_min_size") or 0),
            "max_spread": float(rw.get("rewards_max_spread") or 0),
            "fee_rate": float(fee.get("rate") or 0),
            "rebate_rate": float(fee.get("rebateRate") or 0),
            "active": bool(gm.get("active")),
            "closed": bool(gm.get("closed")),
            "end_date": str(gm.get("endDate") or ""),
            "tick": float(gm.get("orderPriceMinTickSize") or 0.01),
            "slug": gm.get("slug") or cid,
            "question": gm.get("question") or "",
            "yes_token": str(tokens[0]) if len(tokens) > 0 else None,
            "no_token": str(tokens[1]) if len(tokens) > 1 else None,
            "prices": prices,
        }
        cfg["eligible"] = bool(
            cfg["pool_rate"] >= MIN_POOL
            and cfg["min_size"] == QUOTE_SIZE
            and cfg["max_spread"] >= MAX_SPREAD_MIN
            and cfg["fee_rate"] > 0
            and cfg["active"] and not cfg["closed"]
            and cfg["end_date"] >= "2026-11-20"
            and cfg["yes_token"] and cfg["no_token"]
        )
        ms["cfg"] = cfg
        ms["config_day"] = day
        ms["pools"][day] = cfg["pool_rate"]
    if all(state["markets"][cid].get("config_day") == day for cid in selected):
        state["config_day"] = day


def fetch_trades(cid, since_ts):
    rows = []
    offset = 0
    while offset < 5000:
        try:
            data = http_json("GET", "https://data-api.polymarket.com/trades",
                             params={"market": cid, "limit": 1000, "offset": offset})
        except Exception as exc:  # noqa: BLE001
            print(f"trades {cid[:10]} failed: {exc}", file=sys.stderr)
            break
        if isinstance(data, dict):
            data = data.get("data") or []
        if not data:
            break
        for t in data:
            try:
                if int(t.get("timestamp", 0)) >= since_ts - 5:
                    rows.append(t)
            except Exception:
                continue
        if len(data) < 1000:
            break
        try:
            oldest = min(int(t.get("timestamp", 0)) for t in data)
        except Exception:
            break
        if oldest < since_ts - 5:
            break
        offset += 1000
    return sorted(rows, key=lambda t: int(t.get("timestamp", 0)))


def trade_key(t):
    return ("%s:%s:%s:%s:%s" % (t.get("transactionHash"), t.get("asset"),
                                t.get("timestamp"), t.get("size"), t.get("price")))


def open_quote(ms, cid, slug, side, target, now, cfg, book, rows):
    seq = ms["quote_seq"][side] + 1
    ms["quote_seq"][side] = seq
    price = target["price"]
    quote = {
        "price": price,
        "mid": target["mid"],
        "size": QUOTE_SIZE,
        "remaining": QUOTE_SIZE,
        "placed": int(now.timestamp()),
        "queue_ahead": queue_ahead(book, price),
        "cum_sell": 0.0,
        "filled": 0.0,
        "book_ts": target["ts"],
        "seq": seq,
    }
    ms["quotes"][side] = quote
    row_uid = uid("q", cid, side, now.strftime("%Y%m%dT%H"), seq, price)
    rows.append(make_row(
        now, cid, slug, "挂", "BUY", price, f"book:{target['ts']}", QUOTE_SIZE, 0, 0,
        f"pool={cfg['pool_rate']:.2f};max_spread={cfg['max_spread']:.1f};"
        f"spread={target['spread_cents']:.2f};queue_ahead={quote['queue_ahead']:.2f};"
        f"tick={cfg.get('tick', 0.01)}",
        row_uid))


def cancel_quote(ms, cid, slug, side, now, reason, rows, book_ts):
    quote = ms["quotes"][side]
    if not quote:
        return
    row_uid = uid("c", cid, side, quote["seq"], now.strftime("%Y%m%dT%H"))
    rows.append(make_row(
        now, cid, slug, "撤", "BUY", quote["price"],
        f"book:{book_ts}", quote["remaining"], 0, 0,
        f"reason={reason};placed={quote['placed']};queue_ahead={quote['queue_ahead']:.2f}",
        row_uid))
    ms["quotes"][side] = None


def process_fills(cid, slug, ms, trades, now, cfg, rows):
    day = now.date().isoformat()
    for side in ("yes", "no"):
        quote = ms["quotes"][side]
        if not quote:
            continue
        token = cfg["yes_token"] if side == "yes" else cfg["no_token"]
        for trade in trades:
            if int(trade.get("timestamp", 0)) <= quote["placed"]:
                continue
            if str(trade.get("asset")) != token:
                continue
            if str(trade.get("side", "")).upper() != "SELL":
                continue
            price = float(trade.get("price") or 0)
            size = float(trade.get("size") or 0)
            if price > quote["price"] + 1e-9 or size <= 0:
                continue
            key = trade_key(trade)
            if key in ms["seen"]:
                continue
            ms["seen"].append(key)
            quote["cum_sell"] += size
            excess = quote["cum_sell"] - quote["queue_ahead"] - quote["filled"]
            fill = min(quote["remaining"], max(0.0, excess))
            if fill <= 1e-9:
                continue
            old = ms["inventory"][side]
            new = old + fill
            ms["avg_cost"][side] = ((ms["avg_cost"][side] * old) +
                                    (quote["price"] * fill)) / new
            ms["inventory"][side] = new
            ms["filled_today"][side] += fill
            rebate = fill * cfg["fee_rate"] * quote["price"] * (1.0 - quote["price"]) * cfg["rebate_rate"]
            ms["day_rebate"][day] = ms["day_rebate"].get(day, 0.0) + rebate
            quote["filled"] += fill
            quote["remaining"] -= fill
            row_uid = uid("f", cid, side, key)
            rows.append(make_row(
                now, cid, slug, "成交", "BUY", quote["price"],
                f"trade:{key}", fill, 0, 0,
                f"maker_fill;rebate_gross={rebate:.6f};queue_ahead={quote['queue_ahead']:.2f};"
                f"cum_sell={quote['cum_sell']:.2f};remaining={quote['remaining']:.2f}",
                row_uid))
            if quote["remaining"] <= 1e-9:
                ms["quotes"][side] = None
                break
    if len(ms["seen"]) > 100:
        ms["seen"] = ms["seen"][-100:]


def settle_day(cid, slug, ms, day, now, rows):
    if day in ms["finalized_days"]:
        return
    samples = ms["reward_samples"].get(day) or []
    if not samples and day not in ms["day_rebate"]:
        return
    shares = [s[0] for s in samples]
    share_mean = sum(shares) / len(shares) if shares else 0.0
    pool = ms["pools"].get(day, 0.0)
    reward_gross = pool * share_mean
    rebate_gross = ms["day_rebate"].get(day, 0.0)
    reward_paid = reward_gross if reward_gross >= 1.0 else 0.0
    rebate_paid = rebate_gross if rebate_gross >= 1.0 else 0.0
    last_ts = samples[-1][1] if samples else 0
    row_uid = uid("s", cid, day)
    rows.append(make_row(
        now, cid, slug, "结算", "-", 0, f"book:{last_ts}", 0, 0,
        reward_paid + rebate_paid,
        f"day={day};pool={pool:.2f};share_mean={share_mean:.6f};samples={len(samples)};"
        f"reward_gross={reward_gross:.6f};reward_paid={reward_paid:.6f};"
        f"rebate_gross={rebate_gross:.6f};rebate_paid={rebate_paid:.6f};"
        f"min_payout=1_per_market_day",
        row_uid))
    ms["finalized_days"].append(day)


def liquidate(cid, slug, ms, cfg, books, now, rows):
    if ms["liquidated"]:
        return
    closed = bool(cfg.get("closed"))
    for side in ("yes", "no"):
        inv = ms["inventory"][side]
        if inv <= 1e-9:
            continue
        token = cfg["yes_token"] if side == "yes" else cfg["no_token"]
        book = books.get(token) or {}
        book_ts = int(book.get("timestamp") or 0)
        bids, _ = parse_levels(book)
        avg = ms["avg_cost"][side]
        if closed and len(cfg.get("prices") or []) >= 2:
            idx = 0 if side == "yes" else 1
            payoff = 1.0 if cfg["prices"][idx] >= 0.99 else 0.0
            fee = 0.0
            price = payoff
            note = "resolved_at_payoff"
        else:
            price = bids[0][0] if bids else 0.0
            fee = inv * cfg["fee_rate"] * price * (1.0 - price)
            payoff = price
            note = "end_liquidation_best_bid" if bids else "no_bid_marked_zero"
        pnl = inv * (payoff - avg) - fee
        row_uid = uid("x", cid, side, now.strftime("%Y%m%dT%H"))
        rows.append(make_row(
            now, cid, slug, "平", "SELL", price, f"book:{book_ts}", inv, fee, pnl,
            f"{note};avg_cost={avg:.6f};inventory={inv:.6f}",
            row_uid))
        ms["inventory"][side] = 0.0
        ms["avg_cost"][side] = 0.0
    ms["liquidated"] = True


def run():
    now = utcnow()
    if not DRY and now < START:
        print(f"{iso(now)} before start {iso(START)}; nothing written")
        return 0
    state = load_state()
    if state.get("finalized") and now >= END:
        print(f"{iso(now)} already finalized; nothing written")
        return 0
    if not state.get("selected"):
        try:
            selected = select_markets(now)
        except Exception as exc:  # noqa: BLE001
            print(f"market selection failed: {exc}", file=sys.stderr)
            selected = []
        if not selected:
            selected = list(MARKETS)
        state["selected"] = selected
        for cid in selected:
            state["markets"].setdefault(cid, new_market_state())
    selected = list(state["selected"])
    rows = []
    day = now.date().isoformat()
    now_ms = int(now.timestamp() * 1000)

    for cid in selected:
        ms = state["markets"][cid]
        if ms.get("day") != day:
            ms["day"] = day
            ms["filled_today"] = {"yes": 0.0, "no": 0.0}

    try:
        refresh_configs(state, now, selected)
    except Exception as exc:  # noqa: BLE001
        print(f"config refresh failed: {exc}", file=sys.stderr)

    tokens = []
    for cid in selected:
        cfg = state["markets"][cid].get("cfg")
        if cfg:
            tokens.extend([cfg.get("yes_token"), cfg.get("no_token")])
    books = fetch_books([t for t in tokens if t])

    for cid in selected:
        ms = state["markets"][cid]
        cfg = ms.get("cfg")
        if not cfg:
            continue
        slug = cfg.get("slug") or cid
        eligible = cfg.get("eligible") and now < END

        had_quote = bool(ms["quotes"]["yes"] or ms["quotes"]["no"])
        if had_quote:
            trades = fetch_trades(cid, ms["last_trade_ts"])
            if trades:
                process_fills(cid, slug, ms, trades, now, cfg, rows)
                ms["last_trade_ts"] = max(ms["last_trade_ts"],
                                          max(int(t.get("timestamp", 0)) for t in trades))

        for side in ("yes", "no"):
            token = cfg["yes_token"] if side == "yes" else cfg["no_token"]
            book = books.get(token) or {}
            tick = float(book.get("tick_size") or 0.01)
            target = target_quote(book, tick, cfg["max_spread"], now_ms)
            quote = ms["quotes"][side]
            book_ts = int(book.get("timestamp") or 0)

            if quote:
                reason = None
                if now >= END:
                    reason = "end"
                elif not eligible:
                    reason = "config_ineligible"
                elif target is None:
                    reason = "no_target"
                elif abs(target["mid"] - quote["mid"]) > 0.03:
                    reason = "mid_move_gt_3c"
                elif abs(target["price"] - quote["price"]) >= tick / 2.0:
                    reason = "requote"
                elif ms["inventory"][side] >= MAX_INVENTORY:
                    reason = "inventory_cap"
                if reason == "mid_move_gt_3c":
                    ms["paused_until"] = int(now.timestamp()) + 3600
                if reason:
                    cancel_quote(ms, cid, slug, side, now, reason, rows, book_ts)
                    quote = None

            if (not quote and eligible and target is not None
                    and ms["inventory"][side] + QUOTE_SIZE <= MAX_INVENTORY + 1e-9
                    and int(now.timestamp()) >= ms.get("paused_until", 0)):
                open_quote(ms, cid, slug, side, target, now, cfg, book, rows)

            if (ms["quotes"]["yes"] or ms["quotes"]["no"]
                    or ms["inventory"]["yes"] > 0 or ms["inventory"]["no"] > 0):
                share = q_share(ms["quotes"], books.get(cfg["yes_token"]) or {},
                                books.get(cfg["no_token"]) or {}, cfg["max_spread"])
                ms["reward_samples"].setdefault(day, []).append([share, book_ts])

        for d in sorted(ms["reward_samples"]):
            if d < day:
                settle_day(cid, slug, ms, d, now, rows)

        if now >= END:
            for side in ("yes", "no"):
                if ms["quotes"][side]:
                    token = cfg["yes_token"] if side == "yes" else cfg["no_token"]
                    book_ts = int((books.get(token) or {}).get("timestamp") or 0)
                    cancel_quote(ms, cid, slug, side, now, "end", rows, book_ts)
            liquidate(cid, slug, ms, cfg, books, now, rows)
            for d in sorted(ms["reward_samples"]):
                if d < day:
                    settle_day(cid, slug, ms, d, now, rows)
            state["finalized"] = True

    append_rows(rows)
    save_state(state)
    print(f"{iso(now)} rows={len(rows)} markets={len(selected)} finalized={state.get('finalized')}")
    return 0


def main():
    try:
        return run()
    except Exception as exc:  # noqa: BLE001 - exit 0 on network/data errors
        print(f"record.py error (exit 0): {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
