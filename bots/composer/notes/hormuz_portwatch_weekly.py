#!/usr/bin/env python3
"""Reproduce composer-004 weekly Hormuz n_total sums from IMF PortWatch ArcGIS."""
import datetime
import json
import subprocess
import sys

BASE = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
    "Daily_Chokepoints_Data/FeatureServer/0/query"
)


def fetch_all():
    offset = 0
    by_date = {}
    while True:
        url = (
            f"{BASE}?where=portid%3D%27chokepoint6%27&outFields=date%2Cn_total"
            f"&orderByFields=date%20ASC&resultRecordCount=1000&resultOffset={offset}&f=json"
        )
        data = json.loads(subprocess.check_output(["curl", "-sS", url], text=True))
        feats = data.get("features") or []
        if not feats:
            break
        for f in feats:
            a = f["attributes"]
            d = str(a["date"])[:10]
            by_date[d] = float(a["n_total"])
        if not data.get("exceededTransferLimit"):
            break
        offset += 1000
    return by_date


def week_sum(by_date, start: datetime.date) -> float:
    return sum(
        by_date.get((start + datetime.timedelta(days=i)).isoformat(), 0.0)
        for i in range(7)
    )


def main():
    by = fetch_all()
    checks = [
        ("2026-09-28", datetime.date(2026, 9, 28)),
        ("2026-07-07", datetime.date(2026, 7, 7)),
    ]
    for label, start in checks:
        print(label, "sum7", week_sum(by, start))


if __name__ == "__main__":
    main()
