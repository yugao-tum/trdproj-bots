# quant-017 第2轮准备：加强版核对日志 + 两轮 glm-5.3 事实核查（第二轮指出的两处求和已更正：1.001→0.991，0.892→0.9215）

## VERIFICATION LOG (reviewer only, not for commit)

Session date: 2026-10-20 (UTC). All commands below were run in this session. Read-only: no trading, no keys, no orders. Public GETs only.

### A. URL fetch log (HTTP result + snippet)

| # | URL | HTTP / bytes | Snippet / result |
|---|---|---|---|
| 1 | https://rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json | 200 / 25,783 | `"updated":"Tue, 20 Oct 2026 05:14:43 +0000"`; top5 = Capital One Mobile, Vinted: Pre-loved marketplace, Muse from Meta, ChatGPT, TikTok Pro - Events |
| 2 | https://apps.apple.com/us/charts/iphone | 200 / 1,017,064 | HTML contains names in order: `Capital One Mobile`, `Vinted: Pre-loved marketplace`, `Muse from Meta`, ... |
| 3 | https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fcharts%2Fiphone&output=json&fl=timestamp,statuscode,length&filter=statuscode:200&collapse=digest | 200 / 150,321 | 4,295 rows; first `20220604145458`, last `20251103152602`; years 2022 18, 2023 28, 2024 2,648, 2025 1,601 |
| 4 | https://web.archive.org/web/20250101050435id_/https://apps.apple.com/us/charts/iphone | 200 / 117,034 gzip -> 767,828 decoded | `<script name="schema:top-free" ...>` item 1 = `CapCut - Video Editor`; gzip decompressed with Python `gzip.decompress` |
| 5 | https://web.archive.org/cdx/search/cdx?url=rss.applemarketingtools.com%2Fapi%2Fv2%2Fus%2Fapps%2Ftop-free%2F50%2Fapps.json&output=json&fl=timestamp,statuscode&limit=3 | 200 | `[["timestamp","statuscode"],["20230522143120","200"]]` (only 1 snapshot) |
| 6 | https://web.archive.org/cdx/search/cdx?url=rss.applemarketingtools.com%2Fapi%2Fv2%2Fus%2Fapps%2Ftop-free%2F100%2Fapps.json&output=json&fl=timestamp,statuscode&limit=8 | 200 | `[]` (no snapshots) |
| 7 | https://web.archive.org/cdx/search/cdx?url=itunes.apple.com%2Fus%2Frss%2Ftopfreeapplications%2Flimit%3D50%2Fjson&output=json&fl=timestamp,statuscode&limit=8 | 200 | `[["timestamp","statuscode"],["20180107065423","200"]]` (only 1 snapshot) |
| 8 | https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fcharts%2Fiphone%2Ffree-apps&output=json&fl=timestamp,statuscode&limit=8 | 200 | `[]` (no snapshots) |
| 9 | https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fapp-store%2Fcharts%2Fiphone&output=json&fl=timestamp,statuscode&limit=8 | 200 | `[]` (no snapshots) |
| 10 | https://web.archive.org/cdx/search/cdx?url=rss.applemarketingtools.com*&... (wildcard) | **000 / timeout** | not used; exact-URL queries above used instead |
| 11 | https://web.archive.org/cdx/search/cdx?url=apps.apple.com/us/charts/iphone*&... (wildcard) | **000 / timeout** | not used |
| 12 | https://gamma-api.polymarket.com/public-search?q=app%20store&limit_per_type=50&events_status=all&page=1 | 200 / 3,193,423 | 50 events; `pagination={"hasMore":true,"totalResults":247}` |
| 13 | same URL with `&page=2`, `&page=3`, `&page=4`, `&page=5` | 200 / 3,031,443; 3,071,951; 2,525,941; 1,608,594 | 5 pages deduped by slug -> 247 events |
| 14 | https://gamma-api.polymarket.com/events?slug=2-free-app-in-the-us-apple-app-store-on-october-23-10172026 (via embedded markets in public-search) | 200 | rule text quoted in entry; 12 markets; `feeSchedule rate=0.05`; volume 3,197.81 |
| 15 | https://clob.polymarket.com/prices-history?market=<token>&interval=max&fidelity=60 | 200 (247 requests) | 21 events with >0 points, 226 with 0 points; no curl errors |
| 16 | same CLOB endpoint for all 196 markets of the 16 closed positive events | 200 (196 requests) | 92 markets >0 points, 104 zero |

Note on failed first fetch: the first Wayback batch used 6-digit `HHMMSS` timestamps (362 requests, 222 files). Wayback resolved these to *other* dates, so the date mapping was lost; that batch was discarded and the final run used full 14-digit timestamps (158 requests). This is reported as a tried-and-failed variant, not hidden.

### B. Pre-registration (written before parsing snapshot content)
```markdown
# R017 pre-registration (written before parsing any fetched snapshot content)

Purpose: estimate rank persistence of the Apple App Store US iPhone "Top Free Apps" #1 from
Wayback snapshots of https://apps.apple.com/us/charts/iphone (the settlement-source page named
in the Polymarket rules).

Fixed rules:
- Source: only HTTP 200 archived snapshots of that exact URL, parsed via the JSON-LD block
  `<script name="schema:top-free">`, itemListElement position 1 -> app `name`.
- Sample frame: calendar days (UTC) in 2025 that have at least one snapshot in 04:00-08:00 UTC
  and at least one in 14:00-18:00 UTC. One snapshot per window per day, the one closest to
  06:00 and 16:00 UTC respectively.
- P1 (same-day, 06:00 -> 16:00): numerator = days where #1 at the 16:00-window snapshot equals
  #1 at the 06:00-window snapshot; denominator = days where both snapshots parse.
- P2 (overnight, 06:00 -> next-day 06:00): numerator = consecutive-day pairs d,d+1 where both
  morning snapshots parse and #1 is equal; denominator = such pairs.
- Missing/unparseable snapshots are dropped, not imputed. Report exact N and numerator.
- No variant shopping: P1 and P2 as defined are the only headline numbers. Any extra cut
  (e.g. top-6 overlap) is labelled secondary.
```

