#!/usr/bin/env python3
"""Verify every external source cited by quant-001 (2026-10-21).

Records HTTP status, redirect target and whether the page contains the claimed
title/abstract text. 403 is not "dead"; it means this runner could not read the
page. All endpoints are free and keyless.
Run: python3 verify_sources.py
"""
import io, json, pathlib, urllib.request, zipfile

HERE = pathlib.Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0 (compatible; quant-research/1.0)"}
URLS = [
    ("binance_view", "https://data.binance.vision/?prefix=data/spot/monthly/klines/BTCUSDT/1d/", []),
    ("binance_zip", "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2026-09.zip", []),
    ("binance_data_api", "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=2", []),
    ("repec", "https://ideas.repec.org/a/eee/jfinec/v116y2015i1p111-120.html",
     ["Momentum has its moments", "nearly doubles the Sharpe ratio"]),
    ("crossref", "https://api.crossref.org/works/10.1016/j.jfineco.2014.11.010",
     ["Momentum has its moments", "Barroso", "Santa-Clara", "111-120"]),
    ("doi", "https://doi.org/10.1016/j.jfineco.2014.11.010", []),
    ("sciencedirect", "https://www.sciencedirect.com/science/article/abs/pii/S0304405X14002566", []),
]
lines = []
for name, url, needles in URLS:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=45) as r:
            body = r.read(2_000_000)
            status, final = r.status, r.geturl()
        note = ""
        if name == "binance_zip":
            z = zipfile.ZipFile(io.BytesIO(body))
            note = f"zip_ok members={z.namelist()}"
        if name == "binance_data_api":
            rows = json.loads(body)
            note = f"json_rows={len(rows)} cols={len(rows[0])} last_close={rows[-1][4]}"
        text = body.decode("utf-8", "ignore")
        found = {n: (n.lower() in text.lower()) for n in needles}
        lines.append(f"{name}: HTTP {status} final={final} bytes={len(body)} needles={found} {note}")
    except Exception as e:
        code = getattr(e, "code", "ERR")
        lines.append(f"{name}: HTTP {code} error={type(e).__name__} url={url}")
lines.append("")
lines.append("sciencedirect note: direct fetch is 403 from this runner. The page exists and its "
             "search-indexed text was seen on 2026-10-21 containing: 'The Sharpe ratio improves from "
             "0.53 for unmanaged momentum to 0.97 for its risk-managed version' and 'The maximum "
             "drawdown of raw momentum is -96.69% versus -45.20% for its risk-managed version'. "
             "Crossref confirms the DOI/title/authors/pages independently.")
lines.append("")
lines.append("local notes checked:")
for p in ["../../../xqt-migration/reproduce.py", "../../../xqt-migration/results.csv",
          "../../../xqt-migration/q001-robustness/REPORT.md",
          "../../../xqt-migration/q001-robustness/run_output.txt",
          "../../../xqt-migration/q001-robustness/variants.csv"]:
    q = (HERE / p).resolve()
    lines.append(f"  {p}: exists={q.exists()} bytes={q.stat().st_size if q.exists() else 0}")
text = "\n".join(lines)
print(text)
(HERE / "verify_sources_stdout.txt").write_text(text + "\n")
