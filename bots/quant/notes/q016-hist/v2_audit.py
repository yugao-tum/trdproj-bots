#!/usr/bin/env python3
"""Audit v1 vs v2 outputs and the local caches.  Re-runnable, stdlib only."""
import csv
import hashlib
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
CACHE = BASE / "_cache"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grab(pattern, text, default="n/a"):
    m = re.search(pattern, text, re.S)
    return m.group(1) if m else default


def parse_run(path):
    t = Path(path).read_text(encoding="utf-8")
    d = {}
    d["mapped"] = grab(r"mapped to RT slug[^:]*:\s*([0-9]+/[0-9]+)", t)
    m = re.search(r"Wayback: events with primary snapshot=(\d+)\s+with sensitivity snapshot=(\d+)", t)
    d["snapshots"] = f"{m.group(1)}/{m.group(2)}" if m else "n/a"
    d["primary_header"] = grab(r"independent priced events=(\d+)\s+scored thresholds=(\d+)", t)
    m = re.search(r"triggered trades=(\d+)\s+events/triggered=(\d+)(?:\s+events/zero-trigger=(\d+))?", t)
    d["trades"] = m.group(1) if m else "n/a"
    d["triggered_events"] = m.group(2) if m else "n/a"
    d["zero_events"] = m.group(3) if m and m.group(3) else "n/a"
    m = re.search(r"PRIMARY all priced events.*?median event net/share=([-+0-9.]+)\s+mean event net/share=([-+0-9.]+)", t, re.S)
    if m:
        d["primary_median"], d["primary_mean"] = m.group(1), m.group(2)
    else:
        m = re.search(r"median event net/share=([-+0-9.]+)\s+mean event net/share=([-+0-9.]+)", t)
        d["primary_median"] = m.group(1) if m else "n/a"
        d["primary_mean"] = m.group(2) if m else "n/a"
    m = re.search(r"PRIMARY event-cluster bootstrap 95% CI of mean: \[([-+0-9.na/]+), ([-+0-9.na/]+)\]", t)
    if not m:
        m = re.search(r"event-cluster bootstrap 95% CI of mean: \[([-+0-9.na/]+), ([-+0-9.na/]+)\]", t)
    d["primary_ci"] = f"[{m.group(1)}, {m.group(2)}]" if m else "n/a"
    m = re.search(r"SECONDARY triggered-only events:.*?median event net/share=([-+0-9.]+)\s+mean event net/share=([-+0-9.]+)", t, re.S)
    if m:
        d["secondary_median"], d["secondary_mean"] = m.group(1), m.group(2)
    else:
        d["secondary_median"], d["secondary_mean"] = d["primary_median"], d["primary_mean"]
    m = re.search(r"SECONDARY event-cluster bootstrap 95% CI of mean: \[([-+0-9.na/]+), ([-+0-9.na/]+)\]", t)
    d["secondary_ci"] = f"[{m.group(1)}, {m.group(2)}]" if m else d["primary_ci"]
    d["median_gross"] = grab(r"median trade gross/share=([-+0-9.]+)", t)
    d["brier"] = grab(r"Brier\s+model=([0-9.]+) market=([0-9.]+)\s+diff=([-+0-9.]+)", t)
    d["logloss"] = grab(r"LogLoss model=([0-9.]+) market=([0-9.]+)\s+diff=([-+0-9.]+)", t)
    d["verdict"] = grab(r"VERDICT: ([A-Z]+)", t)
    d["priced_verdict"] = grab(r"independent priced events \(primary\) = (\d+)", t)

    # sensitivity window numbers
    mb = re.search(r"-- sensitivity \[T-7d, T-24h\][^\n]*\n(.*?)(?:\n\npriced events with zero|\n\nsnapshot lag|\n\ntriggered event detail)", t, re.S)
    block = mb.group(1) if mb else ""
    m = re.search(r"independent priced events=(\d+)\s+scored thresholds=(\d+)", block)
    d["s_priced"] = f"{m.group(1)}/{m.group(2)}" if m else "n/a"
    m = re.search(r"PRIMARY all priced events.*?median event net/share=([-+0-9.]+)\s+mean event net/share=([-+0-9.]+)", block, re.S)
    d["s_primary_median_mean"] = f"{m.group(1)} / {m.group(2)}" if m else "n/a"
    m = re.search(r"PRIMARY event-cluster bootstrap 95% CI of mean: \[([-+0-9.na/]+), ([-+0-9.na/]+)\]", block)
    d["s_primary_ci"] = f"[{m.group(1)}, {m.group(2)}]" if m else "n/a"
    m = re.search(r"SECONDARY triggered-only events:.*?median event net/share=([-+0-9.]+)\s+mean event net/share=([-+0-9.]+)", block, re.S)
    d["s_secondary_median_mean"] = f"{m.group(1)} / {m.group(2)}" if m else "n/a"
    return d