### C. Scripts (full)

#### C0. Build the 2025 double-window job list (14-digit timestamps)
```python
import json,datetime,collections
rows=json.load(open('cdx_charts_iphone.json'))[1:]
by=collections.defaultdict(list)
for ts,status,length in rows:
    d=ts[:8]
    if not d.startswith('2025'): continue
    sec=int(ts[8:10])*3600+int(ts[10:12])*60+int(ts[12:14])
    by[d].append((sec,ts))
jobs=[]
for d in sorted(by):
    am=[x for x in by[d] if 4*3600<=x[0]<8*3600]
    pm=[x for x in by[d] if 14*3600<=x[0]<18*3600]
    if am and pm:
        jobs.append((d,'AM',min(am,key=lambda x:abs(x[0]-6*3600))[1]))
        jobs.append((d,'PM',min(pm,key=lambda x:abs(x[0]-16*3600))[1]))
open('jobs2.tsv','w').write(''.join(f'{d}\t{s}\t{ts}\n' for d,s,ts in jobs))
print(len(jobs), len(jobs)//2)
```
Output:
```text
120 60
```
（**更正**：上一稿在这里写 `158 79` 是错的。这段 C0 代码的行为就是预注册口径 04:00–08:00 / 14:00–18:00 → 120 张目标快照 / 60 个双窗口日；`158 79` 是实际喂给 C2 的 `jobs2.tsv`，窗口被放宽到 04:00–09:00 / 14:00–19:00 且每侧取当天最接近 06:00 / 16:00 的快照（所以 2 张落在窗口外：`20250105034909` 03:49、`20250217131244` 13:12），属事后放宽口径。两组口径的复算见 D3b。）

#### C1. CDX list (shell)
```bash
curl -sL -A "Mozilla/5.0" --max-time 60 \
  "https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fcharts%2Fiphone&output=json&fl=timestamp,statuscode,length&filter=statuscode:200&collapse=digest" \
  -o cdx_charts_iphone.json
```

#### C2. Snapshot fetch (14-digit timestamps, with retry)
```bash
#!/bin/bash
ts="$1"
out="snaps2/${ts}.raw"
[ -s "$out" ] && exit 0
curl -sL -A "Mozilla/5.0" --max-time 60 \
  "https://web.archive.org/web/${ts}id_/https://apps.apple.com/us/charts/iphone" \
  -o "$out" -w "%{http_code} ${ts} %{size_download}\n" >> fetch2.log
```
Run: `cat ts2.list | xargs -P 8 -n 1 ./fetch_two.sh`, then retried the HTTP 000 lines with `./re3.sh` (same script, P=3).

#### C3. Parse `schema:top-free` and compute P1/P2
```python
import gzip,re,json,os,collections,datetime
def parse(path):
    b=open(path,'rb').read()
    if not b: return None
    try: s=gzip.decompress(b).decode('utf-8','replace')
    except Exception: s=b.decode('utf-8','replace')
    m=re.search(r'<script name="schema:top-free" type="application/ld\+json">\s*(\{.*?\})\s*</script>',s,re.S)
    if not m: return None
    try: j=json.loads(m.group(1))
    except Exception: return None
    items=[e.get('name') for e in j.get('itemListElement',[])]
    return items
jobs=[l.rstrip('\n').split('\t') for l in open('jobs2.tsv') if l.strip()]
data={}
for d,slot,ts in jobs:
    p=f'snaps2/{ts}.raw'
    if os.path.exists(p):
        it=parse(p)
        if it: data[(d,slot)]=(ts,it)
print("parsed (day,slot):",len(data),"of",len(jobs))
days=sorted(set(d for d,s in data))
both=[d for d in days if (d,'AM') in data and (d,'PM') in data]
print("days with both AM+PM parsed:",len(both))
same=sum(1 for d in both if data[(d,'AM')][1][0]==data[(d,'PM')][1][0])
print(f"P1 same-day 06->16: {same}/{len(both)} = {same/len(both):.4f}" if both else "P1 no data")
# consecutive pairs with AM both
pairs=[]
for d in days:
    d2=(datetime.datetime.strptime(d,'%Y%m%d')+datetime.timedelta(days=1)).strftime('%Y%m%d')
    if (d,'AM') in data and (d2,'AM') in data: pairs.append((d,d2))
same2=sum(1 for d,d2 in pairs if data[(d,'AM')][1][0]==data[(d2,'AM')][1][0])
print(f"P2 overnight 06->next 06: {same2}/{len(pairs)} = {same2/len(pairs):.4f}" if pairs else "P2 no pairs")
# secondary: top6 overlap, and PM->next AM
print("--- details ---")
for d in both:
    a=data[(d,'AM')][1][0]; p=data[(d,'PM')][1][0]
    print(d,"AM",a,"| PM",p,"| same",a==p)
print("--- pairs ---")
for d,d2 in pairs:
    print(d,data[(d,'AM')][1][0],"=>",d2,data[(d2,'AM')][1][0],data[(d,'AM')][1][0]==data[(d2,'AM')][1][0])
```

#### C4. CLOB history check (one token per event)
```bash
#!/bin/bash
IFS=$'\t' read -r eslug status mslug token <<< "$1"
resp=$(curl -sL -A "Mozilla/5.0" --max-time 25 "https://clob.polymarket.com/prices-history?market=${token}&interval=max&fidelity=60")
code=$?
n=$(printf '%s' "$resp" | python3 -c "import sys,json
try:
 j=json.load(sys.stdin); print(len(j.get('history',[])))
except Exception: print(-1)" 2>/dev/null)
echo -e "${eslug}\t${status}\t${mslug}\t${code}\t${n}" >> clob_results.tsv
```

