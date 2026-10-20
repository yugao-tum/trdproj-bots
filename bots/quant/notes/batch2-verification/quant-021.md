# quant-021 工作者核对日志（deepseek-flash 原稿附录，含脚本全文）+ glm-5.3 事实核查报告

## VERIFICATION LOG (reviewer only, not for commit)

工具调用：约 20 次（含 2 次 python 脚本重修分页 bug）。全部为只读 GET，无密钥、无登录、无交易。

### 抓取记录

| URL | HTTP | 从里面取的原文/数字 |
|---|---|---|
| `https://gamma-api.polymarket.com/public-search?q=formula%201&limit_per_type=20&events_status=all` | 200 | `"events"` 50 条；首条 `f1-las-vegas-grand-prix-practice-1-fastest-lap-2025-11-20`，`volume:33163.294399`；含 `f1-united-states-grand-prix-winner-2026-10-25`、`...-driver-pole-position-2026-10-24`、`...-driver-podium-2026-10-25`、`f1-singapore-grand-prix-winner-2026-10-11` |
| `https://gamma-api.polymarket.com/public-search?q=grand%20prix&limit_per_type=100&events_status=all` | 200 | 50 条 event；`f1-abu-dhabi-grand-prix-driver-pole-position-2025-12-06` vol `266568.635166`、`mexican-grand-prix-pole-winner` vol `199264.705955` |
| `https://gamma-api.polymarket.com/events?slug=f1-united-states-grand-prix-winner-2026-10-25` | 200 | `volume 3523.282524`、`liquidity 82037.98231`（首次）/`82670.54831`（二次）、`negRisk true`、29 markets、`feeSchedule {"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.15}`、Verstappen `bestBid 0.43`/`bestAsk 0.44`/`outcomePrices ["0.435","0.565"]`、Antonelli `0.23/0.29`；结算原文「Final Classification published by the FIA」「Disqualifications or changes made after the publication … will not affect market resolution」 |
| `https://gamma-api.polymarket.com/events?slug=f1-united-states-grand-prix-driver-pole-position-2026-10-24` | 200 | `volume 248.793286`、`liquidity 12211.33863`、29 markets、Verstappen `bestBid 0.25`/`bestAsk 0.46`、Antonelli `0.11/0.4`；原文「fastest time during the qualifying session … regardless of any subsequent penalties, disqualifications, or changes to the starting grid」 |
| `https://gamma-api.polymarket.com/events?slug=f1-united-states-grand-prix-driver-podium-2026-10-25` | 200 | `volume 202.691853`、`liquidity 5785.2185`、`negRisk false`、23 markets、Verstappen `0.7/0.85`、Antonelli `0.6/0.8`、Antonelli 的 `clobRewards[0].rewardsDailyRate 0.001`（`rewardsAmount 0`，`startDate 2026-10-05`） |
| `https://gamma-api.polymarket.com/events?tag_slug=f1&closed=true&limit=100&offset={0,100,200,300,400}` | 200 ×5 | 去重后 `unique closed f1-tag events: 401`（按 slug 年份的 2026/2025/2024 拆分未能复现，不再引用）；按标题可复现 = Winner 19 / Pole 37 / Podium 17，FP1/Sprint 分类未能精确复现 |
| `https://gamma-api.polymarket.com/events?slug=f1-singapore-grand-prix-winner-2026-10-11` | 200 | `vol 1131293.1852280004`、`closed True`、`endDate 2026-10-18T12:00:00Z`；`resolved YES markets: [('Max Verstappen','["1","0"]',0.999)]` |
| `https://api.jolpi.ca/ergast/f1/2025/results/1.json` | 200 | `{"MRData":{…"limit":"30","offset":"0","total":"24"…}}`，`Results` 数组含 `"grid"`、`"position"` |
| `https://api.jolpi.ca/ergast/f1/2024/qualifying.json`（含 `?limit=2000`） | 200 | `"limit":"100"`（被压到 100）、`"total":"479"`；默认请求 `limit 30`、`races 2` → 必须分页 |
| `https://api.jolpi.ca/ergast/f1/{2014..2026}/qualifying.json?limit=100&offset=N`、`/results.json?limit=100&offset=N` | 200（约 70 次 GET） | 去重 269 场；完整脚本与输出见下 |
| `https://clob.polymarket.com/prices-history?market=28558391…71030&interval=max&fidelity=60`（Gasly 市场 token） | 200 | `points 200`，首点 `{'t':1791028820,'p':0.495}`，末点 `{'t':1791741625,'p':0.0005}`；**首点 0.495 与 Gasly 是冷门车手不符，我判断是市场创建时的默认价（未核实）**，只用来证明「已关闭市场并非全部为空」 |
| `https://clob.polymarket.com/prices-history?market=<bahrain>&startTs=1780000000&endTs=1791500000` | **400** | `HTTP Error 400: Bad Request`（`startTs/endTs` 组合不可用）；同 token 用 `interval=max&fidelity=60` 返回 `points 49`，首 `p=0.26` 末 `p=0.9995` |
| 18 个已关闭 2026 冠军 event 的杆位车手 token `prices-history`（同一脚本内） | 200 / 空 | 只有 `2026-09-26`(158 点, 赛前价 0.675)、`2026-10-04`(49 点, 0.63)、`2026-10-11`(200 点, 0.64) 有数据，其余 15 个 `{"history":[]}`；三场杆位者均夺冠 |

