#!/usr/bin/env bash
# 立即跑一轮小时循环（不等 cron）
set -euo pipefail
cd "$(dirname "$0")/.."
echo "=== composer run_now $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
python3 ops/run_cycle.py --hourly
echo "=== done; see notes/cache/last_cycle.json ==="