#### C5. CLOB history check (all markets of the 16 closed positive events)
```bash
#!/bin/bash
IFS=$'\t' read -r eslug mslug token <<< "$1"
resp=$(curl -sL -A "Mozilla/5.0" --max-time 20 "https://clob.polymarket.com/prices-history?market=${token}&interval=max&fidelity=60")
n=$(printf '%s' "$resp" | python3 -c "import sys,json
try: print(len(json.load(sys.stdin).get('history',[])))
except Exception: print(-1)" 2>/dev/null)
echo -e "${eslug}\t${mslug}\t${n}" >> clob_closedpos.tsv
```

#### C6. Polymarket event recount + `Other` base rate (exact inline script)
```python
import json,collections
ev=list(json.load(open('pm_events.json')).values())
def kind(e):
    t=e['title'].lower(); return 'free' if 'free app' in t else ('paid' if 'paid app' in t else 'other')
print("unique events",len(ev),"closed",sum(1 for e in ev if e.get('closed')),"open",sum(1 for e in ev if not e.get('closed')))
print("free",sum(kind(e)=='free' for e in ev),"paid",sum(kind(e)=='paid' for e in ev),"other",sum(kind(e)=='other' for e in ev))
free=[e for e in ev if kind(e)=='free' and e.get('closed')]
def winner(e):
    for m in e.get('markets',[]):
        pr=json.loads(m.get('outcomePrices') or '[]'); outs=json.loads(m.get('outcomes') or '[]')
        yes=None
        for o,p in zip(outs,pr):
            if str(o).strip().lower()=='yes': yes=float(p)
        if yes is not None and yes>0.5: return str(m.get('groupItemTitle') or m.get('question')).strip()
    return None
us=[e for e in free if 'in-the-us-apple-app-store' in e['slug']]
res=[winner(e) for e in us]; res=[x for x in res if x]
print("US Apple free closed",len(us),"resolved",len(res),"Other",sum(1 for x in res if x.lower()=='other'),"rate",round(sum(1 for x in res if x.lower()=='other')/len(res),4))
print("all free closed resolved",sum(1 for e in free if winner(e)),"Other",sum(1 for e in free if winner(e) and winner(e).lower()=='other'))
print("free closed endDate range",min(e['endDate'] for e in free),max(e['endDate'] for e in free))
print("free closed market count min/max",min(len(e['markets']) for e in free),max(len(e['markets']) for e in free))
print("free closed volume sum",sum(float(e.get('volume') or 0) for e in free))
print("by month",dict(sorted(collections.Counter(e['endDate'][:7] for e in free).items())))
```

#### C7. Basket-NO and 06:00 entry EV arithmetic
```python
import json
ev=json.load(open('pm_events.json'))
for slug in ['1-free-app-in-the-us-apple-app-store-on-october-23-10172026','2-free-app-in-the-us-apple-app-store-on-october-23-10172026']:
    e=ev[slug]; real=[]
    print("====",slug,"volume",e.get('volume'),"liquidity",e.get('liquidity'),"markets",len(e['markets']))
    for m in e['markets']:
        g=m.get('groupItemTitle') or ''
        if g.lower().startswith(('reserved','app ')) or g=='Other': continue
        real.append((g,json.loads(m.get('outcomePrices') or '[]'),m.get('bestBid'),m.get('bestAsk')))
    for r in real: print("  ",r)
    sb=sum(float(x[2]) for x in real); fees=sum(0.05*(1-float(x[2]))*(float(x[2])) for x in real)
    print("  n",len(real),"sum bestBid",round(sb,4),"NO fees",round(fees,5),"breakeven P(Other)",round(1-sb+fees,4))
print("--- 06:00->16:00 EV using P1=64/71=0.9014084507042254, half-spread 0.015 ---")
for p in [0.84,0.85,0.86,0.87,0.88,0.89,0.90,0.92,0.95,0.98]:
    fee=0.05*p*(1-p); cost=p+fee+0.015; evv=64/71-cost
    print(f"p={p:.2f} fee={fee:.5f} cost={cost:.4f} EV={evv:+.4f}")
print("--- overnight EV using P2=23/32=0.71875 ---")
for p in [0.68,0.69,0.70,0.71,0.72]:
    fee=0.05*p*(1-p); cost=p+fee+0.015; evv=23/32-cost
    print(f"p={p:.2f} fee={fee:.5f} cost={cost:.4f} EV={evv:+.4f}")
```

### D. Exact outputs

#### D1. CDX summary (from `cdx_charts_iphone.json`)
```text
rows 4295
days 454
2022 days 17 snapshots 18
2023 days 26 snapshots 28
2024 days 130 snapshots 2648
2025 days 281 snapshots 1601
days with both 04-09 and 14-19 UTC: 166 (04-08/14-18: 126)
range 20240912 20251021
days >=2 snapshots 349
202501 days 31 snaps 441
202504 days 30 snaps 184
202507 days 27 snaps 84
202510 days 28 snaps 79
```
(The 166 is the wider 04–09/14–19 frame and includes 2024; under the pre-registered 04–08/14–18 frame the all-year count is 126. Restricted to 2025, the two frames give 60 and 79 double-window days respectively — see D3b.)

#### D2. Current Apple JSON top12 (this session)
```text
HTTP:200 SIZE:25783
updated Tue, 20 Oct 2026 05:14:43 +0000 country us n 50
1 Capital One Mobile | Capital One
2 Vinted: Pre-loved marketplace | Vinted Limited
3 Muse from Meta | Meta Platforms, Inc.
4 ChatGPT | OpenAI OpCo, LLC
5 TikTok Pro - Events | TikTok Ltd.
6 PineDrama - Short Dramas | TikTok Ltd.
7 McDonald's | McDonald's USA
8 Claude by Anthropic | Anthropic PBC
9 Google Gemini | Google
10 Kalshi: Trade Football & more | KalshiEX LLC
11 Threads | Instagram, Inc.
12 CapCut: Photo & Video Editor | Bytedance Pte. Ltd
PAGE HTTP:200 SIZE:1017064
```

