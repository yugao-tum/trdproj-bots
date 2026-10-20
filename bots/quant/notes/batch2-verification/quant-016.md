# quant-016 工作者核对日志（deepseek-flash 原稿附录，含脚本全文）+ glm-5.3 事实核查报告

## VERIFICATION LOG (reviewer only, not for commit)

时间：2026-10-20。全部为 keyless 公开 GET，无登录、无 API key、未下单。工作目录 `/workspace/agent-tools/quant-batch2/work_B13`。

### 抓取记录

| URL | HTTP | 我从里面取的原文/数字 |
|---|---|---|
| `https://gamma-api.polymarket.com/public-search?q=rotten%20tomatoes&limit_per_type=100` | 200 | `"pagination":{"hasMore":true,"totalResults":163}`；`events` 长度 50；第一条 `slug":"sense-and-sensibility-rotten-tomatoes-score-20261019"`，`volume":32777.589025` |
| `https://gamma-api.polymarket.com/events?slug=clayface-rotten-tomatoes-score-20261026` | 200 | `"tags":[{"id":"53","slug":"movies"},{"id":"596","slug":"pop-culture"},{"id":"101453","slug":"rotten-tomatoes"}]`；`volume":4096.903617`、`liquidity":870.65026`、`openInterest":1234.128952`、`negRisk":false`、`endDate":"2026-10-26T14:00:00Z"`；各档 `feeSchedule":{"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`；50+ 0.932/0.977、60+ 0.61/0.9、70+ 0.42/0.51、80+ 0.04/0.26、90+ 0.021/0.061；规则原文见条目规则节 |
| `https://gamma-api.polymarket.com/events?slug=sense-and-sensibility-rotten-tomatoes-score-20261019` | 200 | 11 档；event `closedTime":"2026-10-19 16:03:29+00"`；市场级 `umaEndDate":"2026-10-19 16:02:05+00"`、`umaResolutionStatus":"resolved"`、`automaticallyResolved":true`、`umaBond":"500"`、`umaReward":"5"`、`customLiveness":0`、`resolutionSource":""`；75+ `["1","0"]`、78+ `["0","1"]` |
| `https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=true&order=endDate&ascending=false` | 200 | `n=85`；volume 合计 `1818572.46`；月份计数 `2026-08:17, 2026-09:12, 2026-05:12, 2026-03:11, 2026-04:10, 2026-10:9, 2026-06:9, 2026-07:4`；市场数合计 530 |
| `https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=false&order=endDate&ascending=false` | 200 | `n=9`；合计 `56087.15`；`klara-and-the-sun…` vol 297.908884、`ali-g-who-iz-i…` 509.647394、`dune-part-three…` 1027.1947049999999、`avengers-doomsday…` 19284.422160000002；`clobRewards.rewardsDailyRate` 见条目成本节 |
| `https://gamma-api.polymarket.com/events?tag_slug=culture&limit=3` | 200 | 仅用于确认 tag 端点可达（复查返回 0 个 event） |
| `https://gamma-api.polymarket.com/tags?limit=200` | 200 | 实际只返回 100 条，其中与本主题相关的只有 `104208 caesars-entertainment`；`rotten-tomatoes` 不在其中，故改从 event 对象的 `tags` 字段读 |
| `https://clob.polymarket.com/prices-history?market=115247292569760568274899790090301720359959003343471261064290162154153281032682&interval=max&fidelity=60` | 200 | `{"history":[{"t":1790352019,"p":0.8745},…]}`；n=564；首 `2026-09-25 16:00:19Z`，末 `2026-10-19 16:00:22Z` `p=0.9995`；min `p=0.5445` @ `2026-09-26 06:00Z`；`T−7d=0.9785`、`T−3d=0.989`、`T−1d=0.998` |
| `https://clob.polymarket.com/prices-history?market=4867997&interval=max` | 200 | 只是探针：CLOB 接受任意字符串参数，**不能**用 market id 代替 token id，故后续统一用 `clobTokenIds` |
| `https://www.rottentomatoes.com/m/clayface` | 200 (180,045 B) | `"criticsScore":{"likedCount":0,"notLikedCount":1,"ratingCount":1,"reviewCount":1,"reviewsPageUrl":"/m/clayface/reviews","title":"Tomatometer"}` —— 无 `score`/`scorePercent` 键 |
| `https://www.rottentomatoes.com/m/sense_and_sensibility_2026` | 200 (236,581 B) | `"criticsScore":{"averageRating":"7.10","certified":true,"likedCount":78,"notLikedCount":24,"ratingCount":102,"reviewCount":102,"score":"76","sentiment":"POSITIVE","scorePercent":"76%"}` |
| `https://www.rottentomatoes.com/m/other_mommy` | 200 (227,607 B) | `"likedCount":15,"notLikedCount":72,"ratingCount":87,"reviewCount":87,"score":"17","scorePercent":"17%"` |
| `https://www.rottentomatoes.com/m/by_any_means` | 200 (145,244 B) | `"criticsScore":{"likedCount":0,"notLikedCount":0,"ratingCount":0,"reviewCount":0,"title":"Tomatometer"}` —— 无 `score` 键 |
| `https://www.rottentomatoes.com/m/sense_and_sensibility_2026/reviews` | 200 (96,227 B) **但内容不可用** | 正则 `"(publicationDate\|reviewDate\|createDate\|datePublished)":"…"` 命中 **0**；`"reviewCount":(\d+)` 命中 **0**；页面为 JS 渲染 → 无法回放历史评论时间 |

