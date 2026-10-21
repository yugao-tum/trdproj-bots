#!/usr/bin/env python3
"""Checks and scoring for the bot strategy competition (stdlib only).

Lint also checks for files over 1 MB and binary files in bot directories.

Usage:
  python3 tools/check.py lint [--bot NAME]  # 只查指定机器人；第 2 轮字段、证据文件、1 MB 和二进制文件
  python3 tools/check.py dupes   # likely duplicates: similar names or shared source URLs
  python3 tools/check.py stats   # 按市场、类型、状态及 evidence、result、slot 统计
  python3 tools/check.py audit START  # 操作员只读审查 START..HEAD 的目录越界、PLAN 改写和明细旧行改写
  python3 tools/check.py score   # read reviews/REVIEWS.csv, write scoreboard/SCOREBOARD.md (operator only)

Scoring rules: GUIDE.md section 3. The point tables below must match it.
Lint 对待核条目用 git 里 status: 待核 第一次出现的提交时间近似分轮；草稿、
没有 git 或未提交文件用 date。认定以操作员按 GitHub 推送到达 main 的记录核对为准。
提示不算问题；自测负的条目可以待核，不限制 kind。
"""
import collections
import csv
import datetime as dt
import difflib
import os
import pathlib
import re
import sys
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOTS = ROOT / "bots"
REVIEWS = ROOT / "reviews" / "REVIEWS.csv"
SCOREBOARD = ROOT / "scoreboard" / "SCOREBOARD.md"

REQUIRED = ["id", "name_zh", "name_en", "bot", "date", "market", "pm_category", "kind", "improves", "category",
            "return_type", "instruments", "venues", "data", "test_2w", "status", "confidence"]
MARKETS = {"polymarket", "crypto", "prediction_other", "other"}
ROUND2_FIELDS = ["evidence", "result", "slot", "variants", "variants_ext", "window", "max_dd", "contribution"]
EVIDENCE = {"回放", "前向", "回放+前向", "无"}
RESULTS = {"正", "负", "不显著", "未测"}
SLOTS = {"新机制", "-"}
NEW_SLOT_CAP = 3
ROUND2_START = "2026-10-26"
LEDGER_FIELDS = ["time_utc", "event_id", "market", "action", "side", "price", "price_source", "size", "fee", "pnl", "note"]
PM_CATEGORIES = {"finance", "politics", "tech", "crypto", "economics", "weather", "culture", "mentions", "sports",
                 "geopolitics", "other", "cross"}
KINDS = {"new", "improvement", "supplement"}
CATEGORIES = set("TRFESCAMVYXB") | {"?"}
RETURN_TYPES = {"direction", "convergence", "carry", "service", "insurance", "rent", "vol_harvest", "mixed", "unknown"}
STATUSES = {"草稿", "待核"}
CONFIDENCE = {"高", "中", "低"}
URL = re.compile(r"https?://[^\s)>\]，。；;]+")
ROUND_CAP = 15  # 待核 entries per bot per round (GUIDE 3.3)
BINARY_SUFFIXES = {".pkl", ".pickle", ".parquet", ".feather", ".npy", ".npz", ".joblib",
                   ".zip", ".gz", ".bz2", ".xz", ".7z", ".db", ".sqlite", ".h5", ".hdf5"}

# GUIDE 3.1-3.3
WEIGHTS = {"polymarket": 1.3, "crypto_structural": 1.3, "crypto": 1.0, "prediction_other": 1.0, "other": 0.7}
OUTCOMES = {"收录": 3.0, "待选区": 1.0, "改进采纳": 2.0, "补充采纳": 0.5, "退回": 0.0, "退回（低质）": -0.5, "编造": -5.0, "-": 0.0}
STAGES = {"无": 0.0, "通过快速筛选": 5.0, "通过正式检验": 15.0, "进影子前向或模拟盘": 25.0}
NEW_PATH = 1.0
REVIEW_FIELDS = ["round", "date", "entry", "bot", "market", "outcome", "stage", "new_path", "best", "reason"]


def entries():
    for path in sorted(BOTS.glob("*/entries/*.md")):
        if any(p.is_symlink() for p in (path, path.parent, path.parent.parent)):
            continue
        text = path.read_text(encoding="utf-8")
        yield path, front_matter(text), text


def round_of(date):
    """Round 1 is the week of 2026-10-19 (Monday) to 2026-10-25, UTC."""
    d = dt.date.fromisoformat(date)
    return (d - dt.date(2026, 10, 19)).days // 7 + 1


def front_matter(text):
    fields = {}
    if text.startswith("---"):
        for line in text.split("---", 2)[1].splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                fields[key.strip()] = value.strip()
    return fields