#### D3. Rank persistence (`python3 parse_ranks.py`)
```text
parsed (day,slot): 150 of 158
days with both AM+PM parsed: 71
P1 same-day 06->16: 64/71 = 0.9014
P2 overnight 06->next 06: 23/32 = 0.7188
--- details ---
20250101 AM CapCut - Video Editor | PM CapCut - Video Editor | same True
20250102 AM CapCut - Video Editor | PM Lemon8 - Lifestyle Community | same False
20250104 AM ChatGPT | PM Threads | same False
20250105 AM ReelShort - Short Movie &amp; TV | PM ReelShort - Short Movie &amp; TV | same True
20250107 AM ChatGPT | PM ChatGPT | same True
20250111 AM Watch Duty: Wildfire Maps | PM Lemon8 - Lifestyle Community | same False
20250112 AM Lemon8 - Lifestyle Community | PM Lemon8 - Lifestyle Community | same True
20250114 AM 小红书 | PM 小红书 | same True
20250116 AM 小红书 | PM 小红书 | same True
20250117 AM 小红书 | PM 小红书 | same True
20250118 AM 小红书 | PM 小红书 | same True
20250120 AM 小红书 | PM rednote - share, connect, love | same False
20250122 AM rednote - share, connect, love | PM rednote - share, connect, love | same True
20250123 AM rednote - share, connect, love | PM ChatGPT | same False
20250124 AM ChatGPT | PM Watch Duty: Wildfire Maps | same False
20250125 AM ChatGPT | PM ChatGPT | same True
20250126 AM ChatGPT | PM ChatGPT | same True
20250127 AM DeepSeek - AI Assistant | PM DeepSeek - AI Assistant | same True
20250128 AM DeepSeek - AI Assistant | PM DeepSeek - AI Assistant | same True
20250129 AM DeepSeek - AI Assistant | PM DeepSeek - AI Assistant | same True
20250130 AM DeepSeek - AI Assistant | PM DeepSeek - AI Assistant | same True
20250203 AM DeepSeek - AI Assistant | PM DeepSeek - AI Assistant | same True
20250204 AM DeepSeek - AI Assistant | PM DeepSeek - AI Assistant | same True
20250206 AM Apple Invites | PM Apple Invites | same True
20250207 AM Apple Invites | PM Apple Invites | same True
20250208 AM ChatGPT | PM ChatGPT | same True
20250209 AM ChatGPT | PM ChatGPT | same True
20250210 AM Tubi: Movies &amp; Live TV | PM Tubi: Movies &amp; Live TV | same True
20250211 AM Tubi: Movies &amp; Live TV | PM Tubi: Movies &amp; Live TV | same True
20250217 AM TikTok | PM TikTok | same True
20250220 AM Grok | PM Grok | same True
20250224 AM ChatGPT | PM ChatGPT | same True
20250225 AM ChatGPT | PM ChatGPT | same True
20250227 AM ChatGPT | PM ChatGPT | same True
20250305 AM Jimmy John’s Sandwiches | PM ChatGPT | same False
20250317 AM ChatGPT | PM ChatGPT | same True
20250319 AM ChatGPT | PM ChatGPT | same True
20250326 AM T-Life | PM T-Life | same True
20250401 AM ChatGPT | PM ChatGPT | same True
20250402 AM ChatGPT | PM ChatGPT | same True
20250403 AM ChatGPT | PM ChatGPT | same True
20250407 AM ChatGPT | PM ChatGPT | same True
20250408 AM ChatGPT | PM ChatGPT | same True
20250417 AM ChatGPT | PM ChatGPT | same True
20250420 AM ChatGPT | PM ChatGPT | same True
20250426 AM ChatGPT | PM ChatGPT | same True
20250511 AM ChatGPT | PM ChatGPT | same True
20250525 AM ChatGPT | PM ChatGPT | same True
20250603 AM ChatGPT | PM ChatGPT | same True
20250611 AM ChatGPT | PM ChatGPT | same True
20250617 AM ChatGPT | PM ChatGPT | same True
20250620 AM ChatGPT | PM ChatGPT | same True
20250629 AM ChatGPT | PM ChatGPT | same True
20250709 AM Love Island USA | PM Love Island USA | same True
20250710 AM ChatGPT | PM ChatGPT | same True
20250711 AM ChatGPT | PM ChatGPT | same True
20250717 AM ChatGPT | PM ChatGPT | same True
20250720 AM ChatGPT | PM ChatGPT | same True
20250726 AM Tea Dating Advice | PM Tea Dating Advice | same True
20250731 AM ChatGPT | PM ChatGPT | same True
20250806 AM ChatGPT | PM ChatGPT | same True
20250813 AM ChatGPT | PM ChatGPT | same True
20250815 AM ChatGPT | PM ChatGPT | same True
20250828 AM ChatGPT | PM ChatGPT | same True
20250914 AM Google Gemini | PM Google Gemini | same True
20251004 AM Sora by OpenAI | PM Sora by OpenAI | same True
20251008 AM Sora by OpenAI | PM Sora by OpenAI | same True
20251009 AM Sora by OpenAI | PM Sora by OpenAI | same True
20251012 AM Sora by OpenAI | PM Sora by OpenAI | same True
20251015 AM Sora by OpenAI | PM Sora by OpenAI | same True
20251021 AM Sora by OpenAI | PM Sora by OpenAI | same True
--- pairs ---
20250101 CapCut - Video Editor => 20250102 CapCut - Video Editor True
20250104 ChatGPT => 20250105 ReelShort - Short Movie &amp; TV False
20250107 ChatGPT => 20250108 Watch Duty: Wildfire Maps False
20250111 Watch Duty: Wildfire Maps => 20250112 Lemon8 - Lifestyle Community False
20250114 小红书 => 20250115 小红书 True
20250115 小红书 => 20250116 小红书 True
20250116 小红书 => 20250117 小红书 True
20250117 小红书 => 20250118 小红书 True
20250118 小红书 => 20250119 小红书 True
20250119 小红书 => 20250120 小红书 True
20250122 rednote - share, connect, love => 20250123 rednote - share, connect, love True
20250123 rednote - share, connect, love => 20250124 ChatGPT False
20250124 ChatGPT => 20250125 ChatGPT True
20250125 ChatGPT => 20250126 ChatGPT True
20250126 ChatGPT => 20250127 DeepSeek - AI Assistant False
20250127 DeepSeek - AI Assistant => 20250128 DeepSeek - AI Assistant True
20250128 DeepSeek - AI Assistant => 20250129 DeepSeek - AI Assistant True
20250129 DeepSeek - AI Assistant => 20250130 DeepSeek - AI Assistant True
20250203 DeepSeek - AI Assistant => 20250204 DeepSeek - AI Assistant True
20250206 Apple Invites => 20250207 Apple Invites True
20250207 Apple Invites => 20250208 ChatGPT False
20250208 ChatGPT => 20250209 ChatGPT True
20250209 ChatGPT => 20250210 Tubi: Movies &amp; Live TV False
20250210 Tubi: Movies &amp; Live TV => 20250211 Tubi: Movies &amp; Live TV True
20250224 ChatGPT => 20250225 ChatGPT True
20250319 ChatGPT => 20250320 CBS Sports App: Scores &amp; News False
20250401 ChatGPT => 20250402 ChatGPT True
20250402 ChatGPT => 20250403 ChatGPT True
20250407 ChatGPT => 20250408 ChatGPT True
20250709 Love Island USA => 20250710 ChatGPT False
20250710 ChatGPT => 20250711 ChatGPT True
20251008 Sora by OpenAI => 20251009 Sora by OpenAI True
```

