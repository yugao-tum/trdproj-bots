#!/usr/bin/env python3
"""Reproduce composer-003 OKX SOL funding z-score stats (public API only)."""
import json
import statistics
import subprocess
import sys


def curl_json(url: str):
    out = subprocess.check_output(["curl", "-sS", "-A", "Mozilla/5.0", url], text=True)
    return json.loads(out)


def main():
    inst = "SOL-USDT-SWAP"
    rates = []
    after = None
    for _ in range(50):
        url = f"https://www.okx.com/api/v5/public/funding-rate-history?instId={inst}&limit=100"
        if after:
            url += f"&after={after}"
        data = curl_json(url)["data"]
        if not data:
            break
        rates.extend(float(x["fundingRate"]) for x in data)
        after = data[-1]["fundingTime"]
        if len(data) < 100:
            break
    print("samples", len(rates))
    print("mean_bps", round(statistics.mean(rates) * 10000, 4))
    print("frac_positive", round(sum(r > 0 for r in rates) / len(rates), 3))
    ann = statistics.mean(rates) * 3 * 365 * 100
    print("naive_annual_pct", round(ann, 2))
    gated = []
    for i, r in enumerate(rates):
        if i < 30:
            continue
        w = rates[i - 30 : i]
        z = (r - statistics.mean(w)) / (statistics.pstdev(w) or 1e-9)
        if z > 0.5 and r > 0:
            gated.append(r)
    if gated:
        print("gated_n", len(gated))
        print("gated_mean_bps", round(statistics.mean(gated) * 10000, 4))
        print("gated_annual_pct", round(statistics.mean(gated) * 3 * 365 * 100, 2))


if __name__ == "__main__":
    main()
