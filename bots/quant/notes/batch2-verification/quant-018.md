# quant-018 工作者核对日志（deepseek-flash 原稿附录，含脚本全文）+ glm-5.3 事实核查报告

## VERIFICATION LOG (reviewer only, not for commit)

所有抓取均在 2026-10-20 本会话内用 `curl -sL` / Python `urllib` 完成，无密钥、无登录、未下单。逐条结果：

| # | URL | HTTP | 取到的原文/数字 |
|---|---|---|---|
| 1 | `https://gamma-api.polymarket.com/events?tag_slug=geopolitics&limit=500&closed=true&order=endDate&ascending=false` | 200 | JSON，`len=100`（服务端把 limit 截到 100 条/页），3,988,406 字节；`endDate` 首条 2027-12-31T00:00:00Z，末条 2026-10-08T03:59:00Z |
| 2 | 同上 `closed=false&order=endDate&ascending=true` | 200 | `len=100`，4,390,404 字节；首条 `guinea-bissau-presidential-election` |
| 3 | 同上 `limit=100&closed=true&offset=100&order=endDate&ascending=false` | 200 | `len=100`，`endDate` 2026-10-08..2026-09-01 |
| 4 | `https://gamma-api.polymarket.com/events?slug=how-many-ships-transit-bab-el-mandeb-strait-week-of-october-5` | 200 | `closed=true`、`endDate=2026-10-12T03:59:00Z`、`volume=13097.774817000001`；5 档 `<170/170-189/190-209/210-229/230+`，`190-209` 档 `outcomePrices=["1","0"]`、`umaResolutionStatus=resolved`；`description` 全文（PortWatch/「Arrivals of Ships」/14 天兜底/修订条款） |
| 5 | `.../events?slug=how-many-ships-transit-bab-el-mandeb-strait-week-of-october-19` | 200 | `closed=false`、`volume=13595.368699`、`liquidity=53710.92511`、`negRisk=true`；bid/ask：`<170` 0.127/0.16、`170-189` 0.33/0.36、`190-209` 0.35/0.39、`210-229` 0.065/0.106、`230+` 0.028/0.104；`feesEnabled=False`、`feeSchedule=None`、`clobRewards` 逐档 `rewardsDailyRate=6/39/42/5/8`（`170-189` 档 39；其余字段 `rewardsAmount=0,startDate:'2026-10-20',endDate:'2500-12-31'`）、`rewardsMinSize=50`、`rewardsMaxSpread=8.5`、`restricted=True`、`startDate=2026-10-13T09:34:52Z` |
| 6 | `.../events?slug=how-many-ships-transit-the-strait-of-hormuz-week-of-october-19` | 200 | `volume=5539.661748`、`liquidity=22748.92012`；6 档 bid/ask：`<20` 0.25/0.35、`20-24` 0.319/0.375、`25-29` 0.29/0.38、`30-34` 0.03/0.11、`35-39` 0.013/0.104、`40+` 0.013/0.089；中价 `0.3/0.347/0.335/0.07/0.0585/0.051` |
| 7 | `https://gamma-api.polymarket.com/public-search?q=how%20many%20ships%20transit&limit_per_type=100&events_status=all` | 200 | 47 条（全部是 `how-many-*` 周度 event），按 `closed` 分：**43 个已关闭（Hormuz 31，2026-03-16..2026-10-12；Bab 12，2026-07-26..2026-10-12）+ 4 个 open（两海峡各 2）**；另跑一遍逐 slug 复核：`total 47 closed 43 {'hormuz': {'tot': 33, 'closed': 31}, 'bab': {'tot': 14, 'closed': 12}}`，且**所有已关闭事件都有已结算档位** |
| 8 | `.../public-search?q=UKMTO&limit_per_type=50&events_status=all` | 200 | 1 个 event：`how-many-ukmto-notices-october-1925` |
| 9 | `.../public-search?q=Strait%20of%20Hormuz&…` / `q=Bab%20el-Mandeb&…` | 200 | 50 / 23 个 event；月度均值模板共 6 个（两个搜索按 slug 去重的 union：`avgpt-of-ships-…` 5 个 + `avg-of-ships-…` 1 个） |
| 10 | `https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services?f=json` | 200 | 服务清单含 `Daily_Chokepoints_Data`、`Daily_Ports_Data`、`PortWatch_chokepoints_database` |
| 11 | `.../Daily_Chokepoints_Data/FeatureServer/0?f=json` | 200 | `name=Daily_Chokepoints_Data`；字段 `date(esriFieldTypeDateOnly), year, month, day, portid, portname, n_container, n_dry_bulk, n_general_cargo, n_roro, n_tanker, n_cargo, n_total, capacity_*` |
| 12 | `.../Daily_Chokepoints_Data/FeatureServer/0/query?where=portname IN ('Bab el-Mandeb Strait','Strait of Hormuz')&outFields=date,portname,n_total&…&resultOffset=<翻页>` | 200 | 首页 `exceededTransferLimit=true`、1,000 行；分页合计 **5,682 行**（Bab 2,841 + Hormuz 2,841），`date` 覆盖 **2019-01-01..2026-10-11** |
| 13 | `https://portwatch.imf.org/pages/6b1814d64903461b98144a6cc25eb79c` | 200 | 216,598 字节 ArcGIS Hub 页面；HTML 内**未见**指向日度表的直接链接（只找到 logo item id）→ 标「部分」 |
| 14 | `https://clob.polymarket.com/prices-history?market=83323157431384565919039651171113228419822107706617450318634509280075717583619&interval=max&fidelity=60` | 200 | `{"history":[{"t":1790816418,"p":0.255},{"t":1790820019,"p":0.405},{"t":1790823632,"p":0.34},…]}` 非空 → 已关闭市场**部分**有价格历史 |

