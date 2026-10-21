#!/usr/bin/env python3
"""Minimal front-matter lint for the one quant entry touched here.

The repo-wide tools/check.py currently crashes on two muse entries that have a
blockquote before the front matter; this script only checks quant-016 so the
result is not confounded by those files.
"""
import re, sys

P = "bots/quant/entries/quant-016-rotten-tomatoes-beta-model.md"
REQ = ["id", "name_zh", "name_en", "bot", "date", "market", "pm_category", "kind",
       "improves", "category", "return_type", "instruments", "venues", "data",
       "test_2w", "status", "confidence"]
text = open(P, encoding="utf-8").read()
m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
if not m:
    sys.exit("no front matter")
fields = {}
for line in m.group(1).splitlines():
    if ":" in line:
        k, v = line.split(":", 1)
        fields[k.strip()] = v.strip()
problems = []
for k in REQ:
    if not fields.get(k):
        problems.append(f"missing/empty: {k}")
if fields.get("id") != "quant-016":
    problems.append("id != quant-016")
if fields.get("status") not in ("草稿", "待核"):
    problems.append("bad status")
if not re.fullmatch(r"2026-\d\d-\d\d", fields.get("date", "")):
    problems.append("bad date")
if len(fields.get("name_zh", "")) > 18:
    problems.append("name_zh > 18 chars")
print("file:", P)
print("fields:", len(fields), "required:", len(REQ))
print("date:", fields.get("date"), "status:", fields.get("status"))
print("problems:", problems if problems else "none")
sys.exit(1 if problems else 0)