def load_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def cache_audit():
    print("\n== cache audit (local _cache, gitignored) ==")
    rt = list((CACHE / "rt_search").glob("*.html")) if (CACHE / "rt_search").exists() else []
    bad_rt = []
    for f in rt:
        t = f.read_text(encoding="utf-8", errors="replace")
        if "Maintenance in progress" in t or ('data-qa="data-row"' not in t and "no results" not in t.lower()):
            bad_rt.append(f.name)
    print(f"rt_search files={len(rt)} maintenance_or_invalid={len(bad_rt)} {bad_rt[:5]}")

    pages = list((CACHE / "pages").rglob("*.html")) if (CACHE / "pages").exists() else []
    bad_pages = []
    for f in pages:
        t = f.read_text(encoding="utf-8", errors="replace")
        low = t.lower()
        if (len(t) < 2000 or "maintenance in progress" in low or "</html>" not in low
                or "wayback machine has not archived" in low):
            bad_pages.append(f.name)
    print(f"wayback snapshot files={len(pages)} partial_or_error={len(bad_pages)} {bad_pages[:5]}")

    cdx = list((CACHE / "cdx").glob("*.json")) if (CACHE / "cdx").exists() else []
    bad_cdx, empty_cdx = [], []
    for f in cdx:
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            bad_cdx.append(f.name)
            continue
        if not isinstance(j, list) or (j and not (isinstance(j[0], dict) and "ts" in j[0])):
            bad_cdx.append(f.name)
        if j == []:
            empty_cdx.append(f.name)
    print(f"cdx files={len(cdx)} invalid={len(bad_cdx)} empty_lists={len(empty_cdx)} {empty_cdx}")

    tm = list((CACHE / "timemap").glob("*.json")) if (CACHE / "timemap").exists() else []
    bad_tm = []
    for f in tm:
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(j, list):
                bad_tm.append(f.name)
        except Exception:
            bad_tm.append(f.name)
    print(f"timemap files={len(tm)} invalid={len(bad_tm)} {bad_tm}")

    tr = list((CACHE / "trades").glob("*.json")) if (CACHE / "trades").exists() else []
    bad_tr, max_len = [], 0
    for f in tr:
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            bad_tr.append(f.name)
            continue
        if not isinstance(j, list) or not all(isinstance(x, dict) for x in j):
            bad_tr.append(f.name)
            continue
        max_len = max(max_len, len(j))
    full500 = 0
    for f in tr:
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(j, list) and len(j) >= 500:
            full500 += 1
    print(f"trade files={len(tr)} invalid={len(bad_tr)} max_rows={max_len} "
          f"files_with_>=500_rows={full500}")


def main():
    old = parse_run(BASE / "run_output_v1.txt")
    new = parse_run(BASE / "run_output.txt")
    print("== v1 vs v2 stdout ==")
    keys = [
        ("mapped", "mapped to RT slug"), ("snapshots", "Wayback primary/sensitivity"),
        ("primary_header", "priced events / scored thresholds"), ("trades", "triggered trades"),
        ("triggered_events", "events triggered"), ("zero_events", "events zero-trigger"),
        ("primary_median", "PRIMARY median event net/share"),
        ("primary_mean", "PRIMARY mean event net/share"),
        ("primary_ci", "PRIMARY bootstrap 95% CI"),
        ("secondary_median", "SECONDARY median event net/share"),
        ("secondary_mean", "SECONDARY mean event net/share"),
        ("secondary_ci", "SECONDARY bootstrap 95% CI"),
        ("median_gross", "median filled-share gross"),
        ("brier", "Brier model/market/diff"), ("logloss", "LogLoss model/market/diff"),
        ("priced_verdict", "verdict priced events"), ("verdict", "VERDICT"),
        ("s_priced", "sensitivity priced/scored"),
        ("s_primary_median_mean", "sensitivity PRIMARY median / mean"),
        ("s_primary_ci", "sensitivity PRIMARY 95% CI"),
        ("s_secondary_median_mean", "sensitivity SECONDARY median / mean"),
    ]
    print(f"{'metric':42s} {'v1':>28s} {'v2':>28s}")
    for k, label in keys:
        print(f"{label:42s} {old.get(k,'n/a'):>28s} {new.get(k,'n/a'):>28s}")

    for tag, path in [("v1", "events_v1.csv"), ("v2", "events.csv")]:
        rows = load_csv(BASE / path)
        methods = {}
        for r in rows:
            methods[r["map_method"]] = methods.get(r["map_method"], 0) + 1
        mapped = sum(1 for r in rows if r.get("rt_slug"))
        unmapped = [r["event_slug"] for r in rows if not r.get("rt_slug")]
        zeros = [r["event_slug"] for r in rows if r.get("priced_thresholds") not in ("", "0")
                 and r.get("triggered") in ("0", 0)]
        no_primary = [r["event_slug"] for r in rows
                      if not r.get("snapshot_ts_primary") and r.get("range_excluded") == "0"]
        print(f"\n== {tag} mapping / events.csv ==")
        print(f"mapped={mapped}/{len(rows)} methods={dict(sorted(methods.items()))}")
        print(f"unmapped={unmapped}")
        print(f"priced_events_with_zero_triggers={len(zeros)} {zeros}")
        print(f"no_primary_snapshot={len(no_primary)} {no_primary}")
        for slug in ("over-your-live-body-rotten-tomatoes-score",
                     "evil-dead-burn-rotten-tomatoes-score-20260708180406392"):
            for r in rows:
                if r["event_slug"] == slug:
                    print(f"{slug}: rt_slug={r['rt_slug']!r} map_method={r['map_method']} "
                          f"map_note={r.get('map_note','')!r} snap_p={r['snapshot_ts_primary']!r} "
                          f"snap_s={r['snapshot_ts_sens']!r} priced={r['priced_thresholds']!r}")

    print("\n== sha256 ==")
    for f in ("run_output_v1.txt", "run_output.txt", "events_v1.csv", "events.csv"):
        print(f"{sha(BASE / f)}  {f}")
    cache_audit()


if __name__ == "__main__":
    main()