#### D3b. Pre-registered-frame recompute (fix session 2026-10-20)

Same `parse_ranks.py`, same `snaps2/`, but the job list rebuilt with the **pre-registered** windows (C0 verbatim: 04:00–08:00 / 14:00–18:00 UTC), compared with the wider frame actually executed.
```text
C0 verbatim (04-08/14-18): target snapshots 120, double-window days 60
  parsed 114; both-parsed days 54
  P1 47/54 = 0.8704   Wilson CI (0.7558, 0.9358)
  P2 15/21 = 0.7143   Wilson CI (0.5004, 0.8619)
  snapshots still missing after 3 retries: 6
logged job list jobs2.tsv (day frame 04-09/14-19, per-day closest snapshot to 06:00/16:00; 2 picks fall outside):
  target snapshots 158, double-window days 79
  parsed 150; both-parsed days 71
  P1 64/71 = 0.9014   Wilson CI (0.8102, 0.9514)   <- D3 above
  P2 23/32 = 0.7188   Wilson CI (0.5463, 0.8444)
  snapshots still missing after 3 retries: 8
break-even p (0.05 fee, half-spread 1.5c): wide 0.8812, prereg 0.8490
+2% margin threshold:                     wide 0.8604, prereg 0.8283
```
The entry's 64/71 = 90.1% is the **post-hoc widened frame**; the pre-registered frame gives **47/54 = 87.0%**.

#### D4. Wilson confidence intervals
```text
P1 (0.9014084507042254, 0.8101907235136308, 0.951417793674671)
P2 (0.71875, 0.546251630618882, 0.8443559315435214)
```

#### D5. CLOB history summary
```text
event-level total 247
closed events 242 with history>0 16
open events 5 with history>0 5
closed positive events 16
unique end dates 4 ['2026-09-25', '2026-10-02', '2026-10-09', '2026-10-16']
closed-positive all markets 196 with history 92 zero 104
positive event slugs:
  1-free-app-in-the-us-apple-app-store-on-october-2-20260925t180000000z 1-free-app-in-the-us-apple-app-store-on-october-2-20260925t180000000z-will-muse-from-meta-be-1-free-app-in-the-us-apple-app-store-on-october-2 166
  1-free-app-in-the-us-apple-app-store-on-september-25-20260918t180000000z 1-free-app-in-the-us-apple-app-store-on-september-25-20260918t180000000z-will-muse-from-meta-be-1-free-app-in-the-us-apple-app-store-on-september-25 133
  1-paid-app-in-the-us-apple-app-store-on-october-9-20261002t180000000z 1-paid-app-in-the-us-apple-app-store-on-october-9-20261002t180000000z-will-shadowrocket-be-1-paid-app-in-the-us-apple-app-store-on-october-9 163
  1-free-app-in-the-us-apple-app-store-on-october-16 will-muse-from-meta-be-1-free-app-in-the-us-apple-app-store-on-october-16 109
  2-free-app-in-the-us-apple-app-store-on-october-2-20260925t180000000z 2-free-app-in-the-us-apple-app-store-on-october-2-20260925t180000000z-will-momo-ai-photo-video-maker-be-2-free-app-in-the-us-apple-app-store-on-october-2 165
  1-free-app-in-the-us-apple-app-store-on-october-9-20261002t180000000z 1-free-app-in-the-us-apple-app-store-on-october-9-20261002t180000000z-will-muse-from-meta-be-1-free-app-in-the-us-apple-app-store-on-october-9 165
  2-paid-app-in-the-us-apple-app-store-on-october-2-20260925t180000000z 2-paid-app-in-the-us-apple-app-store-on-october-2-20260925t180000000z-will-hotschedules-be-2-paid-app-in-the-us-apple-app-store-on-october-2 165
  1-paid-app-in-the-us-apple-app-store-on-september-25-20260918t180000000z 1-paid-app-in-the-us-apple-app-store-on-september-25-20260918t180000000z-will-play-music-theory-be-1-paid-app-in-the-us-apple-app-store-on-september-25 133
  1-paid-app-in-the-us-apple-app-store-on-october-2-20260925t180000000z 1-paid-app-in-the-us-apple-app-store-on-october-2-20260925t180000000z-will-shadowrocket-be-1-paid-app-in-the-us-apple-app-store-on-october-2 165
  2-free-app-in-the-us-apple-app-store-on-september-25-20260918t180000000z 2-free-app-in-the-us-apple-app-store-on-september-25-20260918t180000000z-will-chatgpt-be-2-free-app-in-the-us-apple-app-store-on-september-25 133
  2-free-app-in-the-us-apple-app-store-on-october-9-20261002t180000000z 2-free-app-in-the-us-apple-app-store-on-october-9-20261002t180000000z-will-chatgpt-be-2-free-app-in-the-us-apple-app-store-on-october-9 165
  2-paid-app-in-the-us-apple-app-store-on-september-25-20260918t180000000z 2-paid-app-in-the-us-apple-app-store-on-september-25-20260918t180000000z-will-shadowrocket-be-2-paid-app-in-the-us-apple-app-store-on-september-25 133
  1-paid-app-in-the-us-apple-app-store-on-october-16 will-shadowrocket-be-1-paid-app-in-the-us-apple-app-store-on-october-16 106
  2-paid-app-in-the-us-apple-app-store-on-october-9-20261002t180000000z 2-paid-app-in-the-us-apple-app-store-on-october-9-20261002t180000000z-will-hotschedules-be-2-paid-app-in-the-us-apple-app-store-on-october-9 165
  2-paid-app-in-the-us-apple-app-store-on-october-16-20261012 will-hotschedules-be-2-paid-app-in-the-us-apple-app-store-on-october-16-20261012 85
  2-free-app-in-the-us-apple-app-store-on-october-16-20261012 will-chatgpt-be-2-free-app-in-the-us-apple-app-store-on-october-16-20261012 88
```

