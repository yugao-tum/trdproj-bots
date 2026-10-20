# quant-017 工作者核对日志（deepseek-flash 原稿附录，含脚本全文）+ glm-5.3 事实核查报告

## VERIFICATION LOG (reviewer only, not for commit)

访问日期全部为 2026-10-20（UTC）。除特别说明，都是 keyless 公开 GET，无登录、无密钥、未交易。

| # | URL | HTTP | 取到的确切片段/数字 |
|---|---|---|---|
| 1 | `https://gamma-api.polymarket.com/public-search?q=app%20store&limit_per_type=50&events_status=all` | 200 | `"pagination":{"hasMore":true,"totalResults":247}`；`events` 50 条，含 `2-free-app-in-the-us-apple-app-store-on-october-23-10172026` 等 |
| 2 | `https://gamma-api.polymarket.com/events?slug=2-free-app-in-the-us-apple-app-store-on-october-23-10172026` | 200 | `title:"#2 Free App in the US Apple App Store on October 23?"`；`negRisk:true`；`volume:3197.808697`；`liquidity:1672.67816`；`startDate:2026-10-17T21:06:16Z`；`endDate:2026-10-23T23:59:00Z`；`n_markets=12`；规则原文（见上「规则」节逐句引用）|
| 3 | 同上（同一响应，逐臂） | — | Vinted `YES=0.395 bid=0.16 ask=0.63 vol=1607.8`；Muse `0.1555/0.033/0.278/298`；ChatGPT `0.1485/0.139/0.158/955.91`；TikTok Pro `0.0975/0.005/0.19/0`；Claude `0.021/0.004/0.038/70.26`；McDonald's `0.0285/0.008/0.049/42.29`；KICK `0.048/0.011/0.085/223.55`；`Reserved app 2..5` 与 `Other` 均 `["0.5","0.5"] bid=0 ask=1 vol=0`；`feeType=culture_fees`、`feeSchedule={exponent:1,rate:0.05,takerOnly:true,rebateRate:0.25}`；`clobRewards` 日率 54/17/16/8/5，`rewardsMinSize=20`、`rewardsMaxSpread=4.5`、`startDate=2026-10-20`；`umaBond=500`、`umaReward=5`、`customLiveness=0`；`restricted=true` |
| 4 | `https://gamma-api.polymarket.com/events?slug=1-free-app-in-the-us-apple-app-store-on-october-23-10172026` | 200 | `volume=5918.217347`、`liquidity=5058.12548`、12 市场；Muse `0.725/0.71/0.74/3412.38`；Vinted `0.072/0.045/0.099/261.74`；ChatGPT `0.065/0.052/0.078/488.17`；Claude `0.0315/0.003/0.06/1232.01`；KICK `0.01/0.002/0.018/274.86`；Google Gemini `0.005/0.001/0.009/144.63`；TikTok Pro `0.0045/0.001/0.008/104.42`；sum_YES_real=0.913、sum_bestBid=0.814、sum_bestAsk=6.012 |
| 5 | `https://rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json` | 200 | `"country":"us"`、`"updated":"Tue, 20 Oct 2026 04:23:37 +0000"`（首次）与 `"...04:25:44 +0000"`（第二次）；`results` 50 条；顺序 `Capital One Mobile, Vinted: Pre-loved marketplace, Muse from Meta, ChatGPT, TikTok Pro - Events, …` |
| 6 | `https://itunes.apple.com/us/rss/topfreeapplications/limit=25/json` | 200 | 25 条 `entry`；`im:name.label` 前 5 位与 #5 **逐位相同**（脚本输出 `same-position agreement over first 25 apps: 25/25 ; set overlap 25/25`） |
| 7 | `https://apps.apple.com/us/charts/iphone` | 200，1,017,064 B | HTML 内 `Top Free` 出现 60 次；正则抽出的有序名字前 9 个：`Capital One Mobile, Vinted: Pre-loved marketplace, Muse from Meta, ChatGPT, TikTok Pro - Events, PineDrama - Short Dramas, McDonald's, Claude by Anthropic, Google Gemini`（与 #5 前 5 位一致，McDonald's 在 Claude 之前 = JSON 的 rank 7 vs 8）|
| 8 | `https://gamma-api.polymarket.com/events?<30 个 slug>`（批量） | 200 | 返回 `events: 20`；赢家（YES 结算价 > 0.5）逐条：2025-10-17 Sora by OpenAI｜2025-10-24 Dave's Hot Chicken｜2025-11-14 ChatGPT｜2025-11-21 ChatGPT｜2025-11-28 ChatGPT｜2025-11-28 Google Gemini｜**2025-12-05 Other**｜2025-12-05 ChatGPT｜2025-12-12 ChatGPT｜2025-12-19 ChatGPT｜**2025-12-19 Other**｜**2025-12-26 Other**｜2025-12-26 ChatGPT｜2026-01-02 ChatGPT｜2026-01-02 CapCut｜2026-01-09 ChatGPT｜2026-01-09 Gemini｜2026-01-16 ChatGPT｜2026-01-16 Freecash｜2026-01-23 ChatGPT → `winner class counts: {'listed app': 17, 'OTHER/RESERVED': 3}`；市场数 18–26、`nReserved=0`、全部 `hasOther=True`；20 个事件成交额合计 4,286,692 USDC |
| 9 | `https://gamma-api.polymarket.com/events?closed=true&limit=500&end_date_min=2025-10-01&end_date_max=2026-10-20&order=endDate&ascending=false` | 200，1,944,393 B | `n events 100`（`limit=500` 未生效）、`app-store events 0` → 此参数组合不可用，未据此写任何数字 |
| 10 | `https://clob.polymarket.com/prices-history?market=79673759724127771853…&interval=max&fidelity=60`（2025-11-21 `#1` board 的 ChatGPT 臂） | 200 | `n_points 0`、`history []`（该臂 `outcomePrices ["1","0"]`，已结算）→ 无法回测 |
| 11 | `http://web.archive.org/cdx/search/cdx?url=rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json&output=json&limit=8` | 200（body 空） | 无快照 |
| 12 | `http://web.archive.org/cdx/search/cdx?url=rss.marketingtools.apple.com/api/v2/us/apps/top-free/50/apps.json&output=json&limit=8` | 200（body 空） | 无快照 |
| 13 | `http://web.archive.org/cdx/search/cdx?url=apps.apple.com/us/charts/iphone&output=json&limit=8` | 200（body 空） | 无快照 → 历史榜单序列「免费未查到」 |
| 14 | `https://gamma-api.polymarket.com/public-search?q=app%20store&...&page=2` 与 `&offset=50` | 200 | `page=2` 返回不同的一批（与第一页 0/50 重叠），`offset=50` 返回同一批；未据此声称全量 247 个已读，只用了第一页 |