def git(*args):
    """Read-only git, no shell, no external diff/text conversion. None when unavailable."""
    try:
        p = subprocess.run(["git", "--no-pager", "-C", str(ROOT), *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        return p.stdout if p.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def entry_dates(path, f):
    """(round date, first commit date); follow renames, use first pending occurrence, not file birth."""
    fallback = f.get("date", "")
    relative = path.relative_to(ROOT).as_posix()
    history = git("log", "--follow", "--format=%H %cI", "--", relative)
    pending_date, first_date = None, None
    for line in (history or "").splitlines():  # newest to oldest, overwriting yields the earliest
        try:
            sha, stamp = line.split(" ", 1)
            day = dt.datetime.fromisoformat(stamp).astimezone(dt.timezone.utc).date().isoformat()
        except ValueError:
            continue
        first_date = day
        if f.get("status") == "待核":
            content = git("show", f"{sha}:{relative}")
            if content is not None and front_matter(content).get("status") == "待核":
                pending_date = day
        # At a rename commit the content is at the new path; older commits use the old path.
        changes = git("diff-tree", "--no-commit-id", "--name-status", "-r", "-M", sha, "--")
        for change in (changes or "").splitlines():
            cells = change.split("\t")
            if len(cells) == 3 and cells[0].startswith("R") and cells[2] == relative:
                relative = cells[1]
                break
    return pending_date or fallback, first_date


def artifact_exists(bot_dir, path, directory=False):
    current = bot_dir
    if current.is_symlink():
        return False
    for part in path.relative_to(bot_dir).parts:
        current = current / part
        if current.is_symlink():
            return False
    return current.is_dir() if directory else current.is_file()


def round2_problems(path, f, bad, hint):
    missing = [k for k in ROUND2_FIELDS if not f.get(k)]
    if missing:
        bad("第 2 轮起缺字段或为空：" + "、".join(missing))
    for key, allowed in (("evidence", EVIDENCE), ("result", RESULTS), ("slot", SLOTS)):
        if f.get(key) and f[key] not in allowed:
            bad(f"{key} 应为 {'、'.join(sorted(allowed))} 之一")
    variants = f.get("variants", "")
    own_count = (1 if variants.strip("0") else 0) if re.fullmatch(r"[0-9]+", variants) else None
    if variants and own_count is None:
        bad("variants 应为非负整数")
    ext = f.get("variants_ext", "")
    if ext and ext not in ("不清楚", "-") and not re.fullmatch(r"[0-9]+", ext):
        bad("variants_ext 应为非负整数、不清楚或 -")
    window, dates = f.get("window", ""), None
    if window and window != "-":
        try:
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\.\.[0-9]{4}-[0-9]{2}-[0-9]{2}", window):
                raise ValueError
            start, end = (dt.date.fromisoformat(s) for s in window.split(".."))
            if start > end:
                raise ValueError
            dates = start, end
        except ValueError:
            bad("window 应为 - 或有效的 YYYY-MM-DD..YYYY-MM-DD，起点不能晚于终点")
    percent = r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)%"
    dd = f.get("max_dd", "")
    numeric_dd = bool(re.fullmatch(percent + r"(?:（[^（）\r\n]+）|\([^()\r\n]+\))?", dd))
    if dd and dd not in ("不清楚", "-") and not numeric_dd:
        bad("max_dd 应为百分数（可注明日线或小时）、不清楚或 -")
    contribution = f.get("contribution", "")
    if contribution and contribution != "不清楚" and not re.fullmatch(percent, contribution):
        bad("contribution 应为百分数或不清楚")
    evidence, result = f.get("evidence"), f.get("result")
    if (evidence == "无") != (result == "未测"):
        bad("evidence: 无 和 result: 未测 必须同时出现")
    if evidence == "无" and own_count != 0:
        bad("evidence: 无 时 variants 应为 0")
    if f.get("status") == "待核" and f.get("slot") != "新机制" and evidence == "无":
        bad("待核且不占新机制名额的条目要有实测，evidence 不能是无")
    if f.get("slot") == "新机制":
        if f.get("kind") != "new":
            bad("slot: 新机制 只能配 kind: new")
        if f.get("status") == "草稿":
            hint("草稿写了 slot: 新机制；草稿不占待核名额")
    bot_dir, eid = path.parent.parent, f.get("id", "")
    safe_id = bool(re.fullmatch(rf"{re.escape(bot_dir.name)}-[0-9]{{3}}", eid))
    if evidence in EVIDENCE and "回放" in evidence:
        if own_count is None or own_count < 1:
            bad("evidence 含回放时 variants 至少为 1")
        if not safe_id or not artifact_exists(bot_dir, bot_dir / "replay" / eid / "SUMMARY.md"):
            bad("evidence 含回放时要有 replay/<条目编号>/SUMMARY.md")
        if f.get("market") == "crypto" and not numeric_dd:
            bad("加密且带回放的条目，max_dd 必须是数字百分数")
    if evidence in EVIDENCE and "前向" in evidence:
        directory = bot_dir / "forward" / eid
        for name in ("PLAN.md", "RESULT.md"):
            if not safe_id or not artifact_exists(bot_dir, directory / name):
                bad(f"evidence 含前向时要有 forward/<条目编号>/{name}")
        ledgers = [p for p in directory.glob("ledger*.csv") if artifact_exists(bot_dir, p)] if safe_id and artifact_exists(bot_dir, directory, True) else []
        if not ledgers:
            bad("evidence 含前向时至少要有一个 forward/<条目编号>/ledger*.csv")
        for ledger in sorted(ledgers):
            try:
                with ledger.open(encoding="utf-8", newline="") as fh:
                    header = next(csv.reader(fh), [])  # header only, never read historical evidence rows
                if header != LEDGER_FIELDS:
                    bad(f"{ledger.name} 的表头应为：{','.join(LEDGER_FIELDS)}")
            except (OSError, UnicodeDecodeError, csv.Error):
                bad(f"{ledger.name} 的表头读不出")
    if f.get("market") == "crypto" and dates:
        start, end = dates
        if start < dt.date(2022, 1, 1):
            bad("加密 window 起点不能早于 2022-01-01")
        if start < dt.date(2024, 1, 1) and end > dt.date(2024, 12, 31):
            bad("加密 window 起点早于 2024-01-01 时，终点不能晚于 2024-12-31")
        if start >= dt.date(2024, 1, 1):
            hint("请核对数据起点和 70% 切分点")
    if result == "正" and contribution == "不清楚":
        hint("result 为正，contribution 还不清楚，请补年化贡献粗算")


def lint(bot_name=None):
    """Check only the requested bot when given; hints do not count as problems."""
    problems = 0
    seen = {}
    pending = collections.Counter()
    new_slots = collections.Counter()

    def bad(rel, msg):
        nonlocal problems
        print(f"{rel}: {msg}")
        problems += 1

    for path, f, _ in entries():
        bot_dir = path.parent.parent.name
        if bot_name is not None and bot_dir != bot_name:
            continue
        rel = path.relative_to(ROOT)
        missing = [k for k in REQUIRED if not f.get(k)]
        if missing:
            bad(rel, f"缺字段或为空：{', '.join(missing)}")
        if f.get("bot") and f["bot"] != bot_dir:
            bad(rel, f"bot 字段 {f['bot']!r} 和目录名 {bot_dir!r} 不一致")
        if f.get("id") and not path.stem.startswith(f["id"] + "-"):
            bad(rel, f"文件名应以 id {f['id']!r} 加连字符开头")
        if f.get("id") and not re.fullmatch(rf"{re.escape(bot_dir)}-\d{{3}}", f["id"]):
            bad(rel, f"id 应写成 {bot_dir}-三位编号")
        if f.get("id"):
            if f["id"] in seen:
                bad(rel, f"id 和 {seen[f['id']]} 重复")
            seen.setdefault(f["id"], rel)
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
                    round_of(f["date"])
                except ValueError:
                    bad(rel, "date 不是有效日期")
        date, first = entry_dates(path, f)
        if first and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", f.get("date", "")) and f["date"] < first:
            print(f"{rel}: 提示：date 早于文件第一次提交日期 {first}，请核对")
        try:
            rnd = round_of(date)
            is_round2 = dt.date.fromisoformat(date) >= dt.date.fromisoformat(ROUND2_START)
        except ValueError:
            continue  # invalid or missing dates were checked above
        if f.get("status") == "待核":
            pending[(bot_dir, rnd)] += 1
        if is_round2:
            round2_problems(path, f, lambda msg: bad(rel, msg), lambda msg: print(f"{rel}: 提示：{msg}"))
            if f.get("status") == "待核" and f.get("slot") == "新机制":
                new_slots[(bot_dir, rnd)] += 1
    for (bot, rnd), n in sorted(new_slots.items()):
        if n > NEW_SLOT_CAP:
            bad(f"bots/{bot}", f"第 {rnd} 轮有 {n} 条新机制，超过 {NEW_SLOT_CAP} 条名额")
    for (bot, rnd), n in sorted(pending.items()):
        if n > ROUND_CAP:
            print(f"bots/{bot}: 第 {rnd} 轮有 {n} 条待核，超过 {ROUND_CAP} 条，超出的这一轮不核对")
            problems += 1
    if BOTS.is_dir():
        for bot in sorted(p for p in BOTS.iterdir() if not p.is_symlink() and p.is_dir() and (bot_name is None or p.name == bot_name)):
            for name in ("README.md", "INDEX.md", "CLAIMS.md", "LOG.md"):
                if not (bot / name).exists():
                    print(f"bots/{bot.name}: 缺 {name}")
                    problems += 1
            for directory, dirs, files in os.walk(bot, followlinks=False):
                dirs[:] = sorted(d for d in dirs if not (pathlib.Path(directory) / d).is_symlink())
                for name in sorted(files):
                    path = pathlib.Path(directory) / name
                    if path.is_symlink() or not path.is_file():
                        continue
                    rel = path.relative_to(ROOT)
                    if path.stat().st_size > 1_000_000:
                        bad(rel, "文件超过 1 MB，原始数据不要进仓库")
                    with path.open("rb") as fh:
                        prefix = fh.read(8192)
                    if path.suffix.lower() in BINARY_SUFFIXES or b"\x00" in prefix:
                        bad(rel, "二进制文件，不要提交")
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
    for key in ("bot", "market", "pm_category", "kind", "category", "return_type", "status", "evidence", "result", "slot"):
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
            if r["market"] == "crypto_structural" and (not r["round"].isascii() or not r["round"].isdigit() or int(r["round"]) < 2):
                errors.append(f"第 {n} 行：crypto_structural 只能用在第 2 轮起的核对记录")
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


def audit(start):
    """Read-only first-parent diffs of every commit in start..HEAD; print metadata only, never evidence rows."""
    base = git("rev-parse", "--verify", "--end-of-options", start + "^{commit}")
    if base is None:
        print("起点提交不存在，或当前目录不是 git 仓库")
        return 1
    commits = git("rev-list", "--reverse", base.strip() + "..HEAD")
    if commits is None:
        print("无法读取起点到 HEAD 的历史")
        return 1
    findings = 0
    for sha in commits.splitlines():
        subject = git("show", "-s", "--format=%s", sha) or ""
        match = re.match(r"\[([a-z0-9][a-z0-9_-]*)\]", subject)
        owner = match.group(1) if match else None
        def note(msg):
            nonlocal findings
            print(f"{sha[:12]}：{msg}")
            findings += 1
        if owner is None:
            note("提交说明开头没有可识别的 [名字]，请人工核对提交者")
        parents = (git("show", "-s", "--format=%P", sha) or "").split()
        args = (parents[0], sha) if parents else ("--root", sha)
        changed = git("diff-tree", "--no-commit-id", "--name-status", "-r", "-M", *args, "--")
        if changed is None:
            note("无法读取改动，请人工核对")
            continue
        for line in changed.splitlines():
            cells = line.split("\t")
            if len(cells) < 2:
                continue
            code, paths = cells[0], cells[1:]
            old, new = paths[0], paths[-1]
            if owner and any(not p.startswith(f"bots/{owner}/") for p in paths):
                note("改了提交者自己目录以外的文件：" + " → ".join(paths))
            if code != "A" and any(re.fullmatch(r"bots/[^/]+/forward/[^/]+/PLAN\.md", p) for p in paths):
                note("改动过已有前向登记：" + " → ".join(paths))
            if code != "A" and any(re.fullmatch(r"bots/[^/]+/forward/[^/]+/ledger[^/]*\.csv", p) for p in paths):
                before = git("show", f"{parents[0]}:{old}") if parents else None
                after = git("show", f"{sha}:{new}") if code != "D" else None
                # Compare complete lines: a partial old last line cannot be rewritten under the guise of appending.
                previous = before.splitlines(keepends=True) if before is not None else None
                current = after.splitlines(keepends=True) if after is not None else None
                if previous is None or current is None or current[:len(previous)] != previous:
                    note("删除或改写了前向明细旧行：" + " → ".join(paths))
    print(f"审查完毕，{len(commits.splitlines())} 个提交，提示 {findings} 处（请人工核对）")
    return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command")
    lint_parser = commands.add_parser("lint")
    lint_parser.add_argument("--bot", help="只输出、只计这个机器人目录的问题")
    for name in ("dupes", "stats", "score"):
        commands.add_parser(name)
    audit_parser = commands.add_parser("audit")
    audit_parser.add_argument("start", help="起点提交（不含该提交）")
    args = parser.parse_args()
    if args.command == "audit":
        sys.exit(audit(args.start))
    if args.command in (None, "lint"):
        sys.exit(lint(getattr(args, "bot", None)))
    sys.exit({"dupes": dupes, "stats": stats, "score": score}[args.command]())
