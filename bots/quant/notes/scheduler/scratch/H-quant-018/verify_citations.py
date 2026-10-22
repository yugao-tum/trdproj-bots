#!/usr/bin/env python3
"""Whole-entry citation and round-2 consistency check for quant-018 (2026-10-21).

Not a replacement for verify_sources.py (which checks the 出处 bullets against
their original claims).  This script additionally:
  * extracts every external URL in the whole entry (body included),
  * checks the OOS event / data-api / PortWatch / CLOB claims used by 4.5-4.6,
  * checks every cited local path exists and the two frozen replay inputs keep
    the sha1 written in the entry and SUMMARY.md,
  * re-parses the 8 round-2 front-matter fields and cross-checks the headline
    values against bots/quant/replay/quant-018/SUMMARY.md.
Only metadata is printed; raw bodies are not stored.
"""
import hashlib
import json
import re
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
ENTRY = REPO / "bots/quant/entries/quant-018-strait-transit-count-base-rate.md"
SUMMARY = REPO / "bots/quant/replay/quant-018/SUMMARY.md"
S = requests.Session()
S.headers.update({"User-Agent": "quant-q018-citation-check/1.0 (keyless public data)"})
AS_OF = "2026-10-21"
checks = []


def add(name, ok, detail):
    checks.append({"check": name, "ok": bool(ok), "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}\n        {detail}")


def get(url, params=None):
    return S.get(url, params=params, timeout=90)


def main():
    text = ENTRY.read_text(encoding="utf-8")
    tail = text.split("## 出处", 1)[1]

    # 1. every external URL in the whole document
    urls = []
    for raw in re.findall(r"https?://[^\s)\]>\"`」]+", text):
        u = raw.rstrip(".,;")
        if "<" in u or u.endswith("market="):
            continue
        if u not in urls:
            urls.append(u)
    ok = True
    for u in urls:
        try:
            r = get(u)
            good = r.status_code == 200
            add("GET " + u[:110], good, f"HTTP {r.status_code}, {len(r.content)} bytes")
            ok &= good
        except Exception as exc:
            add("GET " + u[:110], False, f"request failed: {exc}")
            ok = False

    # 2. claims that need a specific request/field
    e = get("https://gamma-api.polymarket.com/events", params={
        "slug": "how-many-ships-transit-bab-el-mandeb-strait-week-of-october-12-20261006t134953677z"}).json()[0]
    labels = [m.get("groupItemTitle") for m in e["markets"]]
    resolved = [m.get("groupItemTitle") for m in e["markets"]
                if m.get("outcomePrices") in ('["1", "0"]', '["1","0"]')]
    fees = [m.get("feesEnabled") for m in e["markets"]]
    add("OOS event resolves 170-189, 5 buckets, fee 0",
        labels == ["<170", "170-189", "190-209", "210-229", "230+"]
        and resolved == ["170-189"] and all(f is False for f in fees),
        f"labels={labels}, resolved={resolved}, feesEnabled={fees}")

    d = get("https://data-api.polymarket.com/trades", params={
        "market": "0xc3f0b47231b149f564840ae702749014a9f1a63c39d20375d505eba509f10039",
        "limit": 500, "offset": 0}).json()
    add("data-api trades returns real prints for the OOS bucket",
        isinstance(d, list) and len(d) > 0 and {"price", "timestamp", "outcome"} <= set(d[0]),
        f"{len(d)} prints; first keys={sorted(d[0])[:8]}")

    q = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
    both = get(q, params={"where": "portname IN ('Bab el-Mandeb Strait','Strait of Hormuz')",
                          "returnCountOnly": "true", "f": "json"}).json().get("count")
    bab = get(q, params={"where": "portname = 'Bab el-Mandeb Strait'",
                         "returnCountOnly": "true", "f": "json"}).json().get("count")
    latest = get(q, params={"where": "portname = 'Bab el-Mandeb Strait'", "outFields": "date,n_total",
                            "returnGeometry": "false", "f": "json", "resultOffset": 0,
                            "resultRecordCount": 1, "orderByFields": "date DESC"}).json()["features"][0]["attributes"]
    add("PortWatch counts match the 2026-10-21 re-check",
        both == 5696 and bab == 2848 and latest.get("date") == "2026-10-18",
        f"both={both}, Bab={bab}, latest={latest}")

    # 3. local citations and frozen hashes
    local = [
        "bots/quant/notes/batch2-verification/quant-018.md",
        "bots/quant/notes/q018-price-test/REPORT.md",
        "bots/quant/notes/q018-paired/REPORT.md",
        "bots/quant/notes/q018-paired/run_output.txt",
        "bots/quant/notes/q018-paired/buckets.csv",
        "bots/dot/entries/dot-051-strait-count-paired-cash-supplement.md",
        "bots/quant/replay/quant-018/SUMMARY.md",
        "bots/quant/replay/quant-018/stdout.txt",
        "bots/quant/replay/quant-018/trades.csv",
        "bots/quant/replay/quant-018/inputs/buckets_bab.csv",
        "bots/quant/replay/quant-018/inputs/strict_bab.csv",
        "bots/quant/replay/quant-018/inputs/oos_bab_oct12.csv",
        "bots/quant/notes/postdecision-fills-20261021/REPORT.md",
        "bots/quant/notes/postdecision-fills-20261021/q018_strict.py",
        "bots/quant/notes/postdecision-fills-20261021/q018_strict.out",
        "bots/quant/notes/postdecision-fills-20261021/q018_strict_buckets.csv",
        "bots/quant/notes/scheduler/scratch/H-quant-018/tradable_backtest_stdout.txt",
        "bots/quant/notes/scheduler/scratch/H-quant-018/tradable_fills.csv",
        "bots/quant/notes/scheduler/scratch/H-quant-018/brier_start_check_stdout.txt",
    ]
    missing = [p for p in local if not (REPO / p).exists()]
    add("all cited local paths exist", not missing, f"{len(local)} paths; missing={missing}")

    hashes = {
        "bots/quant/replay/quant-018/inputs/buckets_bab.csv": "205f1facfdc5a120cbaae3f163166052736ca6e5",
        "bots/quant/replay/quant-018/inputs/oos_bab_oct12.csv": "420531cd824165f85252917b0a6a5232c0a266c3",
        "bots/quant/replay/quant-018/inputs/strict_bab.csv": "f58e5073e68a65533af6ba088031fe5413532f69",
        "bots/quant/notes/q018-paired/buckets.csv": "962b0b2434581fdf75a6ea8210836a6931baa6e3",
        "bots/quant/notes/postdecision-fills-20261021/q018_strict_buckets.csv": "ae0c71bbb900df8949203d18dadcd939ac4f6c5a",
    }
    bad_hash = {p: hashlib.sha1((REPO / p).read_bytes()).hexdigest()
                for p, h in hashes.items() if hashlib.sha1((REPO / p).read_bytes()).hexdigest() != h}
    add("frozen input sha1s unchanged", not bad_hash, f"claimed={hashes}, mismatches={bad_hash}")

    # 4. round-2 front matter and consistency with SUMMARY.md
    fm = text.split("---", 2)[1]
    fields = dict(re.findall(r"^([a-z_]+):\s*(.*)$", fm, re.M))
    allowed = {
        "evidence": {"回放", "前向", "回放+前向", "无"},
        "result": {"正", "负", "不显著", "未测"},
        "slot": {"新机制", "-"},
    }
    problems = []
    for k, v in allowed.items():
        if fields.get(k) not in v:
            problems.append(f"{k}={fields.get(k)!r}")
    if not re.fullmatch(r"\d+", fields.get("variants", "")):
        problems.append("variants not integer")
    if not (re.fullmatch(r"\d+", fields.get("variants_ext", "")) or fields.get("variants_ext") in {"不清楚", "-"}):
        problems.append("variants_ext invalid")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.\.\d{4}-\d{2}-\d{2}", fields.get("window", "")):
        problems.append("window invalid")
    if not (re.fullmatch(r"[0-9]+(?:\.[0-9]+)?%", fields.get("max_dd", "")) or fields.get("max_dd") in {"不清楚", "-"}):
        problems.append("max_dd invalid")
    if not (re.fullmatch(r"[0-9]+(?:\.[0-9]+)?%", fields.get("contribution", "")) or fields.get("contribution") == "不清楚"):
        problems.append("contribution invalid")
    add("8 round-2 fields valid", not problems, f"parsed={ {k: fields.get(k) for k in allowed} | {'variants': fields.get('variants'), 'variants_ext': fields.get('variants_ext'), 'window': fields.get('window'), 'max_dd': fields.get('max_dd'), 'contribution': fields.get('contribution')} }; problems={problems}")

    summary = SUMMARY.read_text(encoding="utf-8")
    need = [
        "variants（自己的）：**4**",
        "窗口 **2026-07-20..2026-10-18**",
        "result：**不显著**",
        "+0.7116",
        "+1.1505",
        "−0.9200",
        "1.5%",
        "10 个",
    ]
    miss = [x for x in need if x not in summary]
    add("entry fields agree with replay/SUMMARY.md",
        not miss and fields.get("variants") == "4" and fields.get("window") == "2026-07-20..2026-10-18"
        and fields.get("result") == "不显著" and fields.get("contribution") == "1.5%",
        f"missing in SUMMARY={miss}; entry variants/window/result/contribution="
        f"{fields.get('variants')}/{fields.get('window')}/{fields.get('result')}/{fields.get('contribution')}")

    out = {"as_of": AS_OF, "checks": checks}
    (HERE / "verify_citations.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    nfail = sum(not c["ok"] for c in checks)
    print(f"\nsummary: {len(checks)} checks, PASS={len(checks)-nfail}, FAIL={nfail}")
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
