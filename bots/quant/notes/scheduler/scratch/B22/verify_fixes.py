#!/usr/bin/env python3
"""B22 fix verification: live Gamma fields and capacity arithmetic cited in quant-025."""
import json
import requests

UA = {"User-Agent": "Mozilla/5.0 (research)"}
s = requests.Session()
s.headers.update(UA)


def main():
    r = s.get(
        "https://gamma-api.polymarket.com/events",
        params={"series_id": 12689, "closed": "true", "limit": 100, "offset": 0},
        timeout=30,
    )
    r.raise_for_status()
    ev = r.json()
    markets = [m for e in ev for m in e.get("markets", [])]
    print(f"events={len(ev)} markets={len(markets)}")
    print(f"volume_sum={sum(float(e.get('volume') or 0) for e in ev):.6f}")
    print(f"restricted_values={sorted(set(json.dumps(m.get('restricted')) for m in markets))}")
    print(f"restricted_true={sum(1 for m in markets if m.get('restricted') is True)}/{len(markets)}")

    chicago = next(m for m in markets if m["slug"].endswith("-august-19-2026-chicago-il"))
    desc = chicago.get("description", "")
    print(f"chicago.resolutionSource={chicago.get('resolutionSource')}")
    print(f"chicago.feeSchedule={json.dumps(chicago.get('feeSchedule'), sort_keys=True)}")
    print(f"chicago.restricted={chicago.get('restricted')}")
    print(f"chicago.desc_has_01:00_UTC={'01:00 UTC' in desc}")
    print(f"chicago.desc_has_hatched_SIGN={'hatched SIGN overlay' in desc}")
    print(f"chicago.desc_has_coords={'41.8781, -87.6298' in desc}")
    print(f"chicago.desc_has_NOAA_SPC={'NOAA Storm Prediction Center' in desc}")

    cost_strict = 16.03
    cost_broad = 16.93
    max_day = 9.61
    days = 62
    print("\ncapacity arithmetic")
    print(f"broad_cost_x10=${cost_broad*10:.2f} over {days}d = ${cost_broad*10/days:.2f}/day")
    print(f"strict_cost_x10=${cost_strict*10:.2f} over {days}d = ${cost_strict*10/days:.2f}/day")
    print(f"max_day_x10=${max_day*10:.2f}/day (upper bound, not average)")
    print(f"strict_2026-09-30_pnl_share=623.63/658.23={623.63/658.23:.4f}")


if __name__ == "__main__":
    main()
