# quant-023 工作者核对日志（deepseek-flash 原稿附录，含脚本全文）+ glm-5.3 事实核查报告

## VERIFICATION LOG (reviewer only, not for commit)

访问日期全部为 2026-10-20（UTC）。顺序即操作顺序。工作目录 `/workspace/agent-tools/quant-batch2/work_B20/`，文件：`mstr.json`、`btc_daily.csv`、`anchors.json`、`mnav_series.json`、`mnav_test.py`、`fetch_holdings.py`、`fetch_holdings2.py`。

### 1) 抓取与 HTTP 结果

| # | URL | HTTP | 取到的内容（逐字片段） |
|---|---|---|---|
| 1 | `https://stooq.com/q/d/l/?s=mstr.us&i=d` | 200 但非数据 | `<!DOCTYPE html>...This site requires JavaScript to verify your browser.`（3 行，无 CSV）→ 题面给的 stooq 不可用 |
| 2 | `https://stooq.com/q/d/l/?s=btcusd&i=d` | 200 但非数据 | 同上挑战页 |
| 3 | `https://query1.finance.yahoo.com/v8/finance/chart/MSTR?range=3y&interval=1d` | 200 | `"symbol":"MSTR","exchangeName":"NMS","firstTradeDate":897571800`；解析出 751 个收盘；首 `2023-10-20 34.80400085449219`，末 `2026-10-19 136.02000427246094`（脚本输出行：`751 897571800` / `2023-10-20 2026-10-19 34.80400085449219 136.02000427246094`） |
| 4 | `https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2025-09.zip` | 200（2,154 字节） | 解出 `1756684800000000,108246.36000000,109912.40000000,107255.00000000,109237.42000000,...` → **时间戳是微秒**（除 1e6 才得 2025-09-01） |
| 5 | `https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-01..19.zip` | 200 ×19 | 当月月度文件不存在（`btc-2026-10.zip` 解压报 `End-of-central-directory signature not found`），改用日文件；合并后 `btc_daily.csv` = 414 行数据（含表头 415 行），2025-09-01..2026-10-19 |
| 6 | `https://data.sec.gov/submissions/CIK0001050446.json` | 200（gzip，26,680 字节解压后） | `NAME Strategy Inc`；窗口内 8-K 共 79 份；`n8k_recent 210 range 2026-10-19 2021-08-24` |
| 7 | `https://www.strategy.com/`、`https://www.strategy.com/bitcoin`、`https://www.microstrategy.com/bitcoin` | 403 | `<TITLE>Access Denied</TITLE>`（Akamai）→ 公司官网不可用 |
| 8 | `https://saylortracker.com/`、`https://bitcointreasuries.net/` | 200 | 只做可用性探测，**未取任何数字** |
| 9 | `https://data.sec.gov/api/xbrl/companyconcept/CIK0001050446/dei/EntityCommonStockSharesOutstanding.json` | 404 | 无股本 XBRL |
| 10 | `https://data.sec.gov/api/xbrl/companyfacts/CIK0001050446.json` | 200（3,014,282 字节） | `['cik','entityName','facts']`；`dei` 只有 `['EntityPublicFloat']` |
| 11 | 11 份 8-K 的 `index.json` + 新闻稿 HTML（见下表） | 200 ×11 | 见下「持仓锚点逐字片段」 |
| 12 | 4 份 10-Q/10-K 封面页（见下表） | 200 ×4 | 见下「股本锚点逐字片段」 |

### 2) 持仓锚点（8-K 新闻稿逐字片段；编号为 `https://www.sec.gov/Archives/edgar/data/1050446/<acc>/index.json`）

