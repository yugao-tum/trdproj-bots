#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
cd "$ROOT"
D=bots/quant/notes/scheduler/scratch/B21
mkdir -p "$D/_cache"
curl -sL https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv -o "$D/_cache/games.csv"
python3 "$D/fetch_events.py"
python3 "$D/fetch_pregame.py"
python3 "$D/match_elo2.py"
python3 "$D/build_kick_map.py"
python3 "$D/fetch_pregame_nflkick.py"
python3 "$D/match_elo2.py"
python3 "$D/summary4.py"
