#!/usr/bin/env python3
"""Re-check the two public URLs newly cited by I02 for the Sackmann archive."""
import requests

URLS = [
    "https://github.com/Aneeshers/tennis-sackmann-archive",
    "https://raw.githubusercontent.com/Aneeshers/tennis-sackmann-archive/main/atp/atp_matches_2026.csv",
]
HEADERS = {"User-Agent": "Mozilla/5.0 (research; quant-006 I02)"}
for url in URLS:
    try:
        r = requests.get(url, timeout=30, headers=HEADERS)
        print(url, r.status_code, len(r.content), r.headers.get("content-type"))
        print("first:", r.text[:160].replace("\n", " | "))
    except Exception as exc:  # noqa: BLE001
        print(url, "ERR", repr(exc))