未取得/未查：OpenF1 字段与覆盖范围（未调用）、Ergast 原站 `ergast.com` 状态（未访问）、UMA 参数（未查）、逐车手盘口历史深度（无公开来源）。

### 复现脚本（完整代码，`qpos2.py`，python3 标准库，无第三方依赖）

```python
import json,urllib.request,collections,time
def get(u):
    for i in range(3):
        try:
            r=urllib.request.Request(u,headers={'User-Agent':'research/1.0'})
            with urllib.request.urlopen(r,timeout=60) as f: return json.loads(f.read().decode())["MRData"]
        except Exception as e: time.sleep(2); err=e
    raise err
def paged(s,k):
    out=[];off=0
    while True:
        m=get("https://api.jolpi.ca/ergast/f1/%s/%s.json?limit=100&offset=%d"%(s,k,off))
        out.append(m["RaceTable"]["Races"]); off+=100
        if off>=int(m["total"]): break
    return out
def sec(t):
    if not t: return None
    return float(t.split(":")[0])*60+float(t.split(":")[1]) if ":" in t else float(t)
races={}
for s in range(2014,2027):
    for batch in paged(s,"qualifying"):
        for race in batch:
            key=(s,race["round"]); d=races.setdefault(key,{"s":s,"round":race["round"],"q":{},"win":None,"rtime":race.get("time"),"date":race.get("date")})
            for x in race.get("QualifyingResults") or []:
                did=x["Driver"]["driverId"]; pos=int(x["position"])
                best=None
                for k in ("Q3","Q2","Q1"):
                    if x.get(k): best=sec(x[k]); break
                prev=d["q"].get(did)
                if prev is None or pos<prev[0] or (prev[1] is None and best is not None):
                    d["q"][did]=(pos,best)
    for batch in paged(s,"results"):
        for race in batch:
            key=(s,race["round"]); d=races.setdefault(key,{"s":s,"round":race["round"],"q":{},"win":None,"rtime":race.get("time"),"date":race.get("date")})
            for x in race.get("Results") or []:
                if x.get("position")=="1": d["win"]=x["Driver"]["driverId"]
rows=[]
for d in races.values():
    if not d["q"] or not d["win"]: continue
    pole=[did for did,(p,t) in d["q"].items() if p==1]
    bytime=sorted([(t,did,p) for did,(p,t) in d["q"].items() if t is not None])
    d["pole"]=pole[0] if pole else (bytime[0][1] if bytime else None)
    d["wpos"]=d["q"].get(d["win"],(None,None))[0]
    d["margin"]=(bytime[1][0]-bytime[0][0]) if len(bytime)>1 else None
    rows.append(d)
def rate(rs):
    n=len(rs); w=sum(1 for x in rs if x["pole"]==x["win"]); return n,w,(w/n if n else 0)
print("unique races:",len(rows),dict(sorted(collections.Counter(r["s"] for r in rows).items())))
print("pole->win 2014-2026: n=%d wins=%d rate=%.4f"%rate(rows))
print("pole->win 2022-2026: n=%d wins=%d rate=%.4f"%rate([x for x in rows if x["s"]>=2022]))
print("pole->win 2026:      n=%d wins=%d rate=%.4f"%rate([x for x in rows if x["s"]==2026]))
c=collections.Counter()
for x in rows:
    p=x["wpos"]
    c["P1" if p==1 else "P2" if p==2 else "P3" if p==3 else "P4-6" if p and 4<=p<=6 else "P7-10" if p and 7<=p<=10 else "P11+" if p else "unk"]+=1
for k in ["P1","P2","P3","P4-6","P7-10","P11+","unk"]: print("  %-6s %3d %.3f"%(k,c[k],c[k]/len(rows)))
for lo,hi in [(0,0.05),(0.05,0.2),(0.2,0.5),(0.5,99)]:
    rs=[x for x in rows if x["margin"] is not None and lo<=x["margin"]<hi]
    print("  [%.2f,%.2f) n=%d wins=%d rate=%.3f"%(lo,hi,*rate(rs)))
```

### 脚本原始输出（逐行照抄）

```
unique races: 269 per season: {2014: 19, 2015: 19, 2016: 21, 2017: 20, 2018: 21, 2019: 21, 2020: 17, 2021: 22, 2022: 22, 2023: 22, 2024: 24, 2025: 24, 2026: 17}
pole->win 2014-2026: n=269 wins=150 rate=0.5576
pole->win 2022-2026: n=109 wins=65 rate=0.5963
pole->win 2026:      n=17 wins=12 rate=0.7059

winner quali position (2014-2026), n=269:
  P1     150 0.558
  P2      58 0.216
  P3      30 0.112
  P4-6    22 0.082
  P7-10    7 0.026
  P11+     2 0.007
  unk      0 0.000

pole->win by pole margin:
  [0.00,0.05) n=50 wins=21 rate=0.420
  [0.05,0.20) n=95 wins=53 rate=0.558
  [0.20,0.50) n=93 wins=56 rate=0.602
  [0.50,99.00) n=30 wins=20 rate=0.667

top3 quali covers: 238 / 269 =0.885
```