我的算术（全部可复算）：
- 榜单一致率：`25/25`（#6 脚本直接输出）。
- `#1` board：`ΣYES_real = 0.725+0.072+0.065+0.0315+0.01+0.005+0.0045 = 0.913`；`ΣbestBid = 0.814`；`ΣbestAsk(all 12) = 6.012`；`ΣbestAsk_real = 1.012`。
- `#2` board：`ΣYES_real = 0.395+0.1555+0.1485+0.0975+0.048+0.0285+0.021 = 0.894`；`ΣbestBid = 0.360`；`ΣbestAsk(all 12) = 6.428`；`ΣbestAsk_real = 1.428`。
- basket NO 成本 `7 − ΣbestBid`：`#1` = 6.186、`#2` = 6.640；费/份 `Σ 0.05·p·(1−p)`（p=1−YESbid，仅 `#1` 算了）= `0.010295+0.002149+0.002465+0.000150+0.000100+0.000050+0.000050 = 0.015259`；净成本 6.2013 → 平衡 `P(Other)=20.13%`；`#2` 平衡 `P(Other)=64.0%`（未加费，加费只会更高）。基率 `3/20 = 15%`。
- 吃单费/份 = `0.05·p·(1−p)`：p=0.10→0.0045；0.385→0.011841；0.50→0.0125；0.90→0.0045；0.93→0.003255。占名义比 `0.05·(1−p)`：4.50%/3.075%/2.50%/0.50%/0.35%。
- 半价差：Vinted `(0.63−0.16)/2 = 0.235`；Muse `(0.74−0.71)/2 = 0.015`；ChatGPT `(0.078−0.052)/2 = 0.013`。