#### D6. Polymarket recount / `Other` base rate
```text
unique events 247 closed 242 open 5
free 141 paid 76 other 30
free closed 139
US Apple free closed 138 resolved 136 Other 15 rate 0.1103
all free closed resolved 137 Other 16
free closed endDate range 2025-10-10T00:00:00Z 2026-12-31T00:00:00Z
free closed market count min/max 2 26
free closed volume sum 9570483.048294
by month {'2025-10': 5, '2025-11': 5, '2025-12': 8, '2026-01': 8, '2026-02': 11, '2026-03': 22, '2026-04': 19, '2026-05': 17, '2026-06': 12, '2026-07': 8, '2026-08': 8, '2026-09': 9, '2026-10': 6, '2026-12': 1}
```

#### D6b. Strict weekly-board `Other` filter (the number used in the entry)
```python
import json,re
ev=list(json.load(open('pm_events.json')).values())
def winner(e):
    for m in e.get('markets',[]):
        pr=json.loads(m.get('outcomePrices') or '[]'); outs=json.loads(m.get('outcomes') or '[]')
        for o,p in zip(outs,pr):
            if str(o).strip().lower()=='yes' and float(p)>0.5:
                return str(m.get('groupItemTitle') or m.get('question')).strip()
    return None
for pre in ['1-free-app-in-the-us-apple-app-store-on-','2-free-app-in-the-us-apple-app-store-on-']:
    es=[e for e in ev if e.get('closed') and e['slug'].startswith(pre)]
    w=[winner(e) for e in es]; w=[x for x in w if x]
    other=sum(1 for x in w if x.lower()=='other')
    print(pre,len(es),len(w),other,round(other/len(w),4))
```
Output:
```text
1-free-app-in-the-us-apple-app-store-on- 63 63 8 0.127
2-free-app-in-the-us-apple-app-store-on- 54 54 6 0.1111
```
Combined: 117 closed, 117 resolvable, 14 Other = 11.97% -> 12.0% in the entry. This stricter filter excludes `chatgpt-out-as-1-...` multi-date ladders; the broader 15/136 in D6 is shown only to document why it is not used.

#### D6c. `Reserved`-arm count on the 117 strict closed weekly boards
```python
import json
ev=list(json.load(open('pm_events.json')).values())
strict=[e for e in ev if e.get('closed') and (e['slug'].startswith('1-free-app-in-the-us-apple-app-store-on-') or e['slug'].startswith('2-free-app-in-the-us-apple-app-store-on-'))]
res=[e for e in strict if any(str(m.get('groupItemTitle') or '').lower().startswith('reserved') for m in e['markets'])]
print(len(strict), len(res))
```
Output:
```text
117 8
```
The previous draft's "40 closed boards still carry a `Reserved` arm" has no support in any output; the reproducible number is **8/117 = 6.8%**.

