#!/usr/bin/env python3
"""Checks and scoring for the bot strategy competition (stdlib only).

Usage:
  python3 tools/check.py lint    # field and naming checks for every entry
  python3 tools/check.py dupes   # likely duplicates: similar names or shared source URLs
  python3 tools/check.py stats   # entry counts by bot, market, Polymarket category, kind, category, return_type, status
  python3 tools/check.py score   # read reviews/REVIEWS.csv, write scoreboard/SCOREBOARD.md (operator only)

Scoring rules: GUIDE.md section 3. The point tables below must match it.
"""
import collections
import csv
import datetime as dt
import difflib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOTS = ROOT / "bots"
REVIEWS = ROOT / "reviews" / "REVIEWS.csv"
SCOREBOARD = ROOT / "scoreboard" / "SCOREBOARD.md"

REQUIRED = ["id", "name_zh", "name_en", "bot", "date", "market", "pm_category", "kind", "improves", "category",
            "return_type", "instruments", "venues", "data", "test_2w", "status", "confidence"]
MARKETS = {"polymarket", "crypto", "prediction_other", "other"}
PM_CATEGORIES = {"finance", "politics", "tech", "crypto", "economics", "weather", "culture", "mentions", "sports",
                 "geopolitics", "other", "cross"}
KINDS = {"new", "improvement", "supplement"}
CATEGORIES = set("TRFESCAMVYXB") | {"?"}
RETURN_TYPES = {"direction", "convergence", "carry", "service", "insurance", "rent", "vol_harvest", "mixed", "unknown"}
STATUSES = {"草稿", "待核"}
CONFIDENCE = {"高", "中", "低"}
URL = re.compile(r"https?://[^\s)>\]，。；;]+")
ROUND_CAP = 15  # 待核 entries per bot per round (GUIDE 3.3)

# GUIDE 3.1-3.3
WEIGHTS = {"polymarket": 1.3, "crypto": 1.0, "prediction_other": 1.0, "other": 0.7}
OUTCOMES = {"收录": 3.0, "待选区": 1.0, "改进采纳": 2.0, "补充采纳": 0.5, "退回": 0.0, "退回（低质）": -0.5, "编造": -5.0, "-": 0.0}
STAGES = {"无": 0.0, "通过快速筛选": 5.0, "通过正式检验": 15.0, "进影子前向或模拟盘": 25.0}
NEW_PATH = 1.0
REVIEW_FIELDS = ["round", "date", "entry", "bot", "market", "outcome", "stage", "new_path", "best", "reason"]


def entries():
    for path in sorted(BOTS.glob("*/entries/*.md")):
        text = path.read_text(encoding="utf-8")
        fields = {}
        if text.startswith("---"):
            head = text.split("---", 2)[1]
            for line in head.splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    fields[key.strip()] = value.strip()
        yield path, fields, text


def round_of(date):
    """Round 1 is the week of 2026-10-19 (Monday) to 2026-10-25, UTC."""
    d = dt.date.fromisoformat(date)
    return (d - dt.date(2026, 10, 19)).days // 7 + 1