脚本（保存于 `/workspace/agent-tools/quant-batch2/work_B14/`，输出在 `out.txt`、`out2.txt`）：

`appstore_rank_check.py`：抓两个 Apple feed 比对顺序、抓 `#1`/`#2` 两个 board 的逐臂报价与 sums、算费用表、抓 public-search 统计 board 频率。

`appstore_winners.py`：从 public-search 取 closed `free app` 事件 slug，批量丢给 `events?slug=`，按 `outcomePrices>0.5` 定赢家，统计 `listed app` vs `Other` 基率。

（两个脚本的完整代码见同目录文件；核心逻辑与输出已在上面表格中逐条列出。未做任何交易、未使用密钥。）

### 脚本全文 A: appstore_rank_check.py
```python
#!/usr/bin/env python3
"""B14: Polymarket '#N Free App in the US App Store on <date>' vs Apple free RSS chart.
Keyless public GETs only. Fetched 2026-10-20 (UTC). Prints raw numbers used in the entry."""
import json, urllib.request, collections

UA = {"User-Agent": "Mozilla/5.0 (research script; no login)"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status, r.read().decode()

# ---------- 1. Apple free chart feeds (two endpoints, same chart) ----------
s1, t1 = get("https://rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json")
f1 = json.loads(t1)["feed"]
r1 = [x["name"] for x in f1["results"]]
print("A1 rss.applemarketingtools.com status=%s country=%s updated=%s n=%d" % (s1, f1["country"], f1["updated"], len(r1)))
print("A1 top5:", r1[:5])

s2, t2 = get("https://itunes.apple.com/us/rss/topfreeapplications/limit=25/json")
f2 = json.loads(t2)["feed"]
r2 = [x["im:name"]["label"] for x in f2["entry"]]
print("A2 itunes.apple.com status=%s n=%d top5:" % (s2, len(r2)), r2[:5])
n = min(len(r1), len(r2))
same = sum(1 for i in range(n) if r1[i] == r2[i])
print("A3 same-position agreement over first %d apps: %d/%d ; set overlap %d/%d" %
      (n, same, n, len(set(r1) & set(r2)), n))
for i in range(min(5, n)):
    if r1[i] != r2[i]:
        print("   mismatch pos%d: rss=%s itunes=%s" % (i + 1, r1[i], r2[i]))

CAND = ["Vinted: Pre-loved marketplace", "Muse from Meta", "ChatGPT", "TikTok Pro - Events",
        "Claude by Anthropic", "McDonald's", "KICK - Live Streaming"]
print("A4 candidate ranks in top-free-50 RSS feed:")
for c in CAND:
    print("   %-32s rank=%s" % (c, (r1.index(c) + 1) if c in r1 else "not in top50"))

# ---------- 2. Polymarket boards: #1 and #2 free app, 2026-10-23 ----------
def event(slug):
    s, t = get("https://gamma-api.polymarket.com/events?slug=" + slug)
    return s, json.loads(t)[0]

for slug in ["2-free-app-in-the-us-apple-app-store-on-october-23-10172026",
             "1-free-app-in-the-us-apple-app-store-on-october-23-10172026"]:
    s, e = event(slug)
    print("\nB %s status=%s" % (slug, s))
    print("  title=%r negRisk=%s volume=%s liquidity=%s n_markets=%d" %
          (e["title"], e["negRisk"], e["volume"], e["liquidity"], len(e["markets"])))
    print("  startDate=%s endDate=%s" % (e["startDate"], e["endDate"]))
    yes = []
    for m in e["markets"]:
        p = json.loads(m["outcomePrices"])[0]
        yes.append(float(p))
        print("   %-30s YES=%s bid=%s ask=%s vol=%s feeType=%s rate=%s rewDaily=%s" %
              (m["groupItemTitle"], p, m.get("bestBid"), m.get("bestAsk"),
               round(m.get("volumeNum") or 0, 2), m.get("feeType"),
               m.get("feeSchedule", {}).get("rate"),
               [c["rewardsDailyRate"] for c in (m.get("clobRewards") or [])]))
    real = [m for m in e["markets"] if not m["groupItemTitle"].startswith(("Reserved", "Other"))]
    print("  n_real_candidates=%d sum_YES_all=%.4f sum_YES_real=%.4f sum_bestBid=%.4f sum_bestAsk=%.4f" %
          (len(real), sum(yes), sum(float(json.loads(m["outcomePrices"])[0]) for m in real),
           sum(m.get("bestBid") or 0 for m in e["markets"]),
           sum(m.get("bestAsk") or 0 for m in e["markets"])))
    print("  current RSS #1 %r listed here? %s ; RSS #2 %r listed here? %s" %
          (r1[0], r1[0] in [m["groupItemTitle"] for m in e["markets"]],
           r1[1], r1[1] in [m["groupItemTitle"] for m in e["markets"]]))

# ---------- 3. fee arithmetic (GUIDE formula, rate from Gamma feeSchedule) ----------
rate = 0.05
print("\nC fee per share = shares x rate x p x (1-p); taken rate=%s from Gamma feeSchedule" % rate)
for p in [0.10, 0.385, 0.50, 0.90]:
    print("   p=%.3f -> fee/share=%.5f ; fee/notional=%.4f%% (rate*(1-p))" %
          (p, rate * p * (1 - p), 100 * rate * (1 - p)))

# ---------- 4. board size: public-search for 'app store' ----------
s, t = get("https://gamma-api.polymarket.com/public-search?q=app%20store&limit_per_type=50&events_status=all")
d = json.loads(t)
ev = d["events"]
print("\nD public-search q='app store' status=%s returned=%d pagination=%s" % (s, len(ev), d["pagination"]))
closed = [e for e in ev if e.get("closed")]
m = collections.Counter(e["endDate"][:7] for e in closed)
print("D closed among returned=%d ; by endDate month=%s" % (len(closed), dict(sorted(m.items()))))
print("D closed endDate range %s..%s" % (min(e["endDate"] for e in closed)[:10], max(e["endDate"] for e in closed)[:10]))
print("D closed total volume=%.1f USDC (Gamma self-reported)" % sum(e.get("volume") or 0 for e in closed))
freen = [e for e in ev if "free app" in e["title"].lower()]
print("D titles containing 'free app' among returned=%d (open=%d, closed=%d)" %
      (len(freen), sum(1 for e in freen if not e.get("closed")), sum(1 for e in freen if e.get("closed"))))
```

