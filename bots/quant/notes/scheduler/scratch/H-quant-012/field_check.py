#!/usr/bin/env python3
from pathlib import Path
import re
p = Path(__file__).resolve().parents[4] / "entries" / "quant-012-earthquake-count-base-rate.md"
text = p.read_text()
m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
fields = {}
for line in m.group(1).splitlines():
    if ":" in line:
        k, v = line.split(":", 1)
        fields[k.strip()] = v.strip()
required = ["id","name_zh","name_en","bot","date","market","pm_category","kind","improves","category","return_type","instruments","venues","data","test_2w","status","confidence"]
print("file", p)
print("fields", len(fields))
for k in required:
    print(f"  {k}: {'OK' if fields.get(k) else 'MISSING'} = {fields.get(k,'')[:120]}")
print("id matches filename:", fields.get("id") == "quant-012")
print("date:", fields.get("date"), "(unchanged 2026-10-20:", fields.get("date") == "2026-10-20", ")")
print("status:", fields.get("status"), "(unchanged 待核:", fields.get("status") == "待核", ")")
print("bytes:", len(text.encode()))
