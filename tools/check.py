#!/usr/bin/env python3
"""Checks for the bot strategy repo (stdlib only).

Usage:
  python3 tools/check.py lint    # field and naming checks for every entry
  python3 tools/check.py dupes   # likely duplicates: similar names or shared source URLs
  python3 tools/check.py stats   # entry counts by bot, category, return_type
"""
import collections
import difflib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOTS = ROOT / "bots"
REQUIRED = ["id", "name_zh", "name_en", "bot", "date", "category", "return_type",
            "coins", "venues", "regions", "data", "supplements", "status", "confidence"]
CATEGORIES = set("TRFESCAMVYXB") | {"?"}
RETURN_TYPES = {"direction", "convergence", "carry", "service", "insurance", "rent",
                "vol_harvest", "mixed", "unknown"}
STATUSES = {"草稿", "待核"}
CONFIDENCE = {"高", "中", "低"}
URL = re.compile(r"https?://[^\s)>\]，。；;]+")


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


def lint():
    problems = 0
    seen = {}
    for path, f, _ in entries():
        rel = path.relative_to(ROOT)
        bot_dir = path.parent.parent.name
        missing = [k for k in REQUIRED if k not in f]
        if missing:
            print(f"{rel}: 缺字段 {', '.join(missing)}"); problems += 1
        if f.get("bot") and f["bot"] != bot_dir:
            print(f"{rel}: bot 字段 {f['bot']!r} 和目录名 {bot_dir!r} 不一致"); problems += 1
        if f.get("id") and not path.stem.startswith(f["id"] + "-"):
            print(f"{rel}: 文件名应以 id {f['id']!r} 加连字符开头"); problems += 1
        if f.get("id") and not re.fullmatch(rf"{re.escape(bot_dir)}-\d{{3}}", f["id"]):
            print(f"{rel}: id 应写成 {bot_dir}-三位编号"); problems += 1
        if f.get("id") in seen:
            print(f"{rel}: id 和 {seen[f['id']]} 重复"); problems += 1
        seen.setdefault(f.get("id"), rel)
        if f.get("category") and f["category"] not in CATEGORIES:
            print(f"{rel}: category {f['category']!r} 不在 {''.join(sorted(CATEGORIES - {'?'}))} 或 ? 之内"); problems += 1
        if f.get("return_type") and f["return_type"] not in RETURN_TYPES:
            print(f"{rel}: return_type {f['return_type']!r} 不是允许的值"); problems += 1
        if f.get("status") and f["status"] not in STATUSES:
            print(f"{rel}: status 应为 草稿 或 待核"); problems += 1
        if f.get("confidence") and f["confidence"] not in CONFIDENCE:
            print(f"{rel}: confidence 应为 高、中 或 低"); problems += 1
        if f.get("date") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", f["date"]):
            print(f"{rel}: date 应写成 YYYY-MM-DD"); problems += 1
    for bot in sorted(p for p in BOTS.iterdir() if p.is_dir()):
        for name in ("README.md", "INDEX.md", "CLAIMS.md", "LOG.md"):
            if not (bot / name).exists():
                print(f"bots/{bot.name}: 缺 {name}"); problems += 1
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
            print(f"同一出处被多条引用：{url} → {', '.join(sorted(ids))}"); hits += 1
    for i, (pa, fa, _) in enumerate(items):
        for pb, fb, _ in items[i + 1:]:
            if fb.get("supplements") == fa.get("id") or fa.get("supplements") == fb.get("id"):
                continue
            for key in ("name_zh", "name_en"):
                a, b = fa.get(key, "").lower(), fb.get(key, "").lower()
                if a and b and difflib.SequenceMatcher(None, a, b).ratio() >= 0.75:
                    print(f"名字相近（{key}）：{fa.get('id')} 「{fa.get(key)}」 ↔ {fb.get('id')} 「{fb.get(key)}」"); hits += 1
                    break
    print(f"可能重复 {hits} 处（只是提示，请人工判断）")
    return 0


def stats():
    items = list(entries())
    print(f"条目共 {len(items)} 条")
    for key in ("bot", "category", "return_type", "status"):
        counts = collections.Counter(f.get(key) or "（空）" for _, f, _ in items)
        print(f"按 {key}：" + "，".join(f"{k} {v}" for k, v in counts.most_common()))
    return 0


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "lint"
    sys.exit({"lint": lint, "dupes": dupes, "stats": stats}.get(command, lint)())
