#!/usr/bin/env python3
"""Validate quant-012 front matter without tools/check.py (which crashes on muse-700/701)."""
from pathlib import Path
p = Path("bots/quant/entries/quant-012-earthquake-count-base-rate.md")
lines = p.read_text(encoding="utf-8").splitlines()
assert lines[0] == "---"
end = lines.index("---", 1)
fields = {}
for line in lines[1:end]:
    k, _, v = line.partition(":")
    fields[k.strip()] = v.strip()
required = "id name_zh name_en bot date market pm_category kind improves category return_type instruments venues data test_2w status confidence".split()
print("fields", len(fields))
for k in required:
    print(f"  {k}: {'OK' if fields.get(k) else 'MISSING'} = {fields.get(k, '')[:80]}")
missing = [k for k in required if not fields.get(k)]
print("MISSING", missing)
print("id matches filename:", fields["id"] == "quant-012")
print("date unchanged: 2026-10-20 ->", fields["date"])
print("status:", fields["status"])
