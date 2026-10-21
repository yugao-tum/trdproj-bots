#!/usr/bin/env python3
"""Pick Polymarket markets for composer-011 forward (NEEDS #1 / PLAN rules)."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone


def curl_json(url: str) -> list | dict:
    out = subprocess.check_output(["curl", "-sS", "-A", "Mozilla/5.0", url], text=True)
    return json.loads(out)


def main() -> int:
    url = (
        "https://gamma-api.polymarket.com/markets"
        "?active=true&closed=false&limit=150&order=liquidity&ascending=false"
    )
    markets = curl_json(url)
    if not isinstance(markets, list):
        print(json.dumps({"error": "unexpected_gamma", "raw": markets}))
        return 1

    now = datetime.now(timezone.utc)
    picked = []
    for m in markets:
        slug = (m.get("slug") or "").lower()
        if "updown-5m" in slug or "updown-15m" in slug:
            continue
        rewards = m.get("clobRewards") or []
        if not rewards:
            continue
        r0 = rewards[0]
        rate = float(r0.get("rewardsDailyRate") or 0)
        if rate <= 0:
            continue
        end = m.get("endDate") or m.get("end_date_iso")
        if end:
            try:
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                if (end_dt - now).total_seconds() < 48 * 3600:
                    continue
            except ValueError:
                pass
        q = (m.get("question") or "").lower()
        politics_kw = (
            "politics",
            "senate",
            "house",
            "president",
            "election",
            "balance-of-power",
            "republican",
            "democratic",
            "governor",
        )
        pm_cat = "other"
        if any(k in slug or k in q for k in politics_kw):
            pm_cat = "politics"
        elif "crypto" in slug or "bitcoin" in q or "ethereum" in q:
            pm_cat = "crypto"
        elif "fed" in q or "cpi" in slug or "gdp" in slug or "finance" in slug:
            pm_cat = "finance"
        if pm_cat not in ("politics", "crypto", "finance"):
            continue
        picked.append(
            {
                "conditionId": m.get("conditionId"),
                "slug": m.get("slug"),
                "question": m.get("question"),
                "rewardsDailyRate": rate,
                "rewardsMinSize": m.get("rewardsMinSize"),
                "rewardsMaxSpread": m.get("rewardsMaxSpread"),
                "clobTokenIds": m.get("clobTokenIds"),
                "liquidity": m.get("liquidity"),
                "pm_category_heuristic": pm_cat,
            }
        )

    picked.sort(key=lambda x: x["rewardsDailyRate"], reverse=True)
    top = picked[:3]
    out = {
        "generated_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rule": "composer-011 PLAN 2026-10-21",
        "candidates_count": len(picked),
        "top3": top,
    }
    path = __file__.replace("pm_rewards_market_pick.py", "pm_rewards_candidates.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
