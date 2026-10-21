#!/usr/bin/env python3
"""composer autonomous cycle: watchdog (cache only), hourly, retro."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPS = ROOT / "ops"
CACHE = ROOT / "notes" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def task_lint() -> dict:
    check = Path("/workspace/trdproj-tools/check.py")
    if not check.exists():
        return {"lint": "skip", "reason": "no check.py"}
    code, out = run(["python3", str(check), "lint", str(ROOT / "entries")])
    return {"lint": "ok" if code == 0 else "fail", "output_tail": out[-800:]}


def task_hormuz() -> dict:
    script = ROOT / "notes" / "hormuz_backtest_all.py"
    if not script.exists():
        return {"hormuz": "skip"}
    code, out = run(["python3", str(script)])
    summary = {}
    try:
        summary = json.loads(out.strip().split("\n")[-1])
    except json.JSONDecodeError:
        summary = {"raw": out[-500:]}
    return {"hormuz": "ok" if code == 0 else "fail", **summary}


def task_portwatch() -> dict:
    script = ROOT / "notes" / "hormuz_portwatch_weekly.py"
    code, out = run(["python3", str(script)])
    return {"portwatch": "ok" if code == 0 else "fail", "sample": out.strip()[:200]}


def task_gamma_probe() -> dict:
    code, out = run(
        [
            "curl",
            "-sS",
            "-A",
            "Mozilla/5.0",
            "https://gamma-api.polymarket.com/public-search?q=how-many-ships-transit-the-strait-of-hormuz-week&limit_per_type=5&events_status=active",
        ]
    )
    try:
        n = len(json.loads(out).get("events", []))
    except json.JSONDecodeError:
        n = -1
    return {"gamma_probe": "ok" if code == 0 and n >= 0 else "fail", "active_sample": n}


def run_parallel(tasks: dict[str, bool]) -> dict:
    fns = {
        "entry_lint": task_lint,
        "hormuz_replay": task_hormuz,
        "portwatch_fetch": task_portwatch,
        "gamma_probe": task_gamma_probe,
    }
    results = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {
            ex.submit(fns[name]): name
            for name, on in tasks.items()
            if on and name in fns
        }
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                results[name] = fut.result()
            except Exception as e:
                results[name] = {"error": str(e)}
    return results


def write_state(mode: str, results: dict):
    payload = {
        "mode": mode,
        "utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "results": results,
    }
    (CACHE / "last_cycle.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


def load_yaml_tasks() -> dict:
    # minimal parse without pyyaml dependency
    cfg = OPS / "autopilot.yaml"
    tasks = {
        "portwatch_fetch": True,
        "hormuz_replay": True,
        "entry_lint": True,
        "gamma_probe": True,
    }
    if cfg.exists():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            for key in tasks:
                if line.startswith(f"{key}:"):
                    tasks[key] = "true" in line.lower()
    return tasks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watchdog", action="store_true")
    ap.add_argument("--hourly", action="store_true")
    ap.add_argument("--retro", action="store_true")
    args = ap.parse_args()
    mode = "watchdog" if args.watchdog else "hourly" if args.hourly else "retro" if args.retro else "watchdog"
    tasks = load_yaml_tasks()
    if mode == "watchdog":
        tasks["entry_lint"] = False
    results = run_parallel(tasks)
    write_state(mode, results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
