#!/usr/bin/env python3
"""Verify every source cited by quant-002 and the numbers quoted in the entry.

Checks:
 1. data.binance.vision listing page + a real monthly zip (HTTP, zip members).
 2. data-api.binance.vision klines endpoint (12 columns).
 3. aggTrades VWAP for one hour == fills_BTC.csv first_vwap (proves the fill is
    an actual traded price, not a modelled one).
 4. local xqt-migration files exist; results.csv rows equal the entry table.
 5. known/KNOWN.md line for E-E2-turn-of-month.
 6. entry front matter (id/date/status) is unchanged.
No keys, no trading.  Writes verify_sources_stdout.txt.
Run: python3 verify_sources.py
"""
import io, json, pathlib, re, urllib.request, zipfile
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
NOTES = HERE.parent.parent.parent          # bots/quant/notes
ENTRY = HERE.parent.parent.parent.parent / "entries" / "quant-002-tom-monday-oos-counterevidence.md"
UA = {"User-Agent": "Mozilla/5.0 (compatible; quant-research/1.0)"}
lines = []


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.geturl(), r.read()


# ---- 1. Binance public data ----
for name, url, needle in [
    ("binance_view_eth", "https://data.binance.vision/?prefix=data/spot/monthly/klines/ETHUSDT/1d/", None),
    ("binance_zip_eth_2026_09", "https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1d/ETHUSDT-1d-2026-09.zip", None),
]:
    try:
        status, final, body = fetch(url)
        note = ""
        if name.startswith("binance_zip"):
            z = zipfile.ZipFile(io.BytesIO(body))
            member = z.namelist()[0]
            df = pd.read_csv(z.open(member), header=None)
            note = f"zip_members={z.namelist()} rows={len(df)} cols={df.shape[1]}"
        lines.append(f"{name}: HTTP {status} bytes={len(body)} {note} url={final}")
    except Exception as e:
        lines.append(f"{name}: ERROR {type(e).__name__} {getattr(e, 'code', '')} url={url}")

try:
    status, final, body = fetch("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=2")
    rows = json.loads(body)
    lines.append(f"binance_data_api_klines: HTTP {status} rows={len(rows)} cols={len(rows[0])} "
                 f"last_close={rows[-1][4]} url={final}")
except Exception as e:
    lines.append(f"binance_data_api_klines: ERROR {type(e).__name__} {getattr(e, 'code', '')}")

# ---- 2. aggTrades VWAP cross-check ----
try:
    start = int(pd.Timestamp("2026-09-01 00:00:00", tz="UTC").timestamp() * 1000)
    end = int(pd.Timestamp("2026-09-01 01:00:00", tz="UTC").timestamp() * 1000) - 1
    base = "https://data-api.binance.vision/api/v3/aggTrades"
    status, _, body = fetch(f"{base}?symbol=BTCUSDT&startTime={start}&endTime={end}&limit=1000")
    page = json.loads(body)
    trades = list(page)
    pages = 1
    while len(page) == 1000 and pages < 60:
        last_id = page[-1]["a"]
        status, _, body = fetch(f"{base}?symbol=BTCUSDT&fromId={last_id + 1}&limit=1000")
        page = [t for t in json.loads(body) if t["T"] <= end]
        trades += page
        pages += 1
        if not page:
            break
    quote = sum(float(t["p"]) * float(t["q"]) for t in trades)
    baseq = sum(float(t["q"]) for t in trades)
    at_vwap = quote / baseq
    fills = pd.read_csv(HERE / "fills_BTC.csv", index_col=0, parse_dates=True)
    k_vwap = float(fills.loc["2026-09-01", "first_vwap"])
    lines.append(f"aggtrades_vwap_check: pages={pages} trades={len(trades)} "
                 f"aggtrades_vwap={at_vwap:.8f} kline_first_vwap={k_vwap:.8f} "
                 f"diff_bp={(at_vwap / k_vwap - 1) * 1e4:.6f}")
except Exception as e:
    lines.append(f"aggtrades_vwap_check: ERROR {type(e).__name__} {getattr(e, 'code', '')}")

