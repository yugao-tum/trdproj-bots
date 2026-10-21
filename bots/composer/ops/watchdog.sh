#!/usr/bin/env bash
# VM 守护：每 N 秒跑采集（不推送 GitHub）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INTERVAL="${COMPOSER_WATCHDOG_INTERVAL:-900}"
cd "$ROOT"
while true; do
  echo "[watchdog] $(date -u +%Y-%m-%dT%H:%M:%SZ) cycle"
  python3 ops/run_cycle.py --watchdog || true
  sleep "$INTERVAL"
done