| 抓取日 | acc | 逐字片段 | 我取的数 |
|---|---|---|---|
| 2025-10-06 | 000119312525230977 | `As of September 30, 2025, we held approximately 640,031 bitcoins that were acq...` | 640,031 |
| 2025-10-14 | 000119312525238132 | `Strategy Announces ATM and BTC Activity Updates Raised $27.3 million; Purchased 220 BTC; Now Holds 640,250 BTC` | 640,250 |
| 2025-10-30 | 000119312525258690 | `Bitcoin Highlights (as of October 26, 2025) • 640,808 bitcoin holdings` | 640,808 |
| 2025-12-01 | 000119312525303157 | `As of November 30, 2025. ... 650,000 BTC Holdings $59B BTC` | 650,000 |
| 2026-02-05 | 000105044626000012 | `Strategy Announces Fourth Quarter 2025 Financial Results; Holds 713,502 BTC` | 713,502 |
| 2026-03-30 | 000119312526130446 | `As of March 29, 2026, Strategy holds approximately 762,099 bitcoin that were acqu...` | 762,099 |
| 2026-05-05 | 000105044626000024 | `Strategy Announces First Quarter Financial Results; Currently Holds 818,334 BTC` | 818,334 |
| 2026-05-26 | 000119312526237907 | `as of May 25, 2026, Strategy holds 843,738 bitcoin, has 220,900 B...` | 843,738 |
| 2026-07-30 | 000162828026051027 | `Strategy Announces Second Quarter Financial Results; Currently Holds 843,775 Bitcoin` | 843,775 |
| 2026-09-08 | 000119312526384402 | `As of September 7, 2026, Strategy holds approximately 845,050 bitcoin that were acqu...` | 845,050 |
| 2026-09-14 | 000119312526389858 | `As of September 13, 2026, Strategy holds approximately 845,050 bitcoin that were acqu...` | 845,050 |

注意（如实记录）：2026-05-05 的 818,334 与 2026-05-26 的 843,738 之间 3 周增加 25,404 BTC，幅度偏大；新闻稿写「Bitcoin Highlights (as of May 3, 2026)」（as-of 日 2026-05-03），我没有找到解释，按原样使用并在此标注。

### 3) 股本锚点（10-Q/10-K 封面页逐字片段）

| 文件 URL | 逐字片段 | A 类 | B 类 |
|---|---|---:|---:|
| `.../000119312525262568/mstr-20250930.htm` | `As of October 30, 2025, the registrant had 267,713,485 and 19,640,250 shares of class A common stock and class B common stock outstanding, respectively.` | 267,713,485 | 19,640,250 |
| `.../000105044626000020/mstr-20251231.htm` | `As of February 13, 2026, the registrant had 314,112,458 and 19,640,250 shares ...` | 314,112,458 | 19,640,250 |
| `.../000105044626000031/mstr-20260331.htm` | `As of April 26, 2026, the registrant had 330,807,622 and 19,640,250 shares ...` | 330,807,622 | 19,640,250 |
| `.../000105044626000044/mstr-20260630.htm` | `As of July 24, 2026, the registrant had 364,585,501 and 19,640,250 shares ...` | 364,585,501 | 19,640,250 |

B 类「1:1 视作经济股数」**没有在本次抓取的任何原文里核实**（假设，未核实）；STRC 优先股规模本次未取，未计入 mNAV。

### 4) 脚本原样输出（`python3 mnav_test.py`，2026-10-20 本机）

```
anchors: [('2026-09-14', 845050), ('2026-09-08', 845050), ('2026-07-30', 843775), ('2026-05-26', 843738), ('2026-05-05', 818334), ('2026-03-30', 762099), ('2026-02-05', 713502), ('2025-12-01', 650000), ('2025-10-30', 640808), ('2025-10-14', 640250), ('2025-10-06', 640031)]
anchor span 2025-10-06 2026-09-14 n= 11
mNAV series days: 251 2025-10-20 2026-10-19
mNAV first/last/min/max: 1.204 0.820 0.606 1.251
BTC holdings first/last: 640459.25 845050 shares first/last: 287353735 417244576
buy&hold BTC (no cost)                     final=0.7413 cagr= -25.95% mdd= -48.62% switches= 1 pct_in_btc=100.0%
mNAV>=1 -> BTC else cash                   final=0.9471 cagr=  -5.31% mdd= -11.18% switches= 8 pct_in_btc=  8.4%
mNAV<1 -> BTC else cash (reverse)          final=0.7482 cagr= -25.25% mdd= -46.47% switches= 7 pct_in_btc= 91.6%
mNAV>=1.5 -> BTC else cash                 final=1.0000 cagr=  +0.00% mdd=  +0.00% switches= 0 pct_in_btc=  0.0%
mNAV<1.5 -> BTC else cash                  final=0.7391 cagr= -26.17% mdd= -48.62% switches= 1 pct_in_btc=100.0%
mNAV>=2.0 -> BTC else cash                 final=1.0000 cagr=  +0.00% mdd=  +0.00% switches= 0 pct_in_btc=  0.0%
mNAV<2.0 -> BTC else cash                  final=0.7391 cagr= -26.17% mdd= -48.62% switches= 1 pct_in_btc=100.0%
mNAV>=2.5 -> BTC else cash                 final=1.0000 cagr=  +0.00% mdd=  +0.00% switches= 0 pct_in_btc=  0.0%
mNAV<2.5 -> BTC else cash                  final=0.7391 cagr= -26.17% mdd= -48.62% switches= 1 pct_in_btc=100.0%
mNAV 90d z>0 -> BTC else cash              final=1.0825 cagr=  +8.28% mdd= -11.81% switches=21 pct_in_btc= 30.0%
mNAV 90d change>0 -> BTC else cash         final=0.8309 cagr= -16.96% mdd= -25.31% switches=11 pct_in_btc= 21.2%
mNAV 90d change<=0 -> BTC else cash        final=0.8376 cagr= -16.29% mdd= -44.87% switches=10 pct_in_btc= 78.8%
```