失败/未取到（照写）：`/events?tag_slug=geopolitics&limit=500` 无法一次拿全（截到 100/页）；PortWatch 页面 HTML 未暴露日度表链接；3–5 月的 PortWatch 历史快照不可得（故 7 个 MISMATCH 未解释）。

### 我自己的算术（公式全部写出）

- 周总量：`week_total = Σ_{d∈Mon..Sun} n_total(d)`，只保留 7 天齐全的周 → **405 个完整周**（每海峡）。
- Bab 近 12 完整周：`198,215,178,206,206,184,178,191,173,190,207,198` → `mean=2324/12=193.67`、`sd=13.51`（样本 sd，除 11）、`min=173`、`max=215`；全样本 405 周 `min=173`、`max=578`。
- Hormuz 近 30 完整周：`mean=46.00`、`sd=44.17`、`min=10`、`max=213`；`|WoW Δ|`: n=29、median=13、p90=68、max=128（排序后取第 `int(0.9*29)=26` 位）。
- 基准率：`p_i = (k_i+1)/(12+n)`，n=5 → 分母 17：`<170 1/17=0.059`、`170-189 5/17=0.294`、`190-209 8/17=0.471`、`210-229 2/17=0.118`、`230+ 1/17=0.059`。
- 中价合计：Bab `0.1435+0.345+0.370+0.0855+0.066 = 1.010`；Hormuz `0.300+0.347+0.335+0.070+0.0585+0.051 = 1.1615`；Hormuz 卖价合计 `0.35+0.375+0.38+0.11+0.104+0.089 = 1.408`，买价合计 `0.915`。
- EV：NO 可成交卖价 `= 1 − YES bestBid` → `<170`: `1−0.127=0.873`；公允 `1−0.059=0.9412`；`EV/份=0.9412−0.873=+0.0682`；`EV/资本=0.0682/0.873=+7.8%`。`230+`: `1−0.028=0.972`，`EV=0.9412−0.972=−0.0308`。
- 盈亏平衡：买 NO 于 0.873 且要覆盖 0.01 安全垫 → 真实概率须 `< 0.127−0.01 = 0.117`。
- 费用：`feesEnabled=false` ⇒ 按 GUIDE 公式 `费=份数×费率×p×(1−p)` 费率 0 ⇒ 费 0；半价差 `<170` = `(0.16−0.127)/2 = 0.0165`。