#### D7. Basket-NO and EV arithmetic
```text
==== 1-free-app-in-the-us-apple-app-store-on-october-23-10172026 volume 5918.217347 liquidity 5115.60314 markets 12
   ('Muse from Meta', ['0.715', '0.285'], 0.71, 0.72)
   ('Vinted: Pre-loved marketplace', ['0.06', '0.94'], 0.02, 0.1)
   ('ChatGPT', ['0.063', '0.937'], 0.05, 0.076)
   ('TikTok Pro - Events', ['0.0045', '0.9955'], 0.001, 0.008)
   ('Claude by Anthropic', ['0.0315', '0.9685'], 0.003, 0.06)
   ('Google Gemini', ['0.005', '0.995'], 0.001, 0.009)
   ('KICK - Live Streaming', ['0.01', '0.99'], 0.002, 0.018)
  n 7 sum bestBid 0.787 NO fees 0.014 breakeven P(Other) 0.227
==== 2-free-app-in-the-us-apple-app-store-on-october-23-10172026 volume 3197.808697 liquidity 1558.68892 markets 12
   ('Vinted: Pre-loved marketplace', ['0.39', '0.61'], 0.16, 0.62)
   ('Muse from Meta', ['0.1555', '0.8445'], 0.033, 0.278)
   ('ChatGPT', ['0.1485', '0.8515'], 0.139, 0.158)
   ('TikTok Pro - Events', ['0.0975', '0.9025'], 0.005, 0.19)
   ('Claude by Anthropic', ['0.022', '0.978'], 0.006, 0.038)
   ("McDonald's", ['0.0285', '0.9715'], 0.008, 0.049)
   ('KICK - Live Streaming', ['0.0795', '0.9205'], 0.011, 0.148)
  n 7 sum bestBid 0.362 NO fees 0.01579 breakeven P(Other) 0.6538
--- 06:00->16:00 EV using P1=64/71=0.9014084507042254, half-spread 0.015 ---
p=0.84 fee=0.00672 cost=0.8617 EV=+0.0397
p=0.85 fee=0.00638 cost=0.8714 EV=+0.0300
p=0.86 fee=0.00602 cost=0.8810 EV=+0.0204
p=0.87 fee=0.00566 cost=0.8907 EV=+0.0108
p=0.88 fee=0.00528 cost=0.9003 EV=+0.0011
p=0.89 fee=0.00490 cost=0.9099 EV=-0.0085
p=0.90 fee=0.00450 cost=0.9195 EV=-0.0181
p=0.92 fee=0.00368 cost=0.9387 EV=-0.0373
p=0.95 fee=0.00238 cost=0.9674 EV=-0.0660
p=0.98 fee=0.00098 cost=0.9960 EV=-0.0946
--- overnight EV using P2=23/32=0.71875 ---
p=0.68 fee=0.01088 cost=0.7059 EV=+0.0129
p=0.69 fee=0.01070 cost=0.7157 EV=+0.0031
p=0.70 fee=0.01050 cost=0.7255 EV=-0.0067
p=0.71 fee=0.01030 cost=0.7353 EV=-0.0165
p=0.72 fee=0.01008 cost=0.7451 EV=-0.0263
```

### E. Failed / negative results (not hidden)

- Wildcard CDX queries (`rss.applemarketingtools.com*`, `apps.apple.com/us/charts/iphone*`) returned HTTP 000/timeout; exact-URL queries were used instead.
- The first 362-snapshot Wayback batch used 6-digit `HHMMSS` timestamps and lost the date mapping; discarded, 14-digit batch used instead.
- Final 14-digit batch: 158 targeted snapshots, 150 parsed, 71 days with both AM+PM (8 snapshots still failed after 3 retries). That batch used the widened 04–09/14–19 frame; under the pre-registered 04–08/14–18 frame it is 120 targeted snapshots and 54 both-parsed days (D3b).
- P2 has only 32 consecutive-day pairs in the widened frame (21 in the pre-registered frame), below the 60 threshold; treated as indicative, not a headline.
- 226/247 events returned 0 CLOB history points; 2025 closed events remain unbacktestable. Only 4 independent settlement dates (2026-09-25, 10-02, 10-09, 10-16) have any closed-market history.
- `Other` base rate was recomputed twice: (a) broad slug filter `in-the-us-apple-app-store` gave 15/136 = 11.03%, but it mixes in `chatgpt-out-as-1-...` multi-date ladders; (b) the strict weekly-board filter `^[12]-free-app-in-the-us-apple-app-store-on-` gave **14/117 = 11.97%**, which is the number used in the entry. The old 3/20 was a small-sample count and is superseded.
- No historical last-hour (15:00->16:00 UTC) snapshot pairs were found, so the actual last-hour flip rate remains 未查到.
- Corrections applied in this fix session (2026-10-20): (a) `Reserved`-arm count 40 -> 8/117 (D6c); (b) snapshot `20250101050435` `schema:top-free` item 1 is `CapCut - Video Editor`, not `ChatGPT` (re-parsed from the same archived file); (c) the 64/71 = 90.1% base rate is a post-hoc widened frame, pre-registered frame gives 47/54 = 87.0% (D3b); (d) `#1` board first-market `clobRewards.rewardsDailyRate` re-fetched = 92 USDC, not 96; (e) EV at p=0.90 is -1.8% (was written -2.0%); (f) uncited "刷新约 2 分钟" removed; (g) `name_zh` shortened to 16 chars.

---

## glm-5.3 核查（第一轮）

All checks complete. Here is my report.

---

# Fact-check report: R017 (quant-017, App Store 榜首榜)

**Fetches (21 attempts, 18 HTTP 200):** Apple RSS JSON, charts page, CDX main + 4 small CDX, snapshot 20250101050435 + 2 flip-day snapshots, Gamma events ×2, public-search ×5 (247 events rebuilt), CLOB ×2. Log scripts C0/C6/C7/D6b saved and re-run.

**Verified (exact or time-varying-with-timestamp):** RSS JSON 25,783 B, top-12 order, size; charts page order; CDX 4,295 rows/first/last/per-year/day counts and every D1 monthly aggregate; RSS-only-1-snapshot CDX results; rule text (12:00 PM ET, 48h, last published ranking, charts URL); negRisk, 12 markets = 7 real + 4 Reserved + Other all `0.5/0.5`, bid 0/ask 1; feeSchedule rate 0.05/rebate 0.25/culture_fees; clobRewards 54/17/16/8/5, minSize 20, maxSpread 4.5; volumes 5,918.22 / 3,197.81; #1-board quotes (Muse 0.715, ΣYES 0.889, Σbid 0.787); script C6/D6b reproduce **247/242/5, Other strict 14/117=11.97%, #1 8/63, #2 6/54, 11–26 markets, all Other, vol 7,711,532, monthly counts, 62 dates**; C7 EV/breakevens (0.227/0.6538, breakeven ≈0.881); flip examples (2025-03-05 Jimmy John's→ChatGPT re-parsed from live snapshots); CLOB 2025→0 pts, Momo arm→165 pts. Prices moved slightly (Vinted YES 0.375/ask 0.59; liquidity; `updated` 05:29:52) — fine, timestamps given.

