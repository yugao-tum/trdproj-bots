#!/usr/bin/env python3
"""SpaceX October 2026 launch running count (LL2 public API; PM settles spacex.com)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

LL2 = (
    "https://ll.thespacedevs.com/2.2.0/launch/"
    "?net__gte=2026-10-01T00:00:00Z&net__lte=2026-10-31T23:59:59Z&limit=100"
)
OUT = Path(__file__).resolve().parent / "cache" / "spacex_oct2026_running.json"


def curl_json(url: str) -> dict:
    out = subprocess.check_output(
        ["curl", "-sS", "-A", "Mozilla/5.0", url], text=True, timeout=120
    )
    return json.loads(out)


def main() -> None:
    data = curl_json(LL2)
    rows = []
    for launch in data.get("results") or []:
        prov = (launch.get("launch_service_provider") or {}).get("name") or ""
        if prov != "SpaceX":
            continue
        st = (launch.get("status") or {}).get("name") or ""
        rows.append(
            {
                "net": (launch.get("net") or "")[:19],
                "status": st,
                "name": launch.get("name"),
                "success": st == "Launch Successful",
            }
        )
    rows.sort(key=lambda r: r["net"])
    success_n = sum(1 for r in rows if r["success"])
    scheduled = [r for r in rows if r["status"] == "Go for Launch"]
    payload = {
        "source": "launch_library_2.2.0",
        "note": "Cross-check only; Polymarket settles spacex.com/launches",
        "success_count": success_n,
        "go_for_launch_count": len(scheduled),
        "upper_bound_if_all_go": success_n + len(scheduled),
        "launches": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"success_count": success_n, "path": str(OUT)}))


if __name__ == "__main__":
    main()
