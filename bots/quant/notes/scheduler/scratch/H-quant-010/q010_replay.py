#!/usr/bin/env python3
"""quant-010 historical executable-price test (Netflix weekly #1 show).

PRE-DECLARED DESIGN -- frozen before any result was computed. Do not tune.

Data (all free, keyless, no login):
  * Gamma API  : series 10440 ("Top Netflix Show Week", global #1 show) and
                 series 10772 ("#1 US Netflix Show"), closed events;
                 movie extension: 10441 (global #1 movie) and 10775 (US #1
                 movie).  GET /events?series_id=<id>&closed=true&limit=200
  * Netflix Tudum (access date 2026-10-20):
      global: https://www.netflix.com/tudum/top10/data/all-weeks-global.tsv
      US    : https://www.netflix.com/tudum/top10/data/all-weeks-countries.tsv
    (the .xlsx variant is also live; the TSV is used because openpyxl is not
    required.)
  * data-api trades (fills):
      GET https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N
      fields side/price/size/timestamp/outcome.  "No" price p -> YES = 1-p.

UNIVERSE (pre-declared):
  * PRIMARY (verdict): all closed Gamma events in the two #1-show series above,
    one chart-week per event.  This is the entry's instrument (Netflix #1 show).
  * EXTENSION (universe completeness): the same pipeline is run with --kind
    movie on Gamma series 10441 (global #1 movie) and 10775 (US #1 movie),
    using the Tudum "Films (English)" / "Films" tables.  Movies are reported
    separately; the verdict is taken on the primary show arm, and the movie
    arm is checked against the same failure criterion.
  * #2 events and "how many views" events are excluded: they are not the
    entry's #1-chart instrument.  Their series IDs are 10719/10720/10773/10774
    and 12534/12535, respectively.
  * Duplicate events for the same (scope, chart week) are collapsed to the one
    with the largest Gamma volume (ties: most markets).
  * One chart-week = one independent cluster.  Global and US on the same week
    are ONE cluster (entry's own independence rule); their net P&L per share
    is averaged inside the cluster.
  * Expected coverage: ~54 publish weeks (2025-03 to 2026-10), of which
    >=30 have both a market and an executable trade.

SIGNAL (pre-declared proxy, labelled as such):
  * The entry's real signal is a daily-chart nowcast.  Netflix has no keyless
    public daily chart archive (FlixPatrol returned HTTP 403 on 2026-10-20), so
    this is the simplest frozen proxy the entry admits: the previous published
    week's #1 show in the SAME chart (global -> global, US -> US) is the
    predicted #1 for the current week.  Only that entity, if it is listed as a
    candidate in the current event, produces a trade.
  * Model probability for Brier/log-loss (all candidates, no lookahead):
    prior-week rank r in the same chart -> weight (11-r) for r=1..10, 0.1 for
    a candidate absent from the prior week's top 10.  Normalised over the
    non-Other candidates that have a market price at decision time.
  * This proxy is deliberately weak; a FAIL is a failure of the proxy, not
    proof that a daily-chart nowcast would fail.  It is the only keyless
    historical executable-price test available.

DECISION TIME AND PRICE (pre-declared):
  * Publication time T_pub is parsed from the Gamma event description:
    "<weekday>, <Month D, YYYY>, 3:00 PM ET".  If absent, fall back to the
    endDate calendar day at 15:00 America/New_York (1 event).
  * Chart week label = the Sunday strictly before T_pub (Netflix publishes the
    previous Mon-Sun week on Tuesday).
  * Decision price = the LAST data-api trade with timestamp <= T_pub AND
    timestamp >= T_pub - 24h, on the predicted candidate's market.
  * ask = trade YES price + 0.01 (half spread); bid is not used (buy only).
  * Fee = shares * rate * ask * (1-ask), per GUIDE section 8.  rate is the
    market feeSchedule.rate when present; otherwise 0 when feesEnabled=false
    (historical markets), otherwise GUIDE culture rate 0.05.  The entry quotes
    0.05 for current culture markets.
  * Hold to resolution: Gamma outcomePrices (YES >= 0.99 = winner).
  * No trade if there is no fill in the 24h window.

ARMS (pre-declared):
  * PRIMARY (verdict arm): buy 1 share of the proxy's predicted #1 at ask.
    This is the entry's own "signal replay" design plus executable cost.
  * PRICE-FILTER arm (secondary): only buy when
    p_model - ask - fee_per_share - 0.01 > 0, i.e. the entry's stated entry
    condition (p_model = proxy probability from the rank weights).
  * ORACLE diagnostic (upper bound, lookahead, not a strategy): buy the
    eventual Gamma winner at its decision-window ask.  This directly tests the
    entry's claim that a taker loses even at 100% win.

FAILURE CRITERION (quoted from the entry, "两周内怎么检验" clause 3):
  "信号：30 个历史周中，发布前 24h 的 #1 预测命中率 < 80%，判失败。"
  "成本：前向每笔按'吃单费 + 半个价差'计，若已成交样本的中位净收益 <= 0，
   判失败。"
  "若无法取得至少 30 个独立周事件，或无法取得可执行 bid/ask，结论写'未验证'。"
  Operational reading used here: fewer than 30 independent chart-week clusters
  with an executable fill -> INSUFFICIENT; otherwise FAIL if hit rate < 80% or
  cluster median net P&L per share <= 0; PASS only if both are met.

SENSITIVITY (one, pre-declared): decision window 12h instead of 24h
  (T_pub-12h .. T_pub, same last-trade rule).  No other parameter is tuned.

STATISTICS: 10000 cluster-block bootstrap of the mean net/share, fixed seed 42.
  Per-$-staked = net / ask.  Brier and log loss are multi-class over priced
  non-Other candidates; model and market are normalised on the same subset.
  Settlement check: Netflix-computed #1 vs Gamma-resolved winner.

CACHE: every download is cached under _cache/ (gitignored), or under
  $Q010_CACHE when set.  A rerun with the cache present performs no network I/O
  and prints identical numbers.  Cached
  payloads are type/size validated before reuse; a malformed or truncated
  download is refetched instead of being treated as complete.

VERDICT SCOPE (v2): the frozen signal criterion applies to the entry's original
  daily-chart nowcast, which was NOT evaluated here (no keyless daily archive).
  The overall verdict is therefore UNVERIFIED.  The previous-week-#1 persistence
  proxy gets its own verdict, explicitly labelled "PROXY ONLY".

Usage: python3 q010_hist.py [--refresh]
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import re
import statistics
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

HERE = Path(__file__).resolve().parent
CACHE = Path(os.environ.get("Q010_CACHE", str(HERE / "_cache")))
GAMMA = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
TUDUM_GLOBAL = "https://www.netflix.com/tudum/top10/data/all-weeks-global.tsv"
TUDUM_US = "https://www.netflix.com/tudum/top10/data/all-weeks-countries.tsv"
SERIES = {
    "show": {10440: "global", 10772: "us"},
    "movie": {10441: "global", 10775: "us"},
}
CATEGORY = {
    ("global", "show"): "TV (English)",
    ("global", "movie"): "Films (English)",
    ("us", "show"): "TV",
    ("us", "movie"): "Films",
}
UA = "quant-research-q010/1.0 (keyless public data)"
HALF_SPREAD = 0.01
PRIMARY_WINDOW_H = 24
SENS_WINDOW_H = 12
FEE_CULTURE = 0.05
BOOT = 10000
SEED = 42
MAX_WORKERS = 8

REFRESH = False
_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": UA})

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}
PUB_RE = re.compile(
    r"on (?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), "
    r"([A-Z][a-z]+) (\d{1,2}), (\d{4}), (\d{1,2}):(\d{2}) (AM|PM) ET")
ET = ZoneInfo("America/New_York")


def _cache_path(key):
    return CACHE / (hashlib.sha1(key.encode("utf-8")).hexdigest() + ".json")


def _read_json_cache(path, expect):
    """Return cached JSON only if it is structurally complete, else None."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    if expect is not None and not isinstance(data, expect):
        return None
    return data