# ---- 3. local notes ----
lines.append("")
lines.append("local files:")
for rel in ["xqt-migration/README.md", "xqt-migration/reproduce.py", "xqt-migration/results.csv",
            "scheduler/scratch/H-quant-002/fills_BTC.csv",
            "scheduler/scratch/H-quant-002/fills_ETH.csv",
            "scheduler/scratch/H-quant-002/tradable_results.csv",
            "scheduler/scratch/H-quant-002/windows.csv",
            "scheduler/scratch/H-quant-002/placebo.csv"]:
    p = NOTES / rel
    lines.append(f"  {rel}: exists={p.exists()} bytes={p.stat().st_size if p.exists() else 0}")

# ---- 4. results.csv numbers quoted in the entry ----
res = pd.read_csv(NOTES / "xqt-migration" / "results.csv")
checks = [
    ("M3_BTC_tom_calendar_exact", 0.001, -26.5931, -35.9785),
    ("M3_ETH_tom_calendar_exact", 0.001, -44.0299, -55.7987),
    ("M3_BTC_mon_calendar_exact", 0.001, 41.5224, -23.0872),
    ("M3_ETH_mon_calendar_exact", 0.001, 11.2663, -39.6449),
    ("M3_BTC_tom_orig_shift", 0.001, 16.4274, -25.2735),
    ("M3_ETH_tom_orig_shift", 0.001, -31.3705, -52.5805),
    ("M3_BTC_tom_calendar_exact", 0.003, -38.9926, -45.7145),
    ("M3_ETH_tom_calendar_exact", 0.003, -53.4788, -61.0297),
    ("M3_BTC_mon_calendar_exact", 0.003, -35.9157, -43.9248),
    ("M3_ETH_mon_calendar_exact", 0.003, -49.6459, -59.6995),
    ("M3_BTC_tom_orig_shift", 0.003, -3.1606, -30.7771),
    ("M3_ETH_tom_orig_shift", 0.003, -42.9414, -57.5562),
    ("M3_BTC_mon_orig_shift", 0.001, -35.6281, -55.3987),
    ("M3_ETH_mon_orig_shift", 0.001, -62.5463, -71.4445),
    ("M3_BTC_mon_orig_shift", 0.003, -70.8375, -76.1320),
    ("M3_ETH_mon_orig_shift", 0.003, -83.0522, -85.1371),
    ("EW_hold_BES", 0.003, 473.2254, -64.3100),
]
lines.append("")
lines.append("xqt-migration/results.csv checks (compound/path_dd):")
all_ok = True
for name, fee, comp, dd in checks:
    row = res[(res.name == name) & (res.fee_side == fee)]
    ok = len(row) == 1 and abs(row.iloc[0].compound_pct - comp) < 0.01 and abs(row.iloc[0].path_dd_pct - dd) < 0.01
    all_ok &= ok
    lines.append(f"  {name} fee={fee}: found={len(row)} compound={row.iloc[0].compound_pct if len(row) else None} "
                 f"path_dd={row.iloc[0].path_dd_pct if len(row) else None} ok={ok}")
lines.append(f"all results.csv checks ok: {all_ok}")

# ---- 5. known entry ----
known = (NOTES.parent.parent.parent / "known" / "KNOWN.md").read_text()
needle = "| E-E2-turn-of-month | 月末月初持有 |"
lines.append("")
lines.append(f"known/KNOWN.md contains {needle!r}: {needle in known}")

# ---- 6. entry front matter ----
txt = ENTRY.read_text()
front = txt.split("---", 2)[1]
lines.append("")
lines.append(f"entry: {ENTRY.relative_to(ENTRY.parents[3])}")
for key in ("id", "date", "status"):
    m = re.search(rf"^{key}:\s*(.+)$", front, re.M)
    lines.append(f"  {key}: {m.group(1).strip() if m else 'MISSING'}")

out = "\n".join(lines)
print(out)
(HERE / "verify_sources_stdout.txt").write_text(out + "\n")
