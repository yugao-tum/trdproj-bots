#!/usr/bin/env python3
"""Check that I02 kept the entry's identity fields unchanged and its fields valid."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
entry = ROOT / "bots/quant/entries/quant-006-tennis-elo-pm-pricing.md"
text = entry.read_text(encoding="utf-8")
m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
assert m, "missing YAML front matter"
fields = {}
for line in m.group(1).splitlines():
    if ":" in line:
        k, v = line.split(":", 1)
        fields[k.strip()] = v.strip()

REQUIRED = ["id", "name_zh", "name_en", "bot", "date", "market", "pm_category", "kind",
            "improves", "category", "return_type", "instruments", "venues", "data",
            "test_2w", "status", "confidence"]
missing = [k for k in REQUIRED if not fields.get(k)]
print("file:", entry.relative_to(ROOT))
print("id:", fields.get("id"), "(expected quant-006)")
print("date:", fields.get("date"), "(expected 2026-10-20)")
print("status:", fields.get("status"), "(expected 草稿)")
print("name_zh:", fields.get("name_zh"))
print("required fields present:", not missing, missing)
print("id matches filename:", fields.get("id") == entry.stem.split("-")[0] + "-" + entry.stem.split("-")[1])
print("date unchanged:", fields.get("date") == "2026-10-20")
print("status is draft:", fields.get("status") == "草稿")
print("market/pm_category valid:", fields.get("market") == "polymarket"
      and fields.get("pm_category") in {"finance", "politics", "tech", "crypto", "economics",
                                        "weather", "culture", "mentions", "sports", "geopolitics",
                                        "other", "cross"})
print("has gate 6 section:", "6. 两周内能检验：" in text)
print("mentions q006-hist:", "q006-hist" in text)
print("mentions I02:", "scratch/I02" in text)
