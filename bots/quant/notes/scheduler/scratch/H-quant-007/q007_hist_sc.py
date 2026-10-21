#!/usr/bin/env python3
"""quant-007 historical tradable-price backtest.

Data (all free, keyless, fetched 2026-10-21):
  - Gamma events?series_id=10030&closed=true  -> rules, arms, resolutions
  - CLOB prices-history?market=<token>&interval=max&fidelity=1440 -> closed-market price path
  - data-api trades?market=<conditionId> -> executed fills (validation subsample)
  - HF lmarena-ai/leaderboard-dataset text/full parquet -> daily overall leaderboard snapshots

Strategy under test (pre-registered, no fitting):
  At check_time - L days (L in {7,14,21}), buy YES of the company that is
  Rank 1 on the latest published "overall" leaderboard snapshot on/before
  that date; hold to settlement. Cost = taker fee rate*p*(1-p), plus
  half-spread sensitivity +0.5c / +1c.

The market's own favourite at the same instant is the benchmark.

One-off prep (needs pyarrow, run once to build _cache/overall_sc.csv):
  python3 -c "import pandas as pd; df=pd.read_parquet('_cache/text_full.parquet'); \
  df[df.category=='overall'][['model_name','organization','rating','rank','category', \
  'leaderboard_publish_date']].to_csv('_cache/overall_sc.csv',index=False)"
"""
import json, os, time, urllib.request, datetime as dt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "_cache")
UA = "Mozilla/5.0"
os.makedirs(CACHE, exist_ok=True)

ORG2ARM = {
    "anthropic": "Anthropic", "google": "Google", "openai": "OpenAI",
    "meta": "Meta", "alibaba": "Alibaba", "xai": "SpaceXAI",
    "zai": "Z.ai", "zhipu": "Z.ai", "zhipu ai": "Z.ai",
    "moonshot": "Moonshot", "minimax": "MiniMax", "mistral": "Mistral",
    "nvidia": "Nvidia", "tencent": "Tencent", "amazon": "Amazon",
    "baidu": "Baidu", "stepfun": "StepFun", "xiaomi": "Xiaomi",
    "microsoft": "Microsoft", "bytedance": "ByteDance", "thinky": "Thinky",
    "meituan": "Meituan", "deepseek": "DeepSeek",
}
PLACEHOLDER = set("Company A B C D E F G H I J K L M Other".split())
ALIAS = {
    "OpenAI": ["OpenAI", "ChatGPT"], "Anthropic": ["Anthropic", "Claude"],
    "Google": ["Google", "Gemini"], "SpaceXAI": ["SpaceXAI", "xAI"],
    "Meta": ["Meta", "Llama"],
}


def arm_for(lb_arm, arms):
    for a in ALIAS.get(lb_arm, [lb_arm]):
        if a in arms:
            return a
    return lb_arm


def get(url, path, binary=False):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return open(path, "rb").read() if binary else json.load(open(path))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
            break
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    open(path, "wb").write(data)
    return data if binary else json.loads(data)


def ts(datestr, end=False):
    d = dt.datetime.fromisoformat(datestr.replace("Z", "+00:00"))
    return d.timestamp()


events = get("https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=true",
             os.path.join(CACHE, "closed.json"))