补充统计（同一 `mnav_series.json` 的第二次计算，原样输出）：

```
n 251 first (datetime.date(2025, 10, 20), 1.204) last (datetime.date(2026, 10, 19), 0.8196)
days>=1: 22 of 251
days<0.8: 62
median 0.870 p05 0.675 p95 1.059
2025-10 min 1.054 max 1.251 last 1.104
2025-11 min 0.895 max 1.118 last 0.901
2025-12 min 0.803 max 0.945 last 0.803
2026-01 min 0.780 max 0.857 last 0.823
2026-02 min 0.787 max 0.917 last 0.903
2026-03 min 0.821 max 0.927 last 0.824
2026-04 min 0.768 max 1.005 last 0.941
2026-05 min 0.885 max 1.034 last 0.932
2026-06 min 0.606 max 0.905 last 0.659
2026-07 min 0.651 max 0.729 last 0.680
2026-08 min 0.666 max 0.805 last 0.798
2026-09 min 0.753 max 0.936 last 0.888
2026-10 min 0.820 max 0.939 last 0.820
```

### 5) 复现失败记录（照实写）

- 第一版解析脚本 `fetch_holdings.py` / `fetch_holdings2.py` 把 8-K 主体页当新闻稿，79 份里只认出 1 个持仓数字；原因是「取第一个出现 bitcoin 的文件就跳出」。改成「取 bitcoin 出现次数最多的文件」后才有上表 11 个锚点。
- Binance 2025 年以后的 kline 文件时间戳是**微秒**，按毫秒解析直接报 `ValueError: year 57637 is out of range`；另外 2025+ 的月度文件带表头行，需跳过非数字首行。
- 2026-10 的月度 kline 文件尚不存在（`unzip` 报 `End-of-central-directory signature not found`），改用 daily 端点逐日抓 19 个文件。

### 6) 脚本全文（`mnav_test.py`）

