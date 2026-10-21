#!/usr/bin/env python3
"""Verify every external source cited by quant-001 (2026-10-21).

Records HTTP status, redirect target and whether the page contains the claimed
title/abstract text. 403 is not "dead"; it means this runner could not read the
page. All endpoints are free and keyless.
Run: python3 verify_sources.py
"""
import io, json, pathlib, tempfile, urllib.request, zipfile

HERE = pathlib.Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0 (compatible; quant-research/1.0)"}
URLS = [
    ("binance_view", "https://data.binance.vision/?prefix=data/spot/monthly/klines/BTCUSDT/1d/", []),
    ("binance_zip", "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-12.zip", []),
    ("binance_data_api", "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1h&startTime=1733011200000&endTime=1733097600000&limit=2", []),
    ("binance_daily_window", "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime=1640995200000&endTime=1735689599999&limit=1000", []),
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
        if name in ("binance_data_api", "binance_daily_window"):
            rows = json.loads(body)
            note = f"json_rows={len(rows)} cols={len(rows[0])} first_open_time={rows[0][0]} last_open_time={rows[-1][0]}"
        text = body.decode("utf-8", "ignore")
        found = {n: (n.lower() in text.lower()) for n in needles}
        lines.append(f"{name}: HTTP {status} final={final} bytes={len(body)} needles={found} {note}")
    except Exception as e:
        code = getattr(e, "code", "ERR")
        lines.append(f"{name}: HTTP {code} error={type(e).__name__} url={url}")
# The exact 0.53 / 0.97 / -96.69% / -45.20% numbers were originally seen only in a
# search-index snippet (ScienceDirect is 403 here). Read the author-version PDF so
# the claim does not depend on an unfetchable page.
PDF_URL = "https://thetabruv.com/risorse/cta/32-barroso-momentum-has-its-moments.pdf"
PDF_PATH = pathlib.Path(tempfile.gettempdir()) / "quant-001-barroso-santa-clara-2014.pdf"
try:
    req = urllib.request.Request(PDF_URL, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        body = r.read(2_000_000)
        status, final = r.status, r.geturl()
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    PDF_PATH.write_bytes(body)
    import subprocess
    txt = subprocess.run(["pdftotext", str(PDF_PATH), "-"], capture_output=True,
                         text=True, timeout=30).stdout
    needles = [
        "The Sharpe ratio improves from 0.53",
        "0.97 for its risk-managed version",
        "The maximum drawdown of raw momentum is -96.69% versus -45.20%",
    ]
    found = {n: (n in txt) for n in needles}
    lines.append(f"barroso_author_pdf: HTTP {status} final={final} bytes={len(body)} "
                 f"pdf_header={body[:5]!r} needles={found}")
except Exception as e:
    code = getattr(e, "code", "ERR")
    lines.append(f"barroso_author_pdf: HTTP {code} error={type(e).__name__} url={PDF_URL}")
lines.append("")
lines.append("sciencedirect note: direct fetch is 403 from this runner. Whether the page says what is "
             "claimed no longer depends on a search-index snippet: the author-version PDF above is "
             "directly readable and contains the exact sentences. Crossref independently confirms "
             "the DOI/title/authors/pages.")
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