rows = []
for ev in events:
    slug = ev["slug"]
    check = ts(ev["endDate"])
    check_dt = dt.datetime.fromtimestamp(check, dt.timezone.utc)
    arms = {}
    for m in ev["markets"]:
        name = m.get("groupItemTitle") or m.get("question")
        try:
            tok = json.loads(m["clobTokenIds"])[0]
        except Exception:
            tok = None
        arms[name] = {
            "token": tok, "yes": float(json.loads(m["outcomePrices"])[0]),
            "cond": m["conditionId"], "q": m["question"],
        }
    winner = [n for n, a in arms.items() if a["yes"] == 1.0]
    winner = winner[0] if len(winner) == 1 else ("MULTI:" + ",".join(winner) if winner else "NONE")

    # price path per arm (daily, interval=max)
    px = {}
    for name, a in arms.items():
        if a["token"] is None:
            continue
        fn = os.path.join(CACHE, "px_%s.json" % a["token"])
        try:
            d = get("https://clob.polymarket.com/prices-history?market=%s&interval=max&fidelity=1440"
                    % a["token"], fn)
            px[name] = [(p["t"], p["p"]) for p in d.get("history", [])]
        except Exception as e:
            px[name] = []
            print("PXFAIL", slug, name, e)

    def price_at(name, t):
        h = [x for x in px.get(name, []) if x[0] <= t]
        return h[-1] if h else None

    for lead in (7, 14, 21):
        entry = check - lead * 86400
        snap_date = (check_dt - dt.timedelta(days=lead)).date().isoformat()
        rows.append({"slug": slug, "lead": lead, "entry_ts": entry, "check": ev["endDate"],
                     "snap_target": snap_date,
                     "winner": winner, "n_arms": len(arms)})

print("events", len(events), "rows", len(rows))
pd.DataFrame(rows).to_csv(os.path.join(HERE, "events_skeleton_sc.csv"), index=False)

# ---- leaderboard snapshots ----
lb = pd.read_csv(os.path.join(CACHE, "overall.csv"))
lb = lb[lb.category == "overall"]
lb["org"] = lb.organization.str.lower().str.strip().map(ORG2ARM)
snaps = sorted(lb.leaderboard_publish_date.unique())


def snap_on_or_before(datestr):
    cand = [s for s in snaps if s <= datestr]
    return cand[-1] if cand else None


out = []
for r in rows:
    sd = snap_on_or_before(r["snap_target"])
    if sd is None:
        r.update(snap=sd, lb_arm=None, lb_model=None)
        out.append(r)
        continue
    top = lb[lb.leaderboard_publish_date == sd].sort_values("rank").iloc[0]
    r.update(snap=sd, lb_arm=top.org, lb_model=top.model_name,
             lb_rating=float(top.rating))
    out.append(r)
rows = out

# ---- attach prices ----
for r in rows:
    ev = [e for e in events if e["slug"] == r["slug"]][0]
    check = ts(ev["endDate"])
    entry = check - r["lead"] * 86400
    arms = {}
    for m in ev["markets"]:
        name = m.get("groupItemTitle") or m.get("question")
        try:
            tok = json.loads(m["clobTokenIds"])[0]
        except Exception:
            tok = None
        arms[name] = {"token": tok, "yes": float(json.loads(m["outcomePrices"])[0])}
    # load cached paths
    paths = {}
    for name, a in arms.items():
        if not a["token"]:
            continue
        fn = os.path.join(CACHE, "px_%s.json" % a["token"])
        if os.path.exists(fn):
            paths[name] = [(p["t"], p["p"]) for p in json.load(open(fn)).get("history", [])]

    def price_at(name, t):
        h = [x for x in paths.get(name, []) if x[0] <= t]
        return h[-1][1] if h else None

    named = {n: price_at(n, entry) for n in arms if n not in PLACEHOLDER}
    named = {n: p for n, p in named.items() if p is not None}
    r["lb_arm"] = arm_for(r["lb_arm"], arms) if r.get("lb_arm") else None
    r.update(lb_price=price_at(r["lb_arm"], entry) if r.get("lb_arm") else None,
             mkt_fav=max(named, key=named.get) if named else None,
             mkt_fav_price=max(named.values()) if named else None,
             n_priced=len(named))
    r["lb_won"] = int(r["lb_arm"] == r["winner"]) if r.get("lb_arm") else None
    r["fav_won"] = int(r["mkt_fav"] == r["winner"]) if r.get("mkt_fav") else None

df = pd.DataFrame(rows)
df.to_csv(os.path.join(HERE, "backtest_sc.csv"), index=False)
print(df[["slug", "lead", "snap", "lb_arm", "lb_model", "lb_price", "winner",
          "lb_won", "mkt_fav", "mkt_fav_price", "fav_won"]].to_string(index=False))