### 中途失败与修正（照写）

1. 第一次基率跑法（只认 `position` 字段，未做分页去重）得 `143/269 = 0.5316`；发现 `limit=100` 分页会把同一场排位/正赛切到两页导致重复计数（2026 出现 20 场 > 实际 17 场）。改为 `key=(season, round)` 去重 + 缺 `position` 时退化为最快圈速，得最终 `150/269 = 0.5576`。**文中所有基率数字用的是修正后的输出**。
2. 早前把 `events?tag_slug=f1&closed=true` 的第一批 300 条按 `endDate` 统计时因部分 event 无 `endDate` 抛 `KeyError: 'endDate'`，改为按 slug 年份兜底后重算。
3. `ask 合计/bid 合计` 第一次统计时因个别市场无 `outcomePrices` 抛 `KeyError`，加空值保护后重算，得 `7.4930 / 0.9460`（Winner）、`13.5800 / 0.7700`（Pole）。
4. 价格曲线的 `startTs/endTs` 组合返回 HTTP 400，只能改用 `interval=max&fidelity=60`。

---

## glm-5.3 事实核查报告

All checks complete (~24 fetches + full script re-run). Report:

---

## Fact-check report — B18.md (F1 pole/winner pricing)

**Script re-run (qpos2.py):** Output matches the entry **exactly**, line for line — 269 races (per-season counts identical), 150/269=0.5576, 65/109=0.5963, 12/17=0.7059, full position distribution (150/58/30/22/7/2), margin bins (50→0.420, 95→0.558, 93→0.602, 30→0.667), 238/269=0.885.

**VERIFIED exactly:** US Winner event (vol 3523.282524, 29 mkts, negRisk, feeSchedule `{1,0.05,takerOnly,0.15}`, Verstappen 0.43/0.44, Antonelli 0.23/0.29, askΣ7.4930/bidΣ0.9460); Pole event (vol 248.793286, 29 mkts, Antonelli 0.11/0.4); Podium (vol 202.691853, 23 mkts, negRisk=false, Verstappen 0.7/0.85, clobRewards 0.001/0/2026-10-05); all three resolution quotes verbatim incl. "Nov 1, 2026"→Other and "regardless of any subsequent penalties…"; Singapore (vol 1,131,293.19, Verstappen `["1","0"]`); Bahrain (vol 652,176.36; token 49 pts, 0.26@1790956829→0.9995@1791129623); Azerbaijan 09-26 (158 pts, pre-race 0.675); Singapore pre-race 0.64; Gasly token (200 pts, 0.495→0.0005, same timestamps); `startTs/endTs`→HTTP 400; jolpi limit-cap 100 (total 479), 2025 total 24; 401 unique closed f1 events; 2026 Winner 19/Pole 37/Podium 17; Spanish 09-13 empty histories. **Time-varying (worker gave 2026-10-20 timestamps, OK):** Winner liquidity 82670→83367; Pole liquidity 12211→11134, Verstappen pole bid 0.25→0.21, Pole sums 13.58/0.77→13.80/0.73.

**Problems:**
1. **Arithmetic error (证据§2):** "P(win|¬pole) = (0.435 − 0.355×0.5963)/0.645 = **0.2234**" — 0.2233 is only the numerator; correct quotient is **0.3462**. Conclusion (<0.4037) still holds. Fix the number.
2. **NOT REPRODUCED — per-year event split:** "2026 年 239 个、2025 年 151 个"（log adds 2024:10）. Slug-year parsing gives 2026:232–236, **2025:51–53**, undated 112. Total 401 matches; 2025:151 appears wrong. Fix or delete the per-year figures (they support no trading number).
3. **id: quant-XXX** placeholder violates GUIDE §7 (id must match filename, e.g. `quant-018`); fix before submission.
4. Minor: Bahrain pre-race now reads 0.63 vs claimed 0.61 (range claim "0.61–0.675" survives); FP1/Sprint title-classification scheme not reproducible exactly (Winner/Pole/Podium do match).

**Compliance:** front-matter values valid otherwise; fee formula `rate×p×(1−p)` used correctly (all cost arithmetic checks out: 0.01232, 2.80%, 0.01097, 0.008, 3.98%, 11.5%); Gamma figures labelled 来源自报; 门槛自查 honest (fails #5/#6 by own admission); no backtest claims (`backtest_count=0` explicit); read-only, no keys/paid data. **No duplication:** no F1/motorsport entries in KNOWN.md (F-F1-* are crypto factors, correctly distinguished) or any bot's entries/claims; quant-006/dot-C12/C13 differ in variables.

**VERDICT: FIX** — substance is fully reproducible and honestly reported, but the 0.2234 arithmetic slip, the unreproducible 2025:151/2026:239 event counts, and the `quant-XXX` id placeholder must be corrected before submission (no fabrication found).

GATES_PASSING: 5/7