### 复算脚本与输出（`pw_verify.py`，完整可重跑）

```python
import json, urllib.request, datetime, collections, re

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research/no-auth"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

s = get("https://gamma-api.polymarket.com/public-search?q=how%20many%20ships%20transit&limit_per_type=100&events_status=all")
slugs = [e["slug"] for e in (s.get("events") or []) if "how-many" in e["slug"]]

BASE = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
        "Daily_Chokepoints_Data/FeatureServer/0/query")
rows, off = [], 0
while True:
    q = ("?where=portname%20IN%20('Bab%20el-Mandeb%20Strait','Strait%20of%20Hormuz')"
         "&outFields=date,portname,n_total&returnGeometry=false&f=json"
         "&resultOffset=" + str(off) + "&resultRecordCount=1000&orderByFields=date%20ASC")
    fs = get(BASE + q).get("features", [])
    rows += [f["attributes"] for f in fs]
    if len(fs) < 1000: break
    off += 1000

days = collections.defaultdict(dict)      # (port, monday) -> {weekday: n_total}
for a in rows:
    d = datetime.date.fromisoformat(a["date"])
    mon = d - datetime.timedelta(days=d.weekday())
    days[(a["portname"], mon)][d.weekday()] = a["n_total"]
wk = {k: sum(v.values()) for k, v in days.items() if len(v) == 7}

for slug in slugs:
    ev = get("https://gamma-api.polymarket.com/events?slug=" + slug)[0]
    m = re.search(r"from (\w+ \d+, \d{4}), through (\w+ \d+, \d{4})", ev.get("description",""))
    if not m: print("NO-DATE-PARSE", slug); continue
    d0 = datetime.datetime.strptime(m.group(1), "%B %d, %Y").date()
    port = "Strait of Hormuz" if "hormuz" in slug else "Bab el-Mandeb Strait"
    tot = wk.get((port, d0))
    res = [mk.get("groupItemTitle") for mk in ev["markets"] if mk.get("outcomePrices") == '["1", "0"]']
    print(d0, port[:18], "pw=" + str(tot), "resolved=" + str(res[:1]), "closed=" + str(ev["closed"]))

def iv(label):                             # bracket label -> interval
    if label.endswith("+"): return (int(label[:-1]), 10**9)
    if label.startswith("<"): return (-10**9, int(label[1:]) - 1)
    a, b = label.split("-"); return (int(a), int(b))
```

**输出（逐行摘录）**：

```
2026-03-23 Strait of Hormuz   pw=  25 resolved=20-24     MISMATCH
2026-03-30 Strait of Hormuz   pw=  37 resolved=45+       MISMATCH
2026-04-06 Strait of Hormuz   pw=  41 resolved=40-49     MATCH
2026-04-13 Strait of Hormuz   pw=  52 resolved=80+       MISMATCH
2026-04-20 Strait of Hormuz   pw=  28 resolved=25-49     MATCH
2026-04-27 Strait of Hormuz   pw=  86 resolved=25-49     MISMATCH
2026-05-04 Strait of Hormuz   pw=  10 resolved=<25       MATCH
2026-05-11 Strait of Hormuz   pw=  38 resolved=40-59     MISMATCH
2026-05-18 Strait of Hormuz   pw=  34 resolved=40-59     MISMATCH
2026-05-25 Strait of Hormuz   pw=  21 resolved=25-49     MISMATCH
2026-06-01 Strait of Hormuz   pw=  31 resolved=25-49     MATCH
...
2026-10-05 Strait of Hormuz   pw=  29 resolved=25-29     MATCH    vol= 64717.6
2026-10-05 Bab el-Mandeb Stra pw= 198 resolved=190-209   MATCH    vol= 13097.8

MATCH 34 MISMATCH 7 NODATA/NORES 5 of 46
Hormuz: last day with data 2026-10-11 | complete weeks 405
last 30 complete Hormuz weekly totals:
2026-03-16:10, 2026-03-23:25, 2026-03-30:37, 2026-04-06:41, 2026-04-13:52, 2026-04-20:28,
2026-04-27:86, 2026-05-04:10, 2026-05-11:38, 2026-05-18:34, 2026-05-25:21, 2026-06-01:31,
2026-06-08:17, 2026-06-15:85, 2026-06-22:213, 2026-06-29:162, 2026-07-06:98, 2026-07-13:44,
2026-07-20:25, 2026-07-27:37, 2026-08-03:39, 2026-08-10:31, 2026-08-17:35, 2026-08-24:30,
2026-08-31:22, 2026-09-07:37, 2026-09-14:22, 2026-09-21:22, 2026-09-28:19, 2026-10-05:29
mean 46.00 sd 44.17 min 10 max 213
|week-over-week change| n=29 median=13 p90=68 max=128
```

