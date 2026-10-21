#!/usr/bin/env python3
"""composer-008 replay entry: delegates to notes/usgs_weekly_55_replay.py."""
from __future__ import annotations

import runpy
from pathlib import Path

_NOTES = Path(__file__).resolve().parents[2] / "notes" / "usgs_weekly_55_replay.py"
runpy.run_path(str(_NOTES), run_name="__main__")