```python
"""B20: MSTR mNAV as a BTC exposure switch. Only public, keyless data.
Inputs already downloaded in this dir: mstr.json (Yahoo chart API), btc monthly klines (Binance vision).
This script (a) re-fetches the Strategy 8-K press releases that state BTC holdings, keeping the exact
sentence, (b) builds a daily mNAV series, (c) runs a simple long-BTC/cash switch test with 0.30%/side.
"""
import json, re, urllib.request, gzip, time, datetime as dt, os, subprocess, csv, statistics as st

UA = {"User-Agent": "quant-research contact@example.org", "Accept-Encoding": "gzip"}


def get(u):
    q = urllib.request.Request(u, headers=UA)
    with urllib.request.urlopen(q, timeout=40) as r:
        d = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            d = gzip.decompress(d)
        return d.decode("utf-8", "replace")


# ---- (a) BTC-holding anchor sentences from 8-K press releases ----
ANCHORS = {  # filing date -> accession (chosen because the doc states holdings)
    "2025-10-14": "0001193125-25-251359",
    "2025-10-30": "0001193125-25-283269",
}
if os.path.exists("anchors.json"):
    anchors = json.load(open("anchors.json"))
else:
    sub = json.load(open("mstr_sub.json"))
    r = sub["filings"]["recent"]
    rows = [(r["form"][i], r["filingDate"][i], r["accessionNumber"][i]) for i in range(len(r["form"]))]
    anchors = []
    for form, date, acc in rows:
        if form != "8-K" or not ("2025-09-20" <= date <= "2026-10-20"):
            continue
        base = "https://www.sec.gov/Archives/edgar/data/1050446/%s/" % acc.replace("-", "")
        try:
            idx = json.loads(get(base + "index.json"))
        except Exception:
            continue
        names = [f["name"] for f in idx["directory"]["item"] if f["name"].endswith(".htm") and "index" not in f["name"]]
        best, bestc = "", -1
        for n in names:
            try:
                t = get(base + n)
            except Exception:
                continue
            t = re.sub(r"<[^>]+>", " ", t)
            t = re.sub(r"&nbsp;?|&#160;", " ", t)
            t = re.sub(r"\s+", " ", t)
            c = len(re.findall(r"bitcoin", t, re.I))
            if c > bestc:
                bestc, best = c, t
        for m in re.finditer(r"([\d][\d,]{5,9})\s*(?:bitcoin|BTC)", best, re.I):
            ctx = best[max(0, m.start() - 160):m.end() + 40]
            if re.search(r"hold|treasury|acquir|purchas", ctx, re.I):
                anchors.append({"date": date, "acc": acc, "n": int(m.group(1).replace(",", "")), "ctx": ctx})
                break
        time.sleep(0.05)
    json.dump(anchors, open("anchors.json", "w"), indent=1)
print("anchors:", [(a["date"], a["n"]) for a in anchors])

# ---- (b) daily closes ----
y = json.load(open("mstr.json"))["chart"]["result"][0]
ts = y["timestamp"]
cl = y["indicators"]["quote"][0]["close"]
mstr = {}
for t, c in zip(ts, cl):
    if c is None:
        continue
    d = dt.datetime.fromtimestamp(t, dt.UTC).date()
    mstr[d] = c

btc = {}
if not os.path.exists("btc_daily.csv"):
    with open("btc_daily.csv", "w") as f:
        f.write("date,close\n")
        for ym in ["2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03",
                   "2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]:
            z = "btc-%s.zip" % ym
            if not os.path.exists(z):
                subprocess.run(["curl", "-sL", "--max-time", "40", "-o", z,
                                "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-%s.zip" % ym])
            subprocess.run(["unzip", "-o", "-q", z])
            fn = "BTCUSDT-1d-%s.csv" % ym
            for row in csv.reader(open(fn)):
                if not re.match(r"^\d+$", row[0]):   # newer monthly files carry a header row
                    continue
                t = int(row[0])
                t = t / 1e6 if t > 1e14 else t / 1e3   # 2025+ files use microseconds
                d = dt.datetime.fromtimestamp(t, dt.UTC).date()
                f.write("%s,%s\n" % (d.isoformat(), row[4]))
for dd in range(1, 20):   # 2026-10 is still an open month: use the daily endpoint
    z = "btc-d-2026-10-%02d.zip" % dd
    if not os.path.exists(z):
        subprocess.run(["curl", "-sL", "--max-time", "40", "-o", z,
                        "https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-%02d.zip" % dd])
    subprocess.run(["unzip", "-o", "-q", z])
    fn = "BTCUSDT-1d-2026-10-%02d.csv" % dd
    for row in csv.reader(open(fn)):
        if not re.match(r"^\d+$", row[0]):
            continue
        t = int(row[0])
        t = t / 1e6 if t > 1e14 else t / 1e3
        d = dt.datetime.fromtimestamp(t, dt.UTC).date()
        with open("btc_daily.csv", "a") as f:
            f.write("%s,%s\n" % (d.isoformat(), row[4]))
for row in csv.DictReader(open("btc_daily.csv")):
    btc[dt.date.fromisoformat(row["date"])] = float(row["close"])

# ---- shares outstanding (10-Q / 10-K cover pages, 已读) ----
shares_pts = [(dt.date(2025, 10, 30), 267713485 + 19640250), (dt.date(2026, 2, 13), 314112458 + 19640250),
              (dt.date(2026, 4, 26), 330807622 + 19640250), (dt.date(2026, 7, 24), 364585501 + 19640250)]


def shares_on(d):
    if d <= shares_pts[0][0]:
        return shares_pts[0][1]
    for (d0, v0), (d1, v1) in zip(shares_pts, shares_pts[1:]):
        if d0 <= d <= d1:
            w = (d - d0).days / (d1 - d0).days
            return v0 + w * (v1 - v0)
    # after last observed point: extend the last segment's daily growth rate (documented approximation)
    d0, v0 = shares_pts[-2]
    d1, v1 = shares_pts[-1]
    return v1 + (d - d1).days * (v1 - v0) / (d1 - d0).days


anch = sorted([(dt.date.fromisoformat(a["date"]), a["n"]) for a in anchors])
print("anchor span", anch[0][0], anch[-1][0], "n=", len(anch))


def btc_on(d):
    dd = d
    for _ in range(10):
        if dd in btc:
            return btc[dd]
        dd -= dt.timedelta(days=1)
    return None


def hold_on(d):
    # step-flat before first anchor, linear interpolation between anchors, flat after last
    if d <= anch[0][0]:
        return anch[0][1]
    for (d0, v0), (d1, v1) in zip(anch, anch[1:]):
        if d0 <= d <= d1:
            w = (d - d0).days / max(1, (d1 - d0).days)
            return v0 + w * (v1 - v0)
    return anch[-1][1]


series = []
start = dt.date(2025, 10, 20)
for d in sorted(m for m in mstr if start <= m <= dt.date(2026, 10, 19)):
    b = btc_on(d)
    if not b:
        continue
    mcap = mstr[d] * shares_on(d)
    nav = hold_on(d) * b
    series.append((d, mstr[d], b, hold_on(d), shares_on(d), mcap / nav))
print("mNAV series days:", len(series), series[0][0], series[-1][0])
print("mNAV first/last/min/max: %.3f %.3f %.3f %.3f" % (series[0][5], series[-1][5],
      min(s[5] for s in series), max(s[5] for s in series)))
print("BTC holdings first/last:", series[0][3], series[-1][3], "shares first/last:", int(series[0][4]), int(series[-1][4]))

# ---- (c) switch test ----
px = {d: b for d, _, b, _, _, _ in series}
ms = {d: v for d, _, _, _, _, v in series}
days = [d for d, *_ in series]
ret = {days[i]: px[days[i]] / px[days[i - 1]] - 1 for i in range(1, len(days))}


def run(signal_fn, cost=0.003, label=""):
    pos, eq, trades, curve = 0, 1.0, 0, []
    for i in range(1, len(days)):
        d = days[i]
        want = signal_fn(i)
        if want != pos:
            eq *= (1 - cost)
            trades += 1
            pos = want
        eq *= (1 + pos * ret[d])
        curve.append((d, eq))
    yrs = (days[-1] - days[0]).days / 365.25
    peak, mdd = -1, 0
    for _, e in curve:
        peak = max(peak, e)
        mdd = min(mdd, e / peak - 1)
    return dict(label=label, final=eq, cagr=eq ** (1 / yrs) - 1, mdd=mdd, trades=trades,
                days_in_btc=sum(1 for i in range(1, len(days)) if signal_fn(i)))


def zs(i, look=90):
    lo = max(0, i - look)
    w = [ms[days[j]] for j in range(lo, i + 1)]
    return (ms[days[i]] - sum(w) / len(w)) / (st.pstdev(w) + 1e-9)


def zl(i, look=90):
    j = max(0, i - look)
    return ms[days[i]] - ms[days[j]]


res = []
res.append(run(lambda i: 1, cost=0.0, label="buy&hold BTC (no cost)"))
res.append(run(lambda i: 1 if ms[days[i]] >= 1.0 else 0, label="mNAV>=1 -> BTC else cash"))
res.append(run(lambda i: 1 if ms[days[i]] < 1.0 else 0, label="mNAV<1 -> BTC else cash (reverse)"))
for th in (1.5, 2.0, 2.5):
    res.append(run(lambda i, th=th: 1 if ms[days[i]] >= th else 0, label="mNAV>=%.1f -> BTC else cash" % th))
    res.append(run(lambda i, th=th: 1 if ms[days[i]] < th else 0, label="mNAV<%.1f -> BTC else cash" % th))
res.append(run(lambda i: 1 if zs(i) > 0 else 0, label="mNAV 90d z>0 -> BTC else cash"))
res.append(run(lambda i: 1 if zl(i) > 0 else 0, label="mNAV 90d change>0 -> BTC else cash"))
res.append(run(lambda i: 1 if zl(i) <= 0 else 0, label="mNAV 90d change<=0 -> BTC else cash"))
for r in res:
    print("%-42s final=%.4f cagr=%+7.2f%% mdd=%+7.2f%% switches=%2d pct_in_btc=%5.1f%%" %
          (r["label"], r["final"], r["cagr"] * 100, r["mdd"] * 100, r["trades"],
           100 * r["days_in_btc"] / (len(days) - 1)))
json.dump([(str(s[0]), round(s[5], 4)) for s in series], open("mnav_series.json", "w"))
```

