#!/usr/bin/env python3
"""Re-fetch the current Gamma snapshot cited in evidence 2 and print sums."""
import json
import requests

slug = "how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25"
d = requests.get(f"https://gamma-api.polymarket.com/events?slug={slug}", timeout=60).json()
ev = d[0] if isinstance(d, list) else d
print("volume", ev.get("volume"))
print("liquidity", ev.get("liquidity"))
print("negRisk", ev.get("negRisk"))
ask = bid = 0.0
for m in ev.get("markets", []):
    a, b = float(m.get("bestAsk")), float(m.get("bestBid"))
    ask += a; bid += b
    print(m.get("groupItemTitle"), "bid", b, "ask", a, "outcomePrices", m.get("outcomePrices"))
print(f"sum bestAsk {ask:.6f}")
print(f"sum bestBid {bid:.6f}")