### 脚本全文 B: appstore_winners.py
```python
#!/usr/bin/env python3
"""B14 part 2: base rate of who wins '#N ... App Store' boards, from Gamma public data.
Keyless GETs. Run 2026-10-20."""
import json, re, collections, urllib.parse, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (research script; no login)"}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
        return r.status, r.read().decode()

s, t = get("https://gamma-api.polymarket.com/public-search?q=app%20store&limit_per_type=50&events_status=all")
ev = json.loads(t)["events"]
closed = [e for e in ev if e.get("closed")]
freen = [e for e in closed if "free app" in e["title"].lower()]
print("closed app-store events in returned page:", len(closed), "| of which 'free app':", len(freen))

q = "&".join("slug=" + urllib.parse.quote(e["slug"]) for e in freen)
s2, t2 = get("https://gamma-api.polymarket.com/events?" + q)
det = json.loads(t2)
print("detail fetch status:", s2, "events:", len(det))

rows, win_counts = [], collections.Counter()
for e in det:
    win = [m["groupItemTitle"] for m in e["markets"]
           if float(json.loads(m["outcomePrices"])[0]) > 0.5 and m.get("closed")]
    titles = [m["groupItemTitle"] for m in e["markets"]]
    nres = sum(1 for x in titles if x.lower().startswith("reserved"))
    has_other = any(x.lower() == "other" for x in titles)
    w = win[0] if len(win) == 1 else "AMBIG:%d" % len(win)
    win_counts["OTHER/RESERVED" if w.lower().startswith(("other", "reserved")) else "listed app"] += 1
    rows.append((e["endDate"][:10], w[:26], len(titles), nres, has_other, round(e.get("volume") or 0)))
print("\nendDate | winner | nMkts | nReserved | hasOther | volume")
for r in rows:
    print(" | ".join(map(str, r)))
print("\nwinner class counts:", dict(win_counts))
print("total volume of these %d events: %.0f USDC" % (len(rows), sum(r[5] for r in rows)))
```