---

## glm-5.3 事实核查报告

# Fact-check report — B20.md (MSTR mNAV as BTC switch)

**Re-fetches (all 2026-10-20 UTC):** Yahoo MSTR chart ✓ (751 closes, first 34.804 on 2023-10-20, last 136.02 on 2026-10-19, firstTradeDate 897571800); Binance BTCUSDT-1d-2025-09.zip ✓ (first row `1756684800000000,108246.36,…,109237.42`, 2154 bytes, microsecond ts); EDGAR submissions ✓ (`Strategy Inc`, 210 recent 8-Ks); **all 11 BTC-holding anchors** found verbatim in the cited 8-K press releases (640,031 / 640,250 / 640,808 / 650,000 / 713,502 / 762,099 / 818,334 / 843,738 / 843,775 / 845,050 ×2); **all 4 share cover sentences verbatim**; stooq JS-challenge ✓, strategy.com 403 ✓, XBRL concept 404 ✓, companyfacts 3,014,282 bytes with dei only `EntityPublicFloat` ✓, 2026-10 monthly zip absent ✓, trackers 200 ✓.

**Script re-run:** extracted `mnav_test.py` from the log (byte-identical to `work_B20/`), re-ran in a clean dir — **all 13 result rows and all supplementary stats (251 days, 1.204→0.8196, 22/251 ≥1, median 0.870, p05 0.675, p95 1.059, 13 monthly rows) reproduce exactly**; `mnav_series.json` identical.