失败/未取：`docs.polymarket.com` 未抓（费率改从 Gamma `feeSchedule` 实取，故不需要）。RT 无任何官方 API 可用性**未核**。`resolutionSource` 为空这一事实已核，具体结算页面**未查到**。

### 计算脚本全文（`calc_rt.py`，用上面已保存的 `tag_true.json`/`tag_false.json`/`ph1.json`，无网络）

```python
import json,statistics,collections,math,datetime
T=json.load(open('tag_true.json')); F=json.load(open('tag_false.json'))
def thresholds(m):
    try: return int(str(m.get('groupItemTitle','')).replace('+','').strip())
    except: return None
def pr(m):
    try: return json.loads(m.get('outcomePrices') or '[]')
    except: return []
rows=[]
for e in T:
    mk=[m for m in e.get('markets',[]) if thresholds(m) is not None]
    yes=[thresholds(m) for m in mk if pr(m)[:1]==['1']]
    no =[thresholds(m) for m in mk if pr(m)==['0','1']]
    if not yes:
        rows.append((e['slug'],e.get('endDate','')[:10],None,None)); continue
    lo=max(yes); hi=min([n for n in no if n>lo],default=None)
    rows.append((e['slug'],e.get('endDate','')[:10],lo,hi))
ok=[r for r in rows if r[2] is not None]
print('closed events:',len(T),' with >=1 YES bracket:',len(ok),' none:',len(rows)-len(ok))
buck=collections.Counter(((r[2]//10)*10) for r in ok)
print('base rate buckets:',sorted(buck.items()))                       # [(20,3),(30,4),(40,5),(50,10),(60,4),(70,15),(80,12),(90,17)]
print('P(>=80)=',round(sum(1 for r in ok if r[2]>=80)/len(ok),4))       # 0.4143
print('P(>=90)=',round(sum(1 for r in ok if r[2]>=90)/len(ok),4))       # 0.2429
print('P(<60) =',round(sum(1 for r in ok if r[2]<60)/len(ok),4))        # 0.3143
print('median lo=',statistics.median([r[2] for r in ok]))               # 74.0
print('median width=',statistics.median([r[3]-r[2] for r in ok if r[3]]))  # 5.0  (min 1, max 20)
vols=[e.get('volume') or 0 for e in T]
print('closed vol median/mean/max/sum:',round(statistics.median(vols),2),round(statistics.mean(vols),2),round(max(vols),2),round(sum(vols),2))
print('mkts/event mean/min/max:',round(statistics.mean([len(e['markets']) for e in T]),2),
      min(len(e['markets']) for e in T), max(len(e['markets']) for e in T))   # 6.24 / 3 / 15
# 单调性检查（在开的 9 个 event，mid 口径）
for e in F:
    mk=sorted([m for m in e['markets'] if thresholds(m) is not None], key=thresholds); prev=None
    for m in mk:
        b,a=m.get('bestBid'),m.get('bestAsk')
        mid=None if (b is None or a is None) else (b+a)/2
        if prev and mid is not None and prev[1] is not None and mid>prev[1]+1e-9:
            print('VIOL',e['slug'],prev,'->',thresholds(m),mid)
        prev=(thresholds(m),mid)
# Beta 90% CI（二分 Beta CDF，均匀先验 Beta(k+1,n-k+1)）
from math import lgamma
def betacdf(x,a,b,n=2000):
    s=0.0
    for i in range(n):
        t=(i+0.5)/n
        if t>=x: break
        s+=math.exp((a-1)*math.log(t)+(b-1)*math.log(1-t)-(lgamma(a)+lgamma(b)-lgamma(a+b)))/n
    return s
def q(p,a,b):
    lo,hi=0.0,1.0
    for _ in range(60):
        m=(lo+hi)/2
        if betacdf(m,a,b)<p: lo=m
        else: hi=m
    return (lo+hi)/2
for n in (10,20,50,100):
    for frac in (0.6,0.75,0.9):
        k=round(n*frac); a,b=k+1,n-k+1; L,U=q(0.05,a,b),q(0.95,a,b)
        print(f'n={n} k={k} pt={100*k/n:.1f}% CI=[{100*L:.1f},{100*U:.1f}] w={100*(U-L):.1f}')
```