def get_json(url, params=None, retries=6, expect=list):
    """Cached JSON GET; malformed/partial cache entries are refetched."""
    key = url
    if params:
        key += "?" + urllib.parse.urlencode(sorted(params.items()))
    path = _cache_path(key)
    if not REFRESH:
        cached = _read_json_cache(path, expect)
        if cached is not None:
            return cached
    last = None
    for attempt in range(retries):
        try:
            r = _SESSION.get(url, params=params, timeout=90)
            if r.status_code == 429 or r.status_code >= 500:
                raise RuntimeError("HTTP %s" % r.status_code)
            r.raise_for_status()
            data = r.json()
            if expect is not None and not isinstance(data, expect):
                raise RuntimeError("unexpected JSON type: %s" % type(data).__name__)
            CACHE.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
            tmp.replace(path)
            return data
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(0.4 * (2 ** attempt))
    raise RuntimeError("GET failed: %s (%s)" % (url, last))


def _valid_tsv(path, name):
    """A Tudum TSV is complete only if header and a plausible row count parse."""
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            rd = csv.DictReader(fh, delimiter="\t")
            fields = set(rd.fieldnames or [])
            need = {"week", "category", "weekly_rank"}
            if name.endswith("countries.tsv"):
                need |= {"country_name", "season_title", "show_title"}
            else:
                need |= {"season_title", "show_title"}
            if not need <= fields:
                return False
            n = sum(1 for _ in rd)
        return n >= (50000 if name.endswith("countries.tsv") else 5000)
    except Exception:  # noqa: BLE001
        return False