**Problems (all minor, fixable):**
1. `Q4 业绩稿 713,502（稿中无明确 as-of 日）`、`Q1 业绩稿 818,334（无明确 as-of 日）` — **MISMATCH**: releases state "Bitcoin Highlights (as of February 1, 2026) 713,502" and "(as of May 3, 2026) …818,334". Use those as-of dates in `anchors.json` (currently filing dates 2026-02-05/05-05 shift interpolation by 2–4 days).
2. `最近 210 份 8-K，2021-08-04..2026-10-19` — MISMATCH: oldest recent 8-K is **2021-08-24**.
3. `批量抓 83 个 8-K` / log `窗口内 8-K 共 83 份` — MISMATCH: I count **79** in the 2025-09-20..2026-10-20 window.
4. `我比较了 8 个变体` — script runs **11** signal variants (5 effectively distinct, since 1.5/2.0/2.5 never trigger).
5. `BTC 415 日线` / `btc_daily.csv = 415 行数据` — off-by-one: **414** data rows (415 incl. header).
6. 门槛自查 #2 `12 个月以上的数据` — exactly 12 months were used (2025-10-20..2026-10-19).
7. Front-matter: `id: quant-XXX` placeholder must be a real id matching the eventual filename (next free: quant-014); `category: X` is dubious — the rule generates its own signal (X = "自己不产生信号"), S or T fits better; `status: 草稿` (not yet 待核).

**Compliance:** no keys/paid data; 0.30%/side per GUIDE §9 applied per-switch; honest 门槛自查 (admits gates 1/5/6 fail, data-snooping on C3); no backtest claims beyond what the script runs; no third-party self-reported numbers needing 来源自报 labels (trackers explicitly unused). **Duplication:** none — KNOWN.md, quant-001..013 and dot entries contain no MSTR/mNAV entry; quant-013 (Coinbase premium) and S-S3-etf-flow use different key variables; B20 already claimed in `bots/quant/CLAIMS.md`.

No fabrication: every load-bearing number and quote verified, results fully reproducible.

VERDICT: FIX — all core evidence reproduces, but the placeholder id, wrong "no as-of date" claim, and several small count/date slips need correction before scoring.
GATES_PASSING: 4/7