### 原始输出（tee 保存）
```
A1 rss.applemarketingtools.com status=200 country=us updated=Tue, 20 Oct 2026 04:25:44 +0000 n=50
A1 top5: ['Capital One Mobile', 'Vinted: Pre-loved marketplace', 'Muse from Meta', 'ChatGPT', 'TikTok Pro - Events']
A2 itunes.apple.com status=200 n=25 top5: ['Capital One Mobile', 'Vinted: Pre-loved marketplace', 'Muse from Meta', 'ChatGPT', 'TikTok Pro - Events']
A3 same-position agreement over first 25 apps: 25/25 ; set overlap 25/25
A4 candidate ranks in top-free-50 RSS feed:
   Vinted: Pre-loved marketplace    rank=2
   Muse from Meta                   rank=3
   ChatGPT                          rank=4
   TikTok Pro - Events              rank=5
   Claude by Anthropic              rank=8
   McDonald's                       rank=7
   KICK - Live Streaming            rank=not in top50

B 2-free-app-in-the-us-apple-app-store-on-october-23-10172026 status=200
  title='#2 Free App in the US Apple App Store on October 23?' negRisk=True volume=3197.808697 liquidity=1672.67816 n_markets=12
  startDate=2026-10-17T21:06:16Z endDate=2026-10-23T23:59:00Z
   Vinted: Pre-loved marketplace  YES=0.395 bid=0.16 ask=0.63 vol=1607.8 feeType=culture_fees rate=0.05 rewDaily=[54]
   Muse from Meta                 YES=0.1555 bid=0.033 ask=0.278 vol=298 feeType=culture_fees rate=0.05 rewDaily=[17]
   ChatGPT                        YES=0.1485 bid=0.139 ask=0.158 vol=955.91 feeType=culture_fees rate=0.05 rewDaily=[16]
   TikTok Pro - Events            YES=0.0975 bid=0.005 ask=0.19 vol=0 feeType=culture_fees rate=0.05 rewDaily=[8]
   Claude by Anthropic            YES=0.021 bid=0.004 ask=0.038 vol=70.26 feeType=culture_fees rate=0.05 rewDaily=[]
   McDonald's                     YES=0.0285 bid=0.008 ask=0.049 vol=42.29 feeType=culture_fees rate=0.05 rewDaily=[]
   KICK - Live Streaming          YES=0.048 bid=0.011 ask=0.085 vol=223.55 feeType=culture_fees rate=0.05 rewDaily=[5]
   Reserved app 2                 YES=0.5 bid=0 ask=1 vol=0 feeType=culture_fees rate=0.05 rewDaily=[]
   Reserved app 3                 YES=0.5 bid=0 ask=1 vol=0 feeType=culture_fees rate=0.05 rewDaily=[]
   Reserved app 4                 YES=0.5 bid=0 ask=1 vol=0 feeType=culture_fees rate=0.05 rewDaily=[]
   Reserved app 5                 YES=0.5 bid=0 ask=1 vol=0 feeType=culture_fees rate=0.05 rewDaily=[]
   Other                          YES=0.5 bid=0 ask=1 vol=0 feeType=culture_fees rate=0.05 rewDaily=[]
  n_real_candidates=7 sum_YES_all=3.3940 sum_YES_real=0.8940 sum_bestBid=0.3600 sum_bestAsk=6.4280
  current RSS #1 'Capital One Mobile' listed here? False ; RSS #2 'Vinted: Pre-loved marketplace' listed here? True

B 1-free-app-in-the-us-apple-app-store-on-october-23-10172026 status=200
  title='#1 Free App in the US Apple App Store on October 23?' negRisk=True volume=5918.217347 liquidity=5058.12548 n_markets=12
  startDate=2026-10-17T21:06:58Z endDate=2026-10-23T23:59:00Z
   Muse from Meta                 YES=0.725 bid=0.71 ask=0.74 vol=3412.38 feeType=culture_fees rate=0.05 rewDaily=[92]
   Vinted: Pre-loved marketplace  YES=0.072 bid=0.045 ask=0.099 vol=261.74 feeType=culture_fees rate=0.05 rewDaily=[4]
   ChatGPT                        YES=0.065 bid=0.052 ask=0.078 vol=488.17 feeType=culture_fees rate=0.05 rewDaily=[4]
   TikTok Pro - Events            YES=0.0045 bid=0.001 ask=0.008 vol=104.42 feeType=culture_fees rate=0.05 rewDaily=[]
   Claude by Anthropic            YES=0.0315 bid=0.003 ask=0.06 vol=1232.01 feeType=culture_fees rate=0.05 rewDaily=[]
   Google Gemini                  YES=0.005 bid=0.001 ask=0.009 vol=144.63 feeType=culture_fees rate=0.05 rewDaily=[]
   KICK - Live Streaming          YES=0.01 bid=0.002 ask=0.018 vol=274.86 feeType=culture_fees rate=0.05 rewDaily=[]
   Reserved app 2                 YES=0.5 bid=0 ask=1 vol=0 feeType=culture_fees rate=0.05 rewDaily=[]
   Reserved app 3                 YES=0.5 bid=0 ask=1 vol=0 feeType=culture_fees rate=0.05 rewDaily=[]
   Reserved app 4                 YES=0.5 bid=0 ask=1 vol=0 feeType=culture_fees rate=0.05 rewDaily=[]
   Reserved app 5                 YES=0.5 bid=0 ask=1 vol=0 feeType=culture_fees rate=0.05 rewDaily=[]
   Other                          YES=0.5 bid=0 ask=1 vol=0 feeType=culture_fees rate=0.05 rewDaily=[]
  n_real_candidates=7 sum_YES_all=3.4130 sum_YES_real=0.9130 sum_bestBid=0.8140 sum_bestAsk=6.0120
  current RSS #1 'Capital One Mobile' listed here? False ; RSS #2 'Vinted: Pre-loved marketplace' listed here? True

C fee per share = shares x rate x p x (1-p); taken rate=0.05 from Gamma feeSchedule
   p=0.100 -> fee/share=0.00450 ; fee/notional=4.5000% (rate*(1-p))
   p=0.385 -> fee/share=0.01184 ; fee/notional=3.0750% (rate*(1-p))
   p=0.500 -> fee/share=0.01250 ; fee/notional=2.5000% (rate*(1-p))
   p=0.900 -> fee/share=0.00450 ; fee/notional=0.5000% (rate*(1-p))

D public-search q='app store' status=200 returned=50 pagination={'hasMore': True, 'totalResults': 247}
D closed among returned=46 ; by endDate month={'2024-02': 1, '2024-12': 1, '2025-10': 2, '2025-11': 7, '2025-12': 10, '2026-01': 11, '2026-02': 10, '2026-03': 1, '2026-04': 2, '2026-05': 1}
D closed endDate range 2024-02-29..2026-05-08
D closed total volume=8156967.3 USDC (Gamma self-reported)
D titles containing 'free app' among returned=32 (open=2, closed=30)

closed app-store events in returned page: 46 | of which 'free app': 30
detail fetch status: 200 events: 20

endDate | winner | nMkts | nReserved | hasOther | volume
2025-10-17 | Sora by OpenAI | 25 | 0 | True | 62206
2025-10-24 | Dave’s Hot Chicken | 26 | 0 | True | 112968
2025-11-14 | ChatGPT | 19 | 0 | True | 475126
2025-11-21 | ChatGPT | 23 | 0 | True | 948411
2025-11-28 | ChatGPT | 22 | 0 | True | 331499
2025-11-28 | Google Gemini | 22 | 0 | True | 88732
2025-12-05 | Other | 22 | 0 | True | 245458
2025-12-05 | ChatGPT | 22 | 0 | True | 188124
2025-12-12 | ChatGPT | 22 | 0 | True | 113781
2025-12-19 | ChatGPT | 20 | 0 | True | 70498
2025-12-19 | Other | 18 | 0 | True | 79463
2025-12-26 | ChatGPT | 20 | 0 | True | 170223
2025-12-26 | Other | 20 | 0 | True | 109587
2026-01-02 | ChatGPT | 20 | 0 | True | 130757
2026-01-02 | CapCut: Photo & Video Edit | 20 | 0 | True | 97763
2026-01-09 | ChatGPT | 20 | 0 | True | 341330
2026-01-09 | Google Gemini | 20 | 0 | True | 110428
2026-01-16 | ChatGPT | 20 | 0 | True | 280957
2026-01-16 | Freecash - Get Paid Real M | 20 | 0 | True | 119932
2026-01-23 | ChatGPT | 20 | 0 | True | 209449

winner class counts: {'listed app': 17, 'OTHER/RESERVED': 3}
total volume of these 20 events: 4286692 USDC
```