def download(url, name, retries=6):
    path = CACHE / name
    if path.exists() and not REFRESH and _valid_tsv(path, name):
        return path
    last = None
    for attempt in range(retries):
        try:
            r = _SESSION.get(url, timeout=300)
            r.raise_for_status()
            if len(r.content) < 500_000:
                raise RuntimeError("suspiciously small body: %d" % len(r.content))
            CACHE.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(r.content)
            if not _valid_tsv(tmp, name):
                raise RuntimeError("incomplete TSV body: %d bytes" % len(r.content))
            tmp.replace(path)
            return path
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(0.5 * (2 ** attempt))
    raise RuntimeError("download failed: %s (%s)" % (url, last))


def parse_pub(event):
    m = PUB_RE.search(event.get("description") or "")
    if m:
        month = MONTHS[m.group(1).lower()]
        day, year = int(m.group(2)), int(m.group(3))
        hour, minute = int(m.group(4)), int(m.group(5))
        if m.group(6) == "PM" and hour != 12:
            hour += 12
        if m.group(6) == "AM" and hour == 12:
            hour = 0
        return dt.datetime(year, month, day, hour, minute, tzinfo=ET), "description"
    end = event.get("endDate") or ""
    if end:
        d = dt.date.fromisoformat(end[:10])
        return dt.datetime(d.year, d.month, d.day, 15, 0, tzinfo=ET), "endDate"
    return None, None


def week_end_for(pub_local):
    """Sunday strictly before the Tuesday publication."""
    back = (pub_local.weekday() - 6) % 7
    if back == 0:
        back = 7
    return pub_local.date() - dt.timedelta(days=back)