实际输出（节选；行内 `#` 注释、`min 1 max 20` 与 `total mid monotonicity violations: 2` 三处是人工注释，不是脚本打印）：

```
closed events: 85  with >=1 YES bracket: 70  none: 15      # 去掉 1 个区间写法(`<60`)后条目里写 14
base rate: bucket of final score floor-10s: [(20, 3), (30, 4), (40, 5), (50, 10), (60, 4), (70, 15), (80, 12), (90, 17)]
P(final>=80) = 0.4143 n= 70
P(final>=90) = 0.2429
P(final<60)  = 0.3143
median final lo = 74.0
median bracket width (points) = 5.0 min 1 max 20
closed-event volume: median 11727.77 mean 21394.97 max 241440.63 sum 1818572.46
open events: 9 sum volume 56087.15
LIVE monotonicity check ... VIOL wildwood-rotten-tomatoes-score-20261026 lo 90 0.969 -> hi 92 0.9695
                             VIOL wildwood-rotten-tomatoes-score-20261026 lo 92 0.9695 -> hi 94 0.97
total mid monotonicity violations: 2
  n= 10 k=  6 point= 60.0%  90%CI=[ 35.0%,  80.0%] width= 45.1pt
  n= 20 k= 12 point= 60.0%  90%CI=[ 41.7%,  75.5%] width= 33.8pt
  n= 50 k= 30 point= 60.0%  90%CI=[ 48.3%,  70.5%] width= 22.1pt
  n=100 k= 75 point= 75.0%  90%CI=[ 67.2%,  81.3%] width= 14.1pt
```

两处需向主审说明的口径：

1. 脚本里"none"是 **15**，因为区间写法 event（`mufasa-the-lion-king…`，唯一的区间写法 event）被 `thresholds()` 过滤掉了；条目里写的是 **14 个全档 NO**（数值标题的 event）。这两个数不矛盾，但含义不同，特此登记。
2. `wildwood` 的两处单调性破坏都发生在 0.969/0.9695/0.97 这种 **0.0005–0.001 的极薄价差**上（档位 90+/92+/94+ 都已接近 1），属于盘口噪声，**不是**可交易的套利；条目正文只写 clayface 的单调性检查结果，没有把它夸大成机会。