（说明这个 `46`：脚本枚举了 46 个 slug（47 个里那个日期解析失败的 `mar-10-16` 在 `continue` 前未入表），其中包含 4 个 open event。逐 slug 复核过的真实分解（另一次统计输出：`total 47 closed 43 {'hormuz': {'tot': 33, 'closed': 31}, 'bab': {'tot': 14, 'closed': 12}}`）：**已关闭 43 = 34 MATCH + 7 MISMATCH + 2 无法比对**（`mar-10-16` 无可解析日期窗口；2026-03-17 那事件的窗口起点是周二，不落在 Mon–Sun 分箱）；4 个 open（`week of october 12` 两个、`week of october 19` 两个）均为 `pw=None` 且无结算。另一次按 `closed==True` 过滤的统计输出为 `closed weekly events: 42, with pw_total: 41, resolved: 42 → MATCH 34 MISMATCH 7 no-data/nr 1`——它的 42 是 43 减去被跳过的 `mar-10-16`。）

**MISMATCH 周清单（脚本输出，全部在 2026-03 至 2026-05）**：`['2026-05-11','2026-04-27','2026-05-25','2026-03-30','2026-04-13','2026-05-18','2026-03-23']`
**成交额（Gamma `volume` 自报，未用成交明细复现）**：Bab 已关闭合计 `265080`、Hormuz 已关闭合计 `6332007`。

### 基准率与校准脚本（`pw_calib.py` 关键部分）

```python
# 逐档取 CLOB 价格历史；只有价格取全的事件才进入 Brier 比较
def ev_data(e):
    ev = get("https://gamma-api.polymarket.com/events?slug=" + e["slug"])[0]
    out = []
    for m in ev["markets"]:
        toks = json.loads(m["clobTokenIds"])
        h = get("https://clob.polymarket.com/prices-history?market=%s&interval=max&fidelity=60" % toks[0]).get("history", [])
        end = datetime.datetime.fromisoformat(ev["endDate"].replace("Z", "+00:00")).timestamp()
        first = h[0]["p"] if h else None
        near = None
        for p in h:
            if p["t"] <= end - 86400: near = p["p"]        # endDate 前约 24h
        out.append(dict(b=m["groupItemTitle"], first=first, near=near,
                        resolved=1.0 if m.get("outcomePrices") == '["1", "0"]' else 0.0))
    return out

# 基准率：该事件周之前 12 个完整周，映射到当期档位，Laplace (k+1)/(12+n)
hist = sorted([(k[1], v) for k, v in wk.items() if k[0] == e["port"] and k[1] < d0])[-12:]
base = [sum(1 for _, v in hist if iv(m["b"])[0] <= v <= iv(m["b"])[1]) / len(hist) for m in d]
base_s = [(b * len(hist) + 1) / (len(hist) + n) for b in base]
brier = lambda p: sum((p[i] - y[i]) ** 2 for i in range(n))
```