def lint():
    problems = 0
    seen = {}
    pending = collections.Counter()

    def bad(rel, msg):
        nonlocal problems
        print(f"{rel}: {msg}")
        problems += 1

    for path, f, _ in entries():
        rel = path.relative_to(ROOT)
        bot_dir = path.parent.parent.name
        missing = [k for k in REQUIRED if not f.get(k)]
        if missing:
            bad(rel, f"缺字段或为空：{', '.join(missing)}")
        if f.get("bot") and f["bot"] != bot_dir:
            bad(rel, f"bot 字段 {f['bot']!r} 和目录名 {bot_dir!r} 不一致")
        if f.get("id") and not path.stem.startswith(f["id"] + "-"):
            bad(rel, f"文件名应以 id {f['id']!r} 加连字符开头")
        if f.get("id") and not re.fullmatch(rf"{re.escape(bot_dir)}-\d{{3}}", f["id"]):
            bad(rel, f"id 应写成 {bot_dir}-三位编号")
        if f.get("id") in seen:
            bad(rel, f"id 和 {seen[f['id']]} 重复")
        seen.setdefault(f.get("id"), rel)
        if f.get("market") and f["market"] not in MARKETS:
            bad(rel, f"market 应为 {'、'.join(sorted(MARKETS))} 之一")
        if f.get("market") == "polymarket" and f.get("pm_category") not in PM_CATEGORIES:
            bad(rel, f"Polymarket 条目的 pm_category 应为 {'、'.join(sorted(PM_CATEGORIES))} 之一")
        if f.get("market") and f["market"] != "polymarket" and f.get("pm_category") not in (None, "-"):
            bad(rel, "不是 Polymarket 的条目，pm_category 写 -")
        if f.get("kind") and f["kind"] not in KINDS:
            bad(rel, "kind 应为 new、improvement 或 supplement")
        if f.get("kind") in ("improvement", "supplement") and f.get("improves") in (None, "", "-"):
            bad(rel, "改进或补充条目要在 improves 写原条目编号或 known/ 里的名字")
        if f.get("kind") == "new" and f.get("improves") not in (None, "-"):
            bad(rel, "新策略的 improves 写 -")
        if f.get("category") and f["category"] not in CATEGORIES:
            bad(rel, f"category {f['category']!r} 不在 {''.join(sorted(CATEGORIES - {'?'}))} 或 ? 之内")
        if f.get("return_type") and f["return_type"] not in RETURN_TYPES:
            bad(rel, f"return_type {f['return_type']!r} 不是允许的值")
        if f.get("status") and f["status"] not in STATUSES:
            bad(rel, "status 应为 草稿 或 待核")
        if f.get("confidence") and f["confidence"] not in CONFIDENCE:
            bad(rel, "confidence 应为 高、中 或 低")
        if f.get("date"):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", f["date"]):
                bad(rel, "date 应写成 YYYY-MM-DD")
            elif f.get("status") == "待核":
                try:
                    pending[(bot_dir, round_of(f["date"]))] += 1
                except ValueError:
                    bad(rel, "date 不是有效日期")
    for (bot, rnd), n in sorted(pending.items()):
        if n > ROUND_CAP:
            print(f"bots/{bot}: 第 {rnd} 轮有 {n} 条待核，超过 {ROUND_CAP} 条，超出的这一轮不核对")
            problems += 1
    if BOTS.is_dir():
        for bot in sorted(p for p in BOTS.iterdir() if p.is_dir()):
            for name in ("README.md", "INDEX.md", "CLAIMS.md", "LOG.md"):
                if not (bot / name).exists():
                    print(f"bots/{bot.name}: 缺 {name}")
                    problems += 1
    print(f"检查完毕，问题 {problems} 个")
    return 1 if problems else 0


def dupes():
    items = list(entries())
    hits = 0
    by_url = collections.defaultdict(set)
    for path, f, text in items:
        for url in URL.findall(text):
            by_url[url.rstrip("/")].add(f.get("id") or path.stem)
    for url, ids in sorted(by_url.items()):
        if len(ids) > 1:
            print(f"同一出处被多条引用：{url} → {', '.join(sorted(ids))}")
            hits += 1
    for i, (pa, fa, _) in enumerate(items):
        for pb, fb, _ in items[i + 1:]:
            if fb.get("improves") == fa.get("id") or fa.get("improves") == fb.get("id"):
                continue
            for key in ("name_zh", "name_en"):
                a, b = fa.get(key, "").lower(), fb.get(key, "").lower()
                if a and b and difflib.SequenceMatcher(None, a, b).ratio() >= 0.75:
                    print(f"名字相近（{key}）：{fa.get('id')} 「{fa.get(key)}」 ↔ {fb.get('id')} 「{fb.get(key)}」")
                    hits += 1
                    break
    print(f"可能重复 {hits} 处（只是提示，请人工判断）")
    return 0


def stats():
    items = list(entries())
    print(f"条目共 {len(items)} 条")
    for key in ("bot", "market", "pm_category", "kind", "category", "return_type", "status"):
        counts = collections.Counter(f.get(key) or "（空）" for _, f, _ in items)
        print(f"按 {key}：" + "，".join(f"{k} {v}" for k, v in counts.most_common()))
    return 0


def read_reviews():
    if not REVIEWS.exists():
        return [], []
    rows, errors = [], []
    with REVIEWS.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != REVIEW_FIELDS:
            return [], [f"REVIEWS.csv 的表头应为：{','.join(REVIEW_FIELDS)}"]
        for n, r in enumerate(reader, start=2):
            r = {k: (v or "").strip() for k, v in r.items()}
            if not r["round"].isdigit():
                errors.append(f"第 {n} 行：round 应为正整数")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"]):
                errors.append(f"第 {n} 行：date 应写成 YYYY-MM-DD")
            if r["market"] not in WEIGHTS:
                errors.append(f"第 {n} 行：market {r['market']!r} 不认识")
            if r["outcome"] not in OUTCOMES:
                errors.append(f"第 {n} 行：outcome {r['outcome']!r} 不认识（{'、'.join(OUTCOMES)}）")
            if r["stage"] not in STAGES:
                errors.append(f"第 {n} 行：stage {r['stage']!r} 不认识（{'、'.join(STAGES)}）")
            if r["new_path"] not in ("是", "否", ""):
                errors.append(f"第 {n} 行：new_path 应为 是 或 否")
            if r["best"] not in ("是", "否", ""):
                errors.append(f"第 {n} 行：best 应为 是 或 否")
            if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*-\d{3}", r["entry"]) or not r["entry"].startswith(r["bot"] + "-"):
                errors.append(f"第 {n} 行：entry 应写成 <bot>-三位编号，且和 bot 一致")
            rows.append(r)
    return rows, errors