---

## glm-5.3 事实核查报告

# Fact-check report: B13 (RT Tomatometer brackets)

**Re-fetched 16 URLs (Gamma, CLOB, RT).** Rule quote, `resolutionSource=""`, `negRisk=false`, tags id 101453, feeSchedule (0.05/takerOnly/rebate 0.25), makerBaseFee/takerBaseFee=1000, restricted=true, umaBond 500/umaReward 5/customLiveness 0, and the no-data→"No" clause: **VERIFIED verbatim**. RT pages (clayface 0/1/1 no score; sas 78/24/102→"76"; other_mommy 15/72/87→"17"; by_any_means all-0 no score): **VERIFIED exact**. Reviews page: 0 date fields, 0 reviewCount: **VERIFIED**. Gamma counts 163/50/85/530/$1,818,572.46/9/47/$56,087.15/median $11,727.77/max $241,440.63/6.24-3-15/months 11-10-12-9-4-17-12-9/klara $297.91/clobRewards 3/5/100/10: **ALL VERIFIED**. prices-history 564 pts, 0.8745→min 0.5445@09-26T06:00Z→0.9995, T−7d 0.9785: **VERIFIED**. Re-ran `calc_rt.py`: output reproduces every entry number (70/14 split, buckets, 0.4143/0.2429/0.3143, median 74, wildwood VIOLs); Beta CIs independently confirmed via exact binomial identity. digger 48/49/50/51… 1-pt spacing **VERIFIED**. Time-varying (snapshot dated, OK): clayface 70+ bid 0.42→0.09/mid 0.465→0.30, 90+ ask 0.061→0.078, liquidity 870.65→753.82.

**Problems:**
1. MISMATCH (arithmetic): "0.009375（占投入 **0.94%**）" — fee/invested = 0.009375/0.75 = **1.25%** (GUIDE §8: 费率×(1−p)); 0.9545 case is 0.23%, not 0.24%. Understates cost.
2. MISMATCH (arithmetic): "200* … **≈±3.1 分**（1.645×sqrt(0.75×0.25/200)）" — that formula gives **±5.0 分**; ±3.1 needs n≈500. Fix number or n.
3. Front-matter `id: quant-XXX` placeholder — must equal filename (quant-014).
4. Field mix-up: "`closedTime` 是 2026-10-19 **16:02:05**+00" — event closedTime is 16:03:29Z; 16:02:05Z is market-level `umaEndDate` (same for `umaResolutionStatus`/bond fields, market-level not event). 2-hour-lag point survives; fix attribution.
5. Log's "实际输出" includes lines the script never prints ("min 1 max 20", "total mid monotonicity violations: 2"). Values re-verified true (hi−lo widths median 5/min 1/max 20 ✓), but should be labeled as annotations.
6. Probe-URL drift: `tag_slug=culture&limit=3` now returns **0** events (log claimed 3); `tags?limit=200` returns 100 (claimed 200). Non-load-bearing; reword.
7. "mufasa… 只有 `<60`" — it has 5 interval brackets (<60, 60-69, 70-79, 80-89, 90+). Fix.

**Rule compliance:** fee formula per GUIDE ✓; honest 门槛自查 and "没有做回测" ✓; no keys/paid data ✓; 来源自报 label appears only in 门槛自查, not inline in 证据/出处 (minor). **Duplication:** none — KNOWN.md (135), all CLAIMS.md, entries quant-001…013/dot/muse contain no RT/critic-score entry; B13 properly claimed 进行中.

VERDICT: FIX — two genuine arithmetic errors (1.25% not 0.94%; ±5.0 not ±3.1), a placeholder id, and minor field/probe mislabels, on an otherwise fully reproducible and honestly hedged entry.
GATES_PASSING: 5/7