---

## glm-5.3 事实核查报告

# Fact-check report — B14.md (App Store chart markets)

## Re-fetch results (18 external fetches + both scripts re-run)

**Verified exactly**: Apple RSS top-9 sequence (Capital One → Vinted → Muse → ChatGPT → TikTok Pro → PineDrama → McDonald's → Claude → Gemini); itunes RSS 25/25 positional agreement; charts page **1,017,064 bytes**, "Top Free"×60; candidate ranks 2/3/4/5/7/8/KICK>50; both boards' titles, `negRisk=true`, volumes **5918.217347 / 3197.808697**, 12 markets = 7 real + 4 `Reserved` + `Other` (all placeholders `["0.5","0.5"]` bid 0/ask 1/vol 0); `culture_fees` rate **0.05**, takerOnly, rebateRate 0.25; `rewardsMinSize=20`/`rewardsMaxSpread=4.5` (market-level fields); clobRewards 54/17/16/8/5; `umaBond=500`,`umaReward=5`,`customLiveness=0`,`restricted=true`; start/endDates; all rule quotes verbatim ("ranked #2...as of 12:00 PM ET", 48h/last-published clauses); public-search 247/50/46/month-histogram/**8,156,967.3**; batch fetch 20 events, winners **17 listed / 3 Other** (12-05, 12-19, 12-26), nMkts 18–26, nReserved 0, vol 4,286,692; CLOB `{"history":[]}` (token prefix matches); 3× CDX empty; `limit=500`→100 events/0 app-store. Scripts A & B re-run: outputs match the log line-for-line (only live prices drifted). Basket-NO math (6.186/0.0153/20.1%/64% vs 15%), fee table, half-spreads all recompute correctly.

**Time-varying (worker gave timestamps — acceptable)**: #2 Vinted ask 0.63↔0.58; #1 Vinted YES 0.072→~0.052; liquidity 1672.68→1828 / 5058→5073; liquidityNum 123–546→151–452; ΣbestBid 0.814→0.789; ΣYES 0.913→0.893. Basket-NO negative-EV conclusion unchanged (breakeven now ~21% > 15%).

## Problems

1. **MISMATCH — ask-sum mislabeled**: "七个真候选 YES 之和 **0.913**，买价之和 **0.814**，卖价之和 **6.012**（我算的）" — 6.012 sums **all 12 arms** (5 placeholders at ask=1); the 7 real candidates' ask sum is **1.012** (same issue: #2 "6.428" → real 1.428). Script computes over all markets; entry attributes it to 7 candidates. Fix: relabel or correct the number.
2. **NOT REPRODUCED (minor)**: Log #14 "两种翻页参数都返回同一批 50 个事件" — now `page=2` returns a different batch (0/50 overlap); only `offset=50` duplicates. Non-load-bearing (entry only used page 1).
3. **Front-matter**: `id: quant-XXX` placeholder — must be `quant-014` at commit (GUIDE §7).
4. **Incomplete self-dedup**: 门槛自查 #4 compares only quant-007; **quant-010** (Netflix/Spotify 周榜日更抢跑) is the same "public chart → chart-settled market" family and isn't mentioned. Add it with the real distinction (instantaneous snapshot at settle vs. weekly aggregate nowcast).
5. Trivial: entry "p=0.385 → 3.08%" vs script 3.075% (rounding).

Compliance otherwise excellent: 来源自报 labels used (and my re-fetch confirmed the self-reported volumes); fee formula per-market `feeSchedule` as GUIDE §8 instructs; 门槛自查 honest (gate 6 admitted failed, ~2 independent results/2wks, `backtest_count=0`, no backtest claims — CLOB emptiness verified); keyless throughout; no KNOWN.md hits.

VERDICT: FIX — every checkable number and quote verifies against sources, but the "卖价之和 6.012/6.428" scope error, the quant-010 dedup gap, and the id placeholder need correction before commit.
GATES_PASSING: 3/7