def points(r):
    """(找得多, 找得好) for one review row; GUIDE 3.1-3.4."""
    w = WEIGHTS[r["market"]]
    o = OUTCOMES[r["outcome"]]
    many = (o * w if o > 0 else o) + (NEW_PATH * w if r["new_path"] == "是" else 0.0)
    good = STAGES[r["stage"]] * w
    return many, good


def score():
    rows, errors = read_reviews()
    if errors:
        for e in errors:
            print(e)
        return 1
    board = collections.defaultdict(lambda: {"many": 0.0, "good": 0.0, "last": "", "counts": collections.Counter()})
    per_round = collections.defaultdict(lambda: collections.defaultdict(float))
    per_entry = {}
    best = collections.defaultdict(list)
    for r in sorted(rows, key=lambda r: (int(r["round"]), r["date"])):
        many, good = points(r)
        b = board[r["bot"]]
        b["many"] += many
        b["good"] += good
        if many or good:
            b["last"] = max(b["last"], r["date"])
        if r["outcome"] != "-":
            b["counts"][r["outcome"]] += 1
        per_round[int(r["round"])][r["bot"]] += many + good
        e = per_entry.setdefault(r["entry"], {"bot": r["bot"], "market": r["market"], "outcome": "-", "stage": "无",
                                              "points": 0.0, "reason": ""})
        if r["outcome"] != "-":
            e["outcome"] = r["outcome"]
        if STAGES[r["stage"]] > STAGES[e["stage"]]:
            e["stage"] = r["stage"]
        e["points"] += many + good
        if r["reason"]:
            e["reason"] = r["reason"]
        if r["best"] == "是":
            best[int(r["round"])].append(r["entry"])
    rank = sorted(board.items(), key=lambda kv: (-(kv[1]["many"] + kv[1]["good"]), kv[1]["last"] or "9999"))
    out = ["# 排行榜", "",
           "由 `python3 tools/check.py score` 从 `reviews/REVIEWS.csv` 生成，请勿手改。计分规则见 `GUIDE.md` 第 3 节。", ""]
    if not rows:
        out += ["还没有核对结果。第 1 轮是 2026-10-19 至 2026-10-25，结束后三天内公布。", ""]
    out += ["## 总榜", "", "| 名次 | 机器人 | 找得多 | 找得好 | 总分 | 收录 | 待选区 | 改进采纳 | 退回 |", "|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
    for i, (bot, b) in enumerate(rank, start=1):
        c = b["counts"]
        out.append(f"| {i} | {bot} | {b['many']:.1f} | {b['good']:.1f} | {b['many'] + b['good']:.1f} | {c['收录']} | {c['待选区']} | {c['改进采纳']} | "
                   f"{c['退回'] + c['退回（低质）'] + c['编造']} |")
    for title, key in (("找得多", "many"), ("找得好", "good")):
        out += ["", f"## {title}", "", "| 名次 | 机器人 | 分 |", "|---:|---|---:|"]
        for i, (bot, b) in enumerate(sorted(board.items(), key=lambda kv: (-kv[1][key], kv[1]["last"] or "9999")), start=1):
            out.append(f"| {i} | {bot} | {b[key]:.1f} |")
    out += ["", "## 每轮得分", ""]
    for rnd in sorted(per_round):
        line = "，".join(f"{bot} {p:.1f}" for bot, p in sorted(per_round[rnd].items(), key=lambda kv: -kv[1]))
        star = f"；本轮最佳：{'、'.join(best[rnd])}" if best.get(rnd) else ""
        out.append(f"- 第 {rnd} 轮：{line}{star}")
    out += ["", "## 每条条目", "", "| 条目 | 机器人 | 市场 | 结局 | 最远到哪一关 | 累计得分 | 理由 |", "|---|---|---|---|---|---:|---|"]
    for entry, e in sorted(per_entry.items()):
        out.append(f"| {entry} | {e['bot']} | {e['market']} | {e['outcome']} | {e['stage']} | {e['points']:.1f} | {e['reason'].replace('|', '/')} |")
    SCOREBOARD.parent.mkdir(exist_ok=True)
    SCOREBOARD.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已写 {SCOREBOARD.relative_to(ROOT)}：{len(rows)} 行核对，{len(board)} 个机器人")
    return 0


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "lint"
    sys.exit({"lint": lint, "dupes": dupes, "stats": stats, "score": score}.get(command, lint)())
