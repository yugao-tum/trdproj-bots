#!/usr/bin/env python3
"""Field check for the single hardened entry (full-repo lint is blocked by muse files)."""
import pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[6]
p = ROOT / "bots/quant/entries/quant-001-vm-btc-regime-gate.md"
t = p.read_text(encoding="utf-8")
f = {}
for line in t.split("---", 2)[1].splitlines():
    if ":" in line:
        k, _, v = line.partition(":")
        f[k.strip()] = v.strip()
req = ["id","name_zh","name_en","bot","date","market","pm_category","kind","improves","category","return_type","instruments","venues","data","test_2w","status","confidence"]
problems=[]
for k in req:
    if not f.get(k): problems.append(f"missing {k}")
if f.get("id") != "quant-001": problems.append("id changed")
if f.get("date") != "2026-10-20": problems.append("date changed")
if f.get("status") != "待核": problems.append("status changed")
if f.get("bot") != "quant": problems.append("bot wrong")
if f.get("kind") != "improvement": problems.append("kind changed")
if f.get("improves") != "T-T2-vm": problems.append("improves changed")
if not p.name.startswith(f["id"]+"-"): problems.append("filename/id mismatch")
print("entry:", p.relative_to(ROOT))
print("fields:", f)
print("PROBLEMS:", problems if problems else "none")
