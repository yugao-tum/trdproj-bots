#!/usr/bin/env python3
"""Test how RT turns liked/notLiked counts into the displayed Tomatometer.

For every accessible /m/<slug> page with both a score and review counts, compare
score to floor(100*k/n) and round-half-up(100*k/n). This directly tests the
entry's old "floor" claim.
"""
import json, os, re, sys, time
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "_cache")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
      "Accept": "text/html,application/xhtml+xml"}
S = requests.Session(); S.headers.update(UA)

SLUGS = [
    "sense_and_sensibility_2026", "other_mommy", "clayface", "by_any_means",
    "the_wild_robot", "inside_out_2", "deadpool_and_wolverine", "dune_part_two",
    "barbie", "you_can_see_everything", "klara_and_the_sun", "ali_g_who_iz_i",
    "wildwood", "godzilla_minus_zero", "wild_horse_nine", "avengers_doomsday",
    "dune_part_three", "mufasa_the_lion_king", "wicked_for_good", "zootopia_2",
    "superman", "jurassic_world_rebirth", "fantastic_four_first_steps",
    "the_odyssey", "project_hail_mary", "altar", "roofman", "good_boy",
    "the_smashing_machine", "one_battle_after_another", "sinners",
    "a_minecraft_movie", "lilo_and_stitch", "how_to_train_your_dragon",
]

def extract(html):
    m = re.search(r'"criticsScore":\{([^}]*)\}', html)
    if not m:
        return None
    body = "{" + m.group(1) + "}"
    try:
        d = json.loads(body)
    except Exception:
        d = {}
        for key in ("likedCount", "notLikedCount", "reviewCount", "score", "scorePercent"):
            mm = re.search(r'"%s":"?([0-9.]+)"?' % key, body)
            if mm:
                d[key] = mm.group(1)
    return d

def main():
    rows = []
    for slug in SLUGS:
        path = os.path.join(CACHE, f"rt_{slug}.html")
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            html = open(path, encoding="utf-8", errors="ignore").read()
            status = 200
        else:
            try:
                r = S.get(f"https://www.rottentomatoes.com/m/{slug}", timeout=30)
                status = r.status_code
                html = r.text
            except Exception as e:
                print(f"{slug}: ERROR {e}")
                continue
            if status == 200:
                open(path, "w", encoding="utf-8").write(html)
            time.sleep(0.8)
        d = extract(html) if status == 200 else None
        if not d:
            print(f"{slug}: HTTP {status} no criticsScore")
            continue
        try:
            k = int(d.get("likedCount", -1)); nl = int(d.get("notLikedCount", -1))
            sc = d.get("score")
            sc = int(sc) if sc not in (None, "") else None
        except Exception:
            print(f"{slug}: HTTP {status} unparsable {d}")
            continue
        n = k + nl
        if sc is None or n <= 0:
            print(f"{slug}: HTTP {status} k={k} n={n} score={sc} (no display score)")
            continue
        raw = 100.0 * k / n
        fl = int(raw // 1)
        rnd = int(raw + 0.5)
        rows.append((slug, k, n, raw, sc, fl, rnd))
        print(f"{slug}: k={k} n={n} raw={raw:.4f} score={sc} floor={fl} round={rnd} "
              f"match={'BOTH' if fl == sc == rnd else ('FLOOR' if fl == sc else ('ROUND' if rnd == sc else 'NEITHER'))}")

    print("\n== summary ==")
    print("pages with score:", len(rows))
    if rows:
        both = sum(1 for r in rows if r[4] == r[5] == r[6])
        only_floor = sum(1 for r in rows if r[4] == r[5] and r[5] != r[6])
        only_round = sum(1 for r in rows if r[4] == r[6] and r[5] != r[6])
        neither = sum(1 for r in rows if r[4] != r[5] and r[4] != r[6])
        print(f"match floor={sum(1 for r in rows if r[4]==r[5])}/{len(rows)}  "
              f"match round={sum(1 for r in rows if r[4]==r[6])}/{len(rows)}")
        print(f"both={both} floor-only={only_floor} round-only={only_round} neither={neither}")
        print("disagreements (floor != round):")
        for r in rows:
            if r[5] != r[6]:
                print(f"  {r[0]}: {r[1]}/{r[2]}={r[3]:.4f} score={r[4]} floor={r[5]} round={r[6]} -> {r[4]}")

if __name__ == "__main__":
    main()