**输出（原样）**：

```
events used: 25
SKIP missing mid price: how-many-ships-transit-the-strait-of-hormuz-week-of-july-20-   (×19 条同类 SKIP)
2026-09-28 Hormuz ['<20','20-24','25-29','30-34','35-39','40+']  mkt_first=0.833 mkt_near24h=1.289 base=1.086  win@<20 | p_mkt_first=0.17 base=0.06
2026-10-05 Hormuz ['<20','20-24','25-29','30-34','35-39','40+']  mkt_first=0.783 mkt_near24h=0.667 base=0.969  win@25-29 | p_mkt_first=0.20 base=0.11
2026-09-21 Hormuz ['<20','20-24','25-29','30-34','35-39','40+']  mkt_first=0.614 mkt_near24h=0.457 base=0.864  win@20-24 | p_mkt_first=0.28 base=0.17
2026-09-28 Bab    ['<170','170-189','190-209','210-229','230+']  mkt_first=0.800 mkt_near24h=0.669 base=0.554  win@190-209 | p_mkt_first=0.20 base=0.35
2026-10-05 Bab    ['<170','170-189','190-209','210-229','230+']  mkt_first=0.948 mkt_near24h=0.459 base=0.464  win@190-209 | p_mkt_first=0.13 base=0.41
2026-09-21 Bab    ['<170','170-189','190-209','210-229','230+']  mkt_first=0.798 mkt_near24h=1.244 base=0.651  win@190-209 | p_mkt_first=0.20 base=0.29

market price at first print        mean Brier 0.7962  (n=6 events)
market price ~24h before end       mean Brier 0.7975  (n=6 events)
PortWatch 12-week base rate        mean Brier 0.7646  (n=6 events)
```

`pw_weekly.py`（Bab 12 周序列的直接来源）用的就是同一段 PortWatch 分页 + `Mon-Sun` 聚周代码，输出：

```
rows fetched: 5682
== Bab el-Mandeb Strait | daily rows 2841 | coverage 2019-01-01 .. 2026-10-11 | complete Mon-Sun weeks 405
   <170        0  0.0000
   170-189     7  0.0173
   190-209    18  0.0444
   210-229    43  0.1062
   230+      337  0.8321
   min/median/max weekly: 173 381 578
== Strait of Hormuz | daily rows 2841 | coverage 2019-01-01 .. 2026-10-11 | complete Mon-Sun weeks 405
   <170       31  0.0765
   170-189     0  0.0000
   190-209     0  0.0000
   210-229     1  0.0025
   230+      373  0.9210
   min/median/max weekly: 10 569 781
```

（这两张是全 405 周的**无条件**分布，用来说明"战前/战中两个状态不能混用"，本条实际只用近 12 周。）

### 去重检查（我实际执行过的命令与结果）

- `grep -ril "portwatch|chokepoint|ships transit|hormuz|bab el-mandeb|ukmto" known/ bots/ reviews/` → **无输出**（仓库内无同源条目）。
- `grep -rl "pm_category: geopolitics" bots/*/entries/` → **无输出**（0 条地缘条目）。
- `grep -ril "基准率|base rate|base-rate" bots/*/entries/ known/` → `quant-004`、`quant-005`、`quant-009`、`quant-011`、`quant-012`；最接近的是 **quant-012（地震周计数基准率）**，已在门槛自查第 4 条写明同族关系与差别（费率 0 vs 0.05、结算源有事后修订与发布滞后导致周内无部分信息、档宽 20 对 sd 13.51）。
- `grep -n "C0[0-9]" bots/dot/CLAIMS.md` → C04「政治官宣与未结算窗口」、C10「截止日型市场生存/时间衰减」、C11「新闻后过度反应及修正」（均为 dot 的 CLAIMS 行，非条目）；`known/KNOWN.md` 中 `grep -n "C04|C10|C11"` **无输出**。本条与三者机制不同（无公告、无截止日时间价值、不预测新闻后修正方向）。