def norm_full(s):
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def norm_base(s):
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"\b(season|collection|part|volume|series)\s*\d+\b", " ", s)
    s = re.sub(r"\b(limited series|the series)\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def titles_match(a, b):
    fa, fb = norm_full(a), norm_full(b)
    if fa and fa == fb:
        return True
    ba, bb = norm_base(a), norm_base(b)
    if not ba or not bb:
        return False
    if ba == bb:
        return True
    if len(ba) >= 6 and len(bb) >= 6:
        if ba.startswith(bb + " ") or bb.startswith(ba + " "):
            return True
        # Netflix sometimes drops a franchise prefix ("The Reunion" vs
        # "Love is Blind: The Reunion"); accept a word-boundary suffix.
        if ba.endswith(" " + bb) or bb.endswith(" " + ba):
            return True
    return False


def load_chart(path, scope, kind):
    """week string -> list of (rank, entity title)."""
    out = {}
    with open(path, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh, delimiter="\t")
        for row in rd:
            if scope == "global":
                if row.get("category") != CATEGORY[(scope, kind)]:
                    continue
            else:
                if row.get("country_name") != "United States":
                    continue
                if row.get("category") != CATEGORY[(scope, kind)]:
                    continue
            title = row.get("season_title") or ""
            if title.strip() in ("", "N/A"):
                title = row.get("show_title") or ""
            if not title:
                continue
            out.setdefault(row["week"], []).append((int(row["weekly_rank"]), title))
    for week in out:
        out[week].sort()
    return out


def parse_prices(market):
    try:
        raw = market.get("outcomePrices")
        if isinstance(raw, str):
            vals = json.loads(raw)
        else:
            vals = raw or []
        return [float(x) for x in vals]
    except Exception:  # noqa: BLE001
        return []


def market_title(market):
    t = (market.get("groupItemTitle") or "").strip()
    if t:
        return t
    q = market.get("question") or ""
    m = re.search(r'Will "(.+?)" be', q)
    return m.group(1) if m else (q.strip() or market.get("slug", ""))


def fee_rate_for(market):
    fs = market.get("feeSchedule")
    if isinstance(fs, str):
        try:
            fs = json.loads(fs)
        except Exception:  # noqa: BLE001
            fs = None
    if isinstance(fs, dict) and fs.get("rate") is not None:
        return float(fs["rate"]), "feeSchedule"
    if market.get("feesEnabled") is False:
        return 0.0, "feesEnabled=false"
    return FEE_CULTURE, "GUIDE culture 0.05"


def last_trade_before(condition_id, t_pub):
    """Newest data-api trade with ts <= t_pub.  Pages past post-resolution trades.

    A page shorter than the requested limit is the last page, so stop there
    instead of fetching (and caching) a spurious empty page.  Cached pages are
    type-checked by get_json; malformed pages are refetched, not reused.
    """
    limit = 500
    offset = 0
    while offset <= 10000:
        tr = get_json(DATA_API + "/trades",
                      {"market": condition_id, "limit": limit, "offset": offset})
        if not tr:
            return None
        cand = [x for x in tr if float(x.get("timestamp", 0)) <= t_pub]
        if cand:
            return max(cand, key=lambda x: float(x["timestamp"]))
        # every trade on this page is after T_pub; page is newest-first
        if len(tr) < limit:
            return None
        offset += limit
    return None


def yes_price(trade):
    p = float(trade["price"])
    oc = trade.get("outcome")
    if oc == "No":
        return 1.0 - p
    if oc == "Yes":
        return p
    return 1.0 - p if int(trade.get("outcomeIndex", 0)) == 1 else p


def load_events(kind):
    events = []
    counts = {}
    for sid, scope in SERIES[kind].items():
        data = get_json(GAMMA + "/events",
                        {"series_id": sid, "closed": "true", "limit": 200})
        counts[scope] = len(data)
        for e in data:
            e = dict(e)
            e["_scope"] = scope
            e["_kind"] = kind
            events.append(e)
    return events, counts


def dedupe_events(events):
    """One event per (scope, kind, chart week), largest volume."""
    groups = {}
    skipped = []
    for e in events:
        if not e.get("closed"):
            skipped.append("not_closed")
            continue
        pub, src = parse_pub(e)
        if pub is None:
            skipped.append("no_pub_date")
            continue
        we = week_end_for(pub)
        key = (e["_scope"], e["_kind"], we.isoformat())
        vol = float(e.get("volume") or 0)
        nm = len(e.get("markets") or [])
        cand = (vol, nm, e["slug"], pub, src, e)
        if key not in groups or cand[:2] > groups[key][:2]:
            groups[key] = cand
    out = []
    for key in sorted(groups):
        vol, nm, slug, pub, src, e = groups[key]
        out.append({"scope": key[0], "kind": key[1], "week": key[2],
                    "pub": pub, "pub_src": src, "event": e})
    return out, skipped


def main():
    global REFRESH
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--kind", choices=("show", "movie"), default="show")
    args = ap.parse_args()
    REFRESH = args.refresh
    kind = args.kind

    # ---------------- data ----------------
    gpath = download(TUDUM_GLOBAL, "all-weeks-global.tsv")
    upath = download(TUDUM_US, "all-weeks-countries.tsv")
    chart = {}
    for scope in ("global", "us"):
        chart[(scope, kind)] = load_chart(
            gpath if scope == "global" else upath, scope, kind)

    raw_events, series_counts = load_events(kind)
    units, skipped = dedupe_events(raw_events)

    # ---------------- per-event signal & price ----------------
    work = []
    for u in units:
        scope, week = u["scope"], dt.date.fromisoformat(u["week"])
        t_pub = u["pub"].astimezone(dt.timezone.utc)
        t_pub_ts = t_pub.timestamp()
        prior_week = (week - dt.timedelta(days=7)).isoformat()
        cur = chart[(scope, kind)].get(week.isoformat())
        prior = chart[(scope, kind)].get(prior_week)
        if not cur:
            u["skip"] = "no_tudum_week"
            work.append(u)
            continue
        if not prior:
            u["skip"] = "no_prior_week"
            work.append(u)
            continue
        u["signal_eligible"] = True
        prior_no1 = prior[0][1]
        u["computed_no1"] = cur[0][1]
        markets = u["event"].get("markets") or []
        info = []
        other_yes = False
        for m in markets:
            title = market_title(m)
            if "other" in title.lower():
                pr = parse_prices(m)
                other_yes = bool(pr and pr[0] >= 0.99)
                continue
            prices = parse_prices(m)
            resolved_yes = bool(prices and prices[0] >= 0.99)
            resolved = bool(prices and (prices[0] >= 0.99 or prices[1] >= 0.99))
            prior_rank = None
            for rank, ptitle in prior:
                if titles_match(title, ptitle):
                    prior_rank = rank
                    break
            info.append({"market": m, "title": title, "prices": prices,
                         "resolved": resolved, "resolved_yes": resolved_yes,
                         "prior_rank": prior_rank})
        u["candidates"] = info
        u["other_yes"] = other_yes
        pred = None
        for it in info:
            if titles_match(it["title"], prior_no1):
                pred = it
                break
        u["pred"] = pred
        u["signal_hit"] = (1 if pred is not None and
                           titles_match(pred["title"], u["computed_no1"]) else 0)
        if pred is None:
            u["skip"] = "prior_no1_not_listed"
            work.append(u)
            continue
        u["skip"] = None
        work.append(u)

    # Fetch the decision trade for every candidate market in parallel.
    tasks = []
    for u in work:
        if u.get("skip"):
            continue
        for it in u["candidates"]:
            cid = it["market"].get("conditionId")
            if not cid:
                continue
            tasks.append((u["pub"].astimezone(dt.timezone.utc).timestamp(), cid))
    uniq = sorted(set(tasks))
    price_map = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(last_trade_before, cid, ts): (cid, ts) for ts, cid in uniq}
        for fut in as_completed(futs):
            cid, ts = futs[fut]
            try:
                price_map[(cid, ts)] = fut.result()
            except Exception:  # noqa: BLE001
                price_map[(cid, ts)] = None

    funnel = {"units": len(units)}
    for u in work:
        if u.get("skip"):
            funnel[u["skip"]] = funnel.get(u["skip"], 0) + 1
            continue
        ts = u["pub"].astimezone(dt.timezone.utc).timestamp()
        lower = ts - PRIMARY_WINDOW_H * 3600
        for it in u["candidates"]:
            raw = price_map.get((it["market"].get("conditionId"), ts))
            it["trade"] = None
            it["trade_too_old"] = False
            if raw:
                if float(raw.get("timestamp", 0)) >= lower:
                    it["trade"] = raw
                else:
                    it["trade_too_old"] = True
        pred = u["pred"]
        if not pred.get("trade"):
            if pred.get("trade_too_old"):
                u["skip"] = "fill_too_old"
                funnel["fill_too_old"] = funnel.get("fill_too_old", 0) + 1
            else:
                u["skip"] = "no_fill_in_24h"
                funnel["no_fill_in_24h"] = funnel.get("no_fill_in_24h", 0) + 1
        else:
            u["skip"] = None

    # ---------------- simulate ----------------
    rows = []
    briers = []
    for u in work:
        if u.get("skip"):
            continue
        pred = u["pred"]
        tr = pred["trade"]
        ts = float(tr["timestamp"])
        t_pub = u["pub"].astimezone(dt.timezone.utc).timestamp()
        if ts < t_pub - PRIMARY_WINDOW_H * 3600:
            u["skip"] = "fill_too_old"
            funnel["fill_too_old"] = funnel.get("fill_too_old", 0) + 1
            continue
        p_yes = yes_price(tr)
        ask = min(1.0, p_yes + HALF_SPREAD)
        rate, fee_src = fee_rate_for(pred["market"])
        fee = rate * ask * (1.0 - ask)
        won = 1 if pred["resolved_yes"] else 0
        net = won - ask - fee
        p_model_raw = {}
        for it in u["candidates"]:
            tr2 = it.get("trade")
            if not tr2:
                continue
            p_model_raw[it["title"]] = (11 - it["prior_rank"]) if it["prior_rank"] else 0.1
        # predicted candidate's model probability, normalised on priced candidates
        p_pred = None
        if p_model_raw:
            p_pred = p_model_raw.get(pred["title"], 0.1) / sum(p_model_raw.values())
        # sensitivity: same trade, 12h window
        sens_ok = ts >= t_pub - SENS_WINDOW_H * 3600
        # oracle: eventual winner at decision-window ask
        oracle = next((it for it in u["candidates"] if it["resolved_yes"]), None)
        orow = None
        if oracle is not None and oracle.get("trade"):
            otr = oracle["trade"]
            ots = float(otr["timestamp"])
            if ots >= t_pub - PRIMARY_WINDOW_H * 3600:
                oask = min(1.0, yes_price(otr) + HALF_SPREAD)
                orate, _ = fee_rate_for(oracle["market"])
                ofee = orate * oask * (1.0 - oask)
                orow = {"title": oracle["title"], "ask": oask,
                        "net": 1.0 - oask - ofee}
        # settlement check
        resolved_title = next(
            (it["title"] for it in u["candidates"] if it["resolved_yes"]), None)
        if resolved_title is None:
            if u.get("other_yes"):
                listed = any(titles_match(it["title"], u["computed_no1"])
                             for it in u["candidates"])
                settle = "MISMATCH_OTHER" if listed else "OTHER_NOT_LISTED"
            else:
                settle = "NO_RESOLUTION"
        elif titles_match(resolved_title, u["computed_no1"]):
            settle = "MATCH"
        else:
            settle = "MISMATCH"

        # Brier / log loss on priced non-Other candidates
        priced = [it for it in u["candidates"] if it.get("trade")]
        if len(priced) >= 2 and any(it["resolved_yes"] for it in priced):
            model_sum = sum(
                (11 - it["prior_rank"]) if it["prior_rank"] else 0.1
                for it in priced)
            qs = [max(0.001, min(0.999, yes_price(it["trade"]))) for it in priced]
            qsum = sum(qs)
            y_idx = next(i for i, it in enumerate(priced) if it["resolved_yes"])
            pb = [((11 - it["prior_rank"]) if it["prior_rank"] else 0.1) / model_sum
                  for it in priced]
            qb = [q / qsum for q in qs]
            briers.append({
                "week": u["week"], "scope": u["scope"],
                "brier_model": sum((p - (1.0 if i == y_idx else 0.0)) ** 2
                                   for i, p in enumerate(pb)),
                "brier_market": sum((q - (1.0 if i == y_idx else 0.0)) ** 2
                                    for i, q in enumerate(qb)),
                "ll_model": -math.log(max(pb[y_idx], 1e-12)),
                "ll_market": -math.log(max(qb[y_idx], 1e-12)),
                "n": len(priced),
            })

        rows.append({
            "week": u["week"], "scope": u["scope"],
            "pub_utc": u["pub"].astimezone(dt.timezone.utc).isoformat(),
            "event_slug": u["event"]["slug"],
            "tudum_no1": u["computed_no1"],
            "resolved": resolved_title or "",
            "settle": settle,
            "pred_title": pred["title"],
            "pred_prior_rank": pred["prior_rank"] if pred["prior_rank"] else "",
            "pred_prices": json.dumps(pred["prices"]),
            "trade_ts": int(ts),
            "trade_outcome": tr.get("outcome"),
            "trade_price": float(tr["price"]),
            "yes_trade": p_yes, "ask": ask, "fee_rate": rate,
            "fee_source": fee_src, "fee": fee,
            "won": won, "net": net, "staked": ask,
            "net_per_dollar": net / ask if ask else float("nan"),
            "p_model": p_pred if p_pred is not None else "",
            "filter_pass": int(p_pred is not None and
                               (p_pred - ask - fee - 0.01) > 0),
            "sens_12h": int(sens_ok),
            "oracle_title": orow["title"] if orow else "",
            "oracle_ask": orow["ask"] if orow else "",
            "oracle_net": orow["net"] if orow else "",
            "n_candidates": len(u["candidates"]),
        })

    # ---------------- statistics ----------------
    def med(xs):
        return statistics.median(xs) if xs else float("nan")

    def mean(xs):
        return statistics.mean(xs) if xs else float("nan")

    def cluster_values(rs, key):
        by = {}
        for r in rs:
            by.setdefault(r["week"], []).append(r[key])
        return [mean(v) for _, v in sorted(by.items())]

    nets = [r["net"] for r in rows]
    cl_nets = cluster_values(rows, "net")
    dollars = [r["net_per_dollar"] for r in rows]
    cl_dollars = cluster_values(rows, "net_per_dollar")
    hits = [r["won"] for r in rows]
    cl_hits = cluster_values(rows, "won")
    # The proxy makes a prediction even when the previous #1 is not listed in
    # the current event: that is a signal miss, not a missing observation.
    sig_units = [u for u in work
                 if u.get("signal_eligible") and u.get("computed_no1")]
    sig_hits = [u["signal_hit"] for u in sig_units]
    sig_cl = cluster_values(
        [{"week": u["week"], "v": u["signal_hit"]} for u in sig_units], "v")

    def bootstrap_mean(vals, seed=SEED, n=BOOT):
        if not vals:
            return (float("nan"), float("nan"))
        import random
        rng = random.Random(seed)
        m = len(vals)
        means = []
        for _ in range(n):
            s = 0.0
            for _ in range(m):
                s += vals[rng.randrange(m)]
            means.append(s / m)
        means.sort()
        return means[int(0.025 * n)], means[int(0.975 * n) - 1]

    # sensitivity arm
    sens_rows = [r for r in rows if r["sens_12h"]]
    sens_nets = [r["net"] for r in sens_rows]
    sens_cl = cluster_values(sens_rows, "net")

    # price-filter arm
    filt = [r for r in rows if r["filter_pass"]]
    filt_nets = [r["net"] for r in filt]
    filt_cl = cluster_values(filt, "net")

    oracle = [r for r in rows if r["oracle_net"] != ""]
    oracle_nets = [float(r["oracle_net"]) for r in oracle]
    oracle_cl = cluster_values(
        [{"week": r["week"], "v": float(r["oracle_net"])} for r in oracle], "v")
    oracle_dollars = [float(r["oracle_net"]) / float(r["oracle_ask"]) for r in oracle]

    ci_lo, ci_hi = bootstrap_mean(cl_nets)

    # all-in 0.05 fee sensitivity (regardless of historical feeSchedule)
    fee005 = []
    for r in rows:
        f = FEE_CULTURE * r["ask"] * (1 - r["ask"])
        fee005.append(r["won"] - r["ask"] - f)
    fee005_cl = cluster_values(
        [{"week": r["week"], "v": v} for r, v in zip(rows, fee005)], "v")

    # ---------------- print ----------------
    print("=" * 78)
    print("quant-010 historical executable-price test (Netflix weekly #1 %s)" % kind)
    print("access date: 2026-10-21 | all sources free, keyless, no login")
    print("=" * 78)
    print("Tudum files:")
    print("  global:", TUDUM_GLOBAL)
    print("  US    :", TUDUM_US)
    print("  global weeks: %d (%s .. %s), %s rows loaded" % (
        len(chart[("global", kind)]), min(chart[("global", kind)]),
        max(chart[("global", kind)]), CATEGORY[("global", kind)]))
    print("  US weeks    : %d (%s .. %s), %s rows loaded" % (
        len(chart[("us", kind)]), min(chart[("us", kind)]),
        max(chart[("us", kind)]), CATEGORY[("us", kind)]))
    print("Gamma closed events by series: global=%d, us=%d" % (
        series_counts["global"], series_counts["us"]))
    print("deduped (scope, chart-week) events: %d" % len(units))
    _weeks = sorted({u["week"] for u in units})
    print("chart-week span: %s .. %s (%d unique weeks)" % (
        _weeks[0], _weeks[-1], len(_weeks)))
    print("")
    print("FUNNEL")
    print("  checks with a computed chart week: %d" % (
        len(units) - funnel.get("no_tudum_week", 0) - funnel.get("no_prior_week", 0)))
    for k in ("no_pub_date", "not_closed", "no_tudum_week", "no_prior_week",
              "prior_no1_not_listed", "no_fill_in_24h", "fill_too_old"):
        if funnel.get(k):
            print("  skipped %-22s %d" % (k + ":", funnel[k]))
    print("  simulated market-events: %d" % len(rows))
    print("  independent chart-week clusters: %d" % len(cl_nets))
    print("")
    print("SIGNAL PROXY HIT RATE (PROXY ONLY; original daily-chart signal NOT evaluated)")
    print("  n chart-scope weeks with a prediction: %d | clusters: %d" % (
        len(sig_units), len(sig_cl)))
    print("  hit rate (events): %.4f (%d/%d) | cluster mean: %.4f" % (
        mean(sig_hits), sum(sig_hits), len(sig_hits), mean(sig_cl)))
    print("")
    print("PRIMARY ARM (buy proxy's predicted #1 at ask, hold to resolution)")
    print("  n market-events: %d | n clusters: %d" % (len(rows), len(cl_nets)))
    print("  hit rate (market-events): %.4f (%d/%d)" % (
        mean(hits), sum(hits), len(hits)))
    print("  hit rate (cluster mean): %.4f" % mean(cl_hits))
    print("  net/share: median %+.4f | mean %+.4f | cluster median %+.4f | cluster mean %+.4f" % (
        med(nets), mean(nets), med(cl_nets), mean(cl_nets)))
    print("  net per $ staked: median %+.4f | mean %+.4f" % (
        med(dollars), mean(dollars)))
    print("  cluster bootstrap 95%% CI of mean net/share: [%+.4f, %+.4f]" % (ci_lo, ci_hi))
    print("  total net: %+.4f USDC on %+.4f staked" % (
        sum(nets), sum(r["staked"] for r in rows)))
    print("")
    print("PRICE-FILTER ARM (entry's p_model - ask - fee - 0.01 > 0)")
    print("  triggers: %d market-events | %d clusters" % (len(filt), len(filt_cl)))
    if filt:
        print("  net/share: median %+.4f | mean %+.4f | cluster median %+.4f" % (
            med(filt_nets), mean(filt_nets), med(filt_cl)))
        print("  hit rate: %.4f" % mean([r["won"] for r in filt]))
    else:
        print("  net/share: n/a (no trigger)")
    print("")
    print("ORACLE DIAGNOSTIC (buy eventual Gamma winner at its ask; 100% win)")
    print("  n market-events: %d | n clusters: %d" % (len(oracle), len(oracle_cl)))
    print("  net/share: median %+.4f | mean %+.4f | cluster median %+.4f" % (
        med(oracle_nets), mean(oracle_nets), med(oracle_cl)))
    print("  net per $ staked: median %+.4f | mean %+.4f" % (
        med(oracle_dollars), mean(oracle_dollars)))
    print("  share of winners with net<=0: %.4f" % (
        mean([1 if x <= 0 else 0 for x in oracle_nets])))
    print("")
    print("SENSITIVITY 1: decision window 12h instead of 24h")
    print("  n market-events: %d | n clusters: %d" % (len(sens_rows), len(sens_cl)))
    print("  net/share: median %+.4f | mean %+.4f | cluster median %+.4f" % (
        med(sens_nets), mean(sens_nets), med(sens_cl)))
    print("  hit rate: %.4f" % mean([r["won"] for r in sens_rows]))
    print("")
    print("SENSITIVITY 2: all-in 0.05 culture fee (ignores historical feesEnabled=false)")
    print("  net/share: median %+.4f | mean %+.4f | cluster median %+.4f" % (
        med(fee005), mean(fee005), med(fee005_cl)))
    print("")
    print("MODEL vs MARKET (priced non-Other candidates, multi-class)")
    if briers:
        print("  n events: %d | mean priced candidates/event: %.2f" % (
            len(briers), mean([b["n"] for b in briers])))
        print("  Brier model %.4f | market %.4f | diff(market-model) %+.4f" % (
            mean([b["brier_model"] for b in briers]),
            mean([b["brier_market"] for b in briers]),
            mean([b["brier_market"] - b["brier_model"] for b in briers])))
        print("  logloss model %.4f | market %.4f | diff(market-model) %+.4f" % (
            mean([b["ll_model"] for b in briers]),
            mean([b["ll_market"] for b in briers]),
            mean([b["ll_market"] - b["ll_model"] for b in briers])))
        print("  model better on Brier: %d/%d" % (
            sum(1 for b in briers if b["brier_model"] < b["brier_market"]), len(briers)))
    else:
        print("  n events: 0 (insufficient priced candidates)")
    print("")
    print("SETTLEMENT CHECK (Tudum computed #1 vs Gamma resolved market)")
    sc = {}
    for r in rows:
        sc[r["settle"]] = sc.get(r["settle"], 0) + 1
    print("  " + " | ".join("%s=%d" % (k, sc[k]) for k in sorted(sc)))
    mism = [r for r in rows if r["settle"] == "MISMATCH"]
    for r in sorted(mism, key=lambda x: (x["week"], x["scope"]))[:12]:
        print("  MISMATCH %s %-6s tudum=%r gamma=%r" % (
            r["week"], r["scope"], r["tudum_no1"], r["resolved"]))
    print("")
    print("VERDICT RULE (frozen, entry's own): <30 clusters with fill -> INSUFFICIENT;")
    print("else FAIL if signal hit rate < 80%% or cluster median net/share <= 0; else PASS.")
    print("SCOPE: the rule's signal clause is about the entry's daily-chart nowcast.")
    print("       That signal was NOT evaluated here, so its verdict stays UNVERIFIED.")
    print("       The proxy below is scored only to describe the substitute.")
    print("")
    print("VERDICT (OVERALL / ORIGINAL entry signal): UNVERIFIED")
    print("  reason: no keyless historical Netflix daily chart; original signal not tested.")
    if len(cl_nets) < 30:
        proxy_verdict = "INSUFFICIENT"
    elif mean(sig_cl) < 0.80 or med(cl_nets) <= 0:
        proxy_verdict = "FAIL"
    else:
        proxy_verdict = "PASS"
    print("VERDICT (PROXY ONLY, previous-week-#1 persistence): %s" % proxy_verdict)
    print("  clusters=%d | proxy signal cluster hit=%.4f | trade cluster hit=%.4f | cluster median net/share=%+.4f" % (
        len(cl_nets), mean(sig_cl), mean(cl_hits), med(cl_nets)))

    # ---------------- write events_<kind>.csv ----------------
    out_csv = "events.csv" if kind == "show" else "events_movies.csv"
    cols = ["week", "scope", "pub_utc", "event_slug", "tudum_no1", "resolved",
            "settle", "pred_title", "pred_prior_rank", "pred_prices",
            "trade_ts", "trade_outcome", "trade_price", "yes_trade", "ask",
            "fee_rate", "fee_source", "fee", "won", "net", "staked",
            "net_per_dollar", "p_model", "filter_pass", "sens_12h",
            "oracle_title", "oracle_ask", "oracle_net", "n_candidates"]
    with open(HERE / out_csv, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x["week"], x["scope"])):
            w.writerow(r)
    print("")
    print("wrote %s (%d rows)" % (out_csv, len(rows)))


if __name__ == "__main__":
    main()