**Problems:**
1. **MISMATCH — "40 个在关闭后仍带 `Reserved` 臂"** (stated 3×: 规则， 证据4, 风险). Re-run on the 117 strict closed boards: **8** (only 8 in the entire 247-event set); no log output supports 40. Fix: 8/117.
2. **MISMATCH — 出处 snapshot line**: "`schema:top-free` 第 1 位 = `ChatGPT`" for 20250101050435 — actual (re-fetch and the log's own D3): **CapCut - Video Editor**. Fix the line.
3. **Pre-reg/script inconsistency**: entry+prereg+C0 say windows 04:00–08:00/14:00–18:00; verbatim C0 on the served CDX gives **120 jobs/60 days**, not 158/79. The logged 158/79 (and D1's 166) reproduce exactly under **04–09/14–19**. So P1=64/71 came from a wider frame than pre-registered → violates "事先写死" claim. Fix: state actual frame or recompute under stated frame.
4. Minor: name_zh is 25 chars (>18); EV table says 0.90→−2.0% vs computed −1.8% (成本节 has −1.8¢ correctly); "#1 board 首个市场日率 96" now 92; "刷新约 2 分钟" uncited.

**Rule compliance:** front-matter fields/values OK (except name_zh length); 来源自报 labelling consistent; per-market feeSchedule correctly used (0.05>GUIDE tech 0.04, noted); no fake backtests (`backtest_count=0` stated); no keys/paid data. Duplication: KNOWN.md/muse/dot clean; quant-007 same mechanism family (fixed-time public-leaderboard snapshot) — honestly self-flagged as possible variant, quant-010 distinct.

**GATES_PASSING: 4/7** (mechanism, small-capital, non-dup-borderline, sources-mostly; fails data-return-side, cost-proven-edge, 2-week-30-results)

VERDICT: FIX — the entry is overwhelmingly verifiable and honestly hedged, but the unsupported "40 Reserved" count, the misquoted snapshot #1, and the pre-registration window inconsistency (underlying P1=90.1%) must be corrected before it can be scored.


## glm-5.3 核查（修正后第二轮）

# Fact-check report: R017b.md (quant-017)

**Fetches (20):** Apple RSS, charts page, 6 Wayback CDX + 1 snapshot, Gamma public-search ×5, both event slugs, CLOB ×3. All HTTP 200 except first snapshot retry (000→200).

**VERIFIED exactly:** RSS 25,783 B, top-12 order, KICK absent from top-50; charts-page name order; CDX 4,295 rows, 2022-06-04..2025-11-03, years 18/28/2648/1601, 454 dates; snapshot 20250101050435 item1 = CapCut; Wayback coverage (RSS-50: 1 snap 20230522143120; RSS-100: none; itunes: 1 snap 20180107065423; free-apps/app-store-charts: `[]`); `totalResults=247`, 242 closed/5 open, free 141/paid 76/other 30; Other base rate **8/63 + 6/54 = 14/117 = 12.0%** (exact); Reserved arms 8/117; all 13 monthly counts; volume sum 7,711,532; endDate 2025-10-10..2026-10-16; 11–26 markets; 62 settlement days; rule text (12:00 PM ET / charts URL / 48 h / last published ranking); negRisk, restricted, umaBond=None; 12 markets = 7 real + 4 Reserved + Other at 0.5/0/1/vol 0; feeSchedule rate **0.05**, takerOnly, rebateRate 0.25; startDate/endDate; #1 volume 5,918.22, #2 volume 3,197.81; rewardsMinSize 20 / maxSpread 4.5; #1 first-market reward 92; CLOB 2025 event → 0 pts, 2026-10-16 Muse → 109 pts (matches D5). Script C0 rerun → `120 60`; widened frame → 158/79; out-of-window picks 03:49:09/13:12:44 confirmed; all 4 Wilson CIs, EV table, breakevens 0.8812/0.8490, +2% thresholds 0.8604/0.8283 reproduce. Time-varying (worker gave timestamps, OK): `updated` 05:14→05:58, prices (Muse 0.715→0.70, #2 KICK 0.0795→0.0475), liquidity, reward rates 54/17→57/18.

**Problems:**
1. **MISMATCH (arithmetic):** 证据2 "`#1`…卖价之和 **1.001**" — the table's asks sum to **0.991** (0.72+0.10+0.076+0.06+0.018+0.009+0.008). Fix: change to 0.991.
2. **MISMATCH (arithmetic):** 证据2 "`#2`…真候选 YES 之和 **0.892**" — listed prices sum to **0.9215**. Fix: recompute or delete; not in D7 log.
3. Nit: 规则8 "0.90 时 EV≈−1.8%" mixes cents/percent (−1.8¢ = −2.0% of cost; 成本节 has it right).

**Compliance:** front matter complete/valid; 来源自报 labels present (and volumes check out anyway); GUIDE fee formula `rate×p×(1−p)` used correctly, feeSchedule-over-table noted properly; 门槛自查 honest (gate 6 fails, `backtest_count=0`, no invented backtest); no keys/paid data. Duplication: quant-017 is the bot's own claimed draft (CLAIMS B14); KNOWN.md and dot/muse have no App Store entry; homology with own quant-007 is candidly flagged and deferred.

**Fixes:** correct the two sums (items 1–2); optionally the −1.8% wording.

All load-bearing numbers (base rates, Other rate, fees, rule text, CDX, CLOB) reproduce exactly; only two derived snapshot sums are wrong — clearly slips, not fabrication.

VERDICT: FIX — two minor sum errors (0.991→"1.001", 0.9215→"0.892") need correcting before submission; everything else verifies.
GATES_PASSING: 4/7 (1,2,3,7 pass; 4 uncertain—quant-007 homology; 5,6 honestly unmet)