---

## glm-5.3 事实核查报告

# Fact-check report: B15.md (海峡周通行数 PortWatch 基准率)

**Re-fetched 15 URLs + re-ran `pw_verify.py` (saved to /tmp/b15check). Core claims reproduce almost exactly.**

## VERIFIED (exact match)
- Bab oct-5: closed, `volume=13097.774817`, resolved `190-209`, all 6 rule quotes verbatim in `description` ✓
- Bab oct-19: `volume=13595.368699`, dates, `negRisk`, all 5 bid/asks incl. `<170 0.127/0.16`; market-level `feesEnabled=False`/`feeSchedule=None`; `rewardsDailyRate=39` (on 170-189 leg), `rewardsMaxSpread=8.5` ✓
- Hormuz oct-19: all 6 bid/asks, mid-sum 1.1615, ask-sum 1.408, bid-sum 0.915, `volume=5539.661748` ✓
- Script re-run: 5,682 rows, 2019-01-01..2026-10-11, 405 weeks/strait, **MATCH 34 / MISMATCH 7 / 2 uncompa­rable**, same 7 mismatch weeks, 25/25 since 2026-07-13, Oct-5 Bab 198→190-209 / Hormuz 29→25-29 ✓
- Bab last-12 series `198,215,178,206,…` mean 193.67 sd 13.51; Hormuz last-30 exact, mean 46.00 sd 44.17, WoW median 13/p90 68; volume sums 265,080/6,332,007; 47/43/31/12 event counts; geopolitics 100-per-page, guinea-bissau, UKMTO=1, CLOB history first points `0.255/0.405`, PortWatch page 216,598 bytes ✓

## Problems
1. **MISMATCH `rewardsMinSize=20`** → API says **50** on every leg. Fix number (subsidy detail only).
2. **MISMATCH "≥30 的占 15/30"** (Hormuz last-30) → actual **18/30**. Fix; direction actually strengthens their no-trade argument.
3. **MISMATCH "月度均值模板 4 个"** → union of `avgpt-of-ships-*` slugs across both searches = **6** distinct events. Recount or state counting rule.
4. **`id: quant-XXX`** placeholder violates GUIDE §7 ("和文件名一致"); set real id (quant-015).
5. **Duplication (main issue)**: same mechanism family as **quant-012** (免费计数源经验分布 vs 周度计数阶梯， maker 卖 NO) — per GUIDE §6 this is a 变体 → `kind: supplement`/`improves: quant-012`, not `kind: new`. Entry honestly discloses and defers to reviewer, but front-matter still says `new`. Either reclassify or explicitly claim distinct key variable (0 fee, revision-prone source, no intraweek observability) — currently ambiguous.
6. **Time-varying (acceptable, timestamped)**: Bab liquidity 53,711→62,804; 170-189 0.33/0.36→0.31/0.38; 230+ ask 0.104→0.122; Bab mid-sum 1.010→1.019.
7. `clobRewards` framed as event-level; actually per-leg (6/39/42/5/8).

## Compliance
来源自报 labels ✓; fee formula (rate 0 → 0) ✓; no fake backtests (explicitly none, Brier labelled n=6 "不构成结论") ✓; no keys/paid data ✓; honest 门槛自查 ✓; CLAIMS.md B15 claimed 进行中 ✓; KNOWN.md has no portwatch/geopolitics overlap ✓. `status: 草稿` fine for draft.

**Gates: 1✓ 2✓(conditional) 3✓ 4✗(quant-012 variant) 5✓(thin) 6✗/uncertain (price history only 6/25 → may not reach 30).**

VERDICT: FIX — data work is genuine and reproducible, but three peripheral numbers mismatch, the id is a placeholder, and the quant-012 duplication must be resolved (supplement vs new) before scoring.
GATES_PASSING: 5/7
