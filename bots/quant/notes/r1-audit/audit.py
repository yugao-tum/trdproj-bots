#!/usr/bin/env python3
import argparse
import csv
import json
import math
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import requests

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
ENTRIES = ROOT / "bots" / "quant" / "entries"
CACHE = OUT / "_cache" / "url_status.json"
URL_CSV = OUT / "url_status.csv"
DUPES_CSV = OUT / "dupes.csv"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
URL_RE = re.compile(r"https?://[^\s\"'`，。；：！？、）】」』》]+")
TRAIL = ".,;:!?，。；：！？、）】」』》"


def parse_entry(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = {}
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines[:20]):
        if line.strip() == "---":
            start = i
            break
    if start is not None:
        for j in range(start + 1, min(len(lines), start + 80)):
            if lines[j].strip() == "---":
                for line in lines[start + 1 : j]:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        fm[k.strip()] = v.strip()
                break
    if "id" not in fm:
        m = re.search(r"^id:\s*(.+)$", text, re.M)
        if m:
            fm["id"] = m.group(1).strip()
    fm["_path"] = str(path.relative_to(ROOT))
    fm["_text"] = text
    fm["_name"] = fm.get("name_zh") or path.stem
    return fm


def extract_urls(text):
    found = []
    for m in URL_RE.finditer(text):
        u = m.group(0)
        while u and u[-1] in TRAIL:
            u = u[:-1]
        while u.endswith(")") and u.count("(") < u.count(")"):
            u = u[:-1]
        while u.endswith("]") and u.count("[") < u.count("]"):
            u = u[:-1]
        if u:
            found.append(u)
    seen = set()
    out = []
    for u in found:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def is_template(u):
    if any(ch in u for ch in "{}<>"):
        return True
    if "..." in u or "…" in u:
        return True
    if "|" in u:
        return True
    if re.search(r"(?:^|[?&])(token_id|market|slug|q|page|offset|starttime|endtime|articleCode)=$", u):
        return True
    if re.search(r"(?:page|offset|start|end|from|to)=[^&]*(?:\.\.|/|,|…)", u):
        return True
    if re.search(r"(?:limit|offset|page)=(?:N|K)(?:&|$)", u):
        return True
    if re.search(r"/f1/(?:N|K)(?:/|$)", u):
        return True
    if u.endswith("/..."):
        return True
    return False


def normalize_url(u):
    try:
        p = urlsplit(u)
        scheme = p.scheme.lower()
        host = p.netloc.lower()
        path = p.path.rstrip("/") or "/"
        q = sorted(parse_qsl(p.query, keep_blank_values=True))
        return urlunsplit((scheme, host, path, urlencode(q), ""))
    except Exception:
        return u


GENERIC_PREFIXES = (
    "https://data.binance.vision/",
    "https://gamma-api.polymarket.com/public-search",
    "https://gamma-api.polymarket.com/tags",
    "https://gamma-api.polymarket.com/events?tag_slug=",
    "https://gamma-api.polymarket.com/events?series_id=",
    "https://clob.polymarket.com/prices-history?market=",
    "https://data-api.polymarket.com/trades?market=",
    "https://docs.polymarket.com/",
    "https://web.archive.org/",
    "https://archive.org/",
    "https://api.github.com/repos/",
    "https://raw.githubusercontent.com/",
    "https://www.sec.gov/Archives/edgar/data/",
)


def is_specific_url(u):
    n = normalize_url(u)
    if is_template(u) or re.search(r"%3[cC]|%3[eE]|[{}<>]|\.\.\.|…|\|", n):
        return False
    for p in GENERIC_PREFIXES:
        if n.startswith(p):
            if p in (
                "https://gamma-api.polymarket.com/events?tag_slug=",
                "https://clob.polymarket.com/prices-history?market=",
                "https://data-api.polymarket.com/trades?market=",
            ) and re.search(r"(?:slug|market|token_id)=[^&/]+", n):
                return True
            return False
    return True


def classify(status, error):
    if status is None:
        e = (error or "").lower()
        if "name or service not known" in e or "nodename nor servname" in e:
            return "dead"
        return "manual"
    if 200 <= status < 400:
        return "alive"
    if status in (404, 410):
        return "dead"
    if status in (401, 403, 407, 429, 451, 503):
        return "manual"
    if 500 <= status < 600:
        return "manual"
    return "manual"


def fetch_url(url, retries=1, timeout=20):
    last = None
    for attempt in range(retries + 1):
        sess = requests.Session()
        started = time.time()
        try:
            r = sess.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True, stream=True)
            status = r.status_code
            final = r.url
            try:
                r.close()
            except Exception:
                pass
            return {
                "http_status": status,
                "final_url": final,
                "error": "",
                "seconds": round(time.time() - started, 3),
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        except requests.exceptions.SSLError as e:
            last = ("SSL: " + str(e).splitlines()[0])[:300]
        except requests.exceptions.Timeout as e:
            last = ("Timeout: " + str(e).splitlines()[0])[:300]
        except requests.exceptions.ConnectionError as e:
            last = ("ConnectionError: " + str(e).splitlines()[0])[:300]
        except requests.exceptions.RequestException as e:
            last = (type(e).__name__ + ": " + str(e).splitlines()[0])[:300]
        finally:
            try:
                sess.close()
            except Exception:
                pass
        if attempt < retries:
            time.sleep(1)
    return {
        "http_status": None,
        "final_url": "",
        "error": last or "unknown error",
        "seconds": 0,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def load_cache():
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


def first_commit(path):
    if not path:
        return ""
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%cI", "--reverse", "--", path],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )
        lines = [x for x in out.stdout.splitlines() if x.strip()]
        return lines[0] if lines else ""
    except Exception:
        return ""


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def tokens(s):
    s = (s or "").lower()
    words = re.findall(r"[a-z][a-z0-9\-]{2,}", s)
    zh = "".join(re.findall(r"[\u4e00-\u9fff]", s))
    grams = [zh[i : i + 2] for i in range(max(0, len(zh) - 1))]
    return Counter(words + grams)


def mechanism_text(e):
    parts = [e.get("name_zh", ""), e.get("name_en", "")]
    text = e.get("_text", "")
    for h in ("一句话", "钱从哪里来", "规则"):
        m = re.search(r"##\s*" + h + r"\s*\n(.*?)(?=\n## |\Z)", text, re.S)
        if m:
            parts.append(m.group(1)[:2500])
    return " ".join(parts)


def build_weights(docs):
    df = Counter()
    for d in docs:
        for t in set(tokens(d)):
            df[t] += 1
    n = max(1, len(docs))
    return {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}


def vec(text, weights):
    c = tokens(text)
    return {t: (1 + math.log(v)) * weights.get(t, 1.0) for t, v in c.items()}


def cosine(a, b):
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0.0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def word_set(s):
    return set(re.findall(r"[a-z0-9][a-z0-9\-]{1,}", (s or "").lower()))


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def field_sim(a, b):
    s = 0.0
    if a.get("market") and a.get("market") == b.get("market"):
        s += 0.35
    ac = a.get("pm_category", "")
    bc = b.get("pm_category", "")
    if ac and ac != "-" and ac == bc:
        s += 0.25
    s += 0.20 * jaccard(word_set(a.get("venues")), word_set(b.get("venues")))
    s += 0.20 * jaccard(word_set(a.get("instruments")), word_set(b.get("instruments")))
    return s


def url_sets(e):
    raw = [u for u in extract_urls(e.get("_text", "")) if not is_template(u)]
    allu = set(normalize_url(u) for u in raw)
    spec = set(u for u in allu if is_specific_url(u))
    return allu, spec


def gate_status(text):
    m = re.search(r"##\s*门槛自查\s*\n(.*?)(?=\n## |\Z)", text, re.S)
    if not m:
        return [], []
    rows = []
    flags = []
    for line in m.group(1).splitlines():
        g = re.match(r"\s*(\d)[\.、]\s*(.*)", line)
        if not g:
            continue
        num = int(g.group(1))
        rest = g.group(2)
        sm = re.search(r"(不满足|不确定|满足)", rest)
        status = sm.group(1) if sm else "未写"
        rows.append((num, status, rest.strip()))
        if status in ("不满足", "不确定"):
            flags.append((num, status, rest.strip()))
    return rows, flags


def gate6_admissions(text):
    pats = [
        r"凑不[到够]",
        r"(?:不足|不到|少于|低于|至多|最多|只能)[^。\n]{0,25}30",
        r"30[^。\n]{0,25}(?:未证|不够|不能保证|不可|拿不到|凑不)",
        r"(?:拿不到|补不到|取不到)[^。\n]{0,25}30",
        r"30\s*个[^。\n]{0,25}(?:约需|需要|要|得)",
        r"两周[^。\n]{0,40}(?:最多|只有|约)\s*\d+",
        r"每周\s*\d+\s*个",
    ]
    hits = []
    for line in text.splitlines():
        for p in pats:
            if re.search(p, line):
                hits.append(line.strip())
                break
    return hits


def load_known():
    p = ROOT / "known" / "KNOWN.md"
    out = []
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([A-Za-z]-[^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if not m:
            continue
        kid = m.group(1).strip()
        name = m.group(2).strip()
        if kid == "编号":
            continue
        out.append(
            {
                "id": kid,
                "name_zh": name,
                "name_en": "",
                "bot": "known",
                "market": "",
                "pm_category": "",
                "instruments": "",
                "venues": "",
                "kind": "known",
                "improves": "-",
                "status": "known",
                "_path": "known/KNOWN.md",
                "_text": name,
                "_name": name,
            }
        )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    quant = [parse_entry(p) for p in sorted(ENTRIES.glob("*.md"))]
    pending = [e for e in quant if e.get("status") == "待核"]
    drafts = [e for e in quant if e.get("status") == "草稿"]

    print("== quant 条目状态 ==")
    print(f"待核: {len(pending)}")
    for e in pending:
        print(f"  {e.get('id'):10s} {e.get('market'):12s} {e.get('pm_category'):10s} {e.get('kind'):11s} {e.get('name_zh')}")
    print(f"草稿: {len(drafts)}")
    for e in drafts:
        print(f"  {e.get('id'):10s} {e.get('market'):12s} {e.get('pm_category'):10s} {e.get('kind'):11s} {e.get('name_zh')}")

    print("\n== 门槛自查扫描（待核） ==")
    for e in pending:
        rows, flags = gate_status(e.get("_text", ""))
        adm = gate6_admissions(e.get("_text", ""))
        print(f"  {e.get('id')}: " + ("; ".join(f"{n}:{s}" for n, s, _ in flags) if flags else "全部满足"))
        for h in adm:
            print(f"    <30证据> {h[:180]}")

    url_rows = []
    to_fetch = {}
    for e in pending:
        for u in extract_urls(e.get("_text", "")):
            if is_template(u):
                url_rows.append(
                    {
                        "entry_id": e.get("id"),
                        "url": u,
                        "http_status": "",
                        "final_url": "",
                        "error": "template placeholder; not requested",
                        "class": "template",
                    }
                )
            else:
                to_fetch.setdefault(u, None)

    cache = load_cache()
    todo = [u for u in to_fetch if args.refresh or u not in cache]
    print(f"\n== 出处抓取 ==")
    print(f"模板 URL 行数: {len(url_rows)}; 唯一非模板 URL: {len(to_fetch)}; 需抓取: {len(todo)}")
    if todo:
        done = 0
        with ThreadPoolExecutor(max_workers=10) as ex:
            futs = {ex.submit(fetch_url, u): u for u in todo}
            for fut in as_completed(futs):
                u = futs[fut]
                try:
                    cache[u] = fut.result()
                except Exception as exc:
                    cache[u] = {
                        "http_status": None,
                        "final_url": "",
                        "error": f"{type(exc).__name__}: {exc}",
                        "seconds": 0,
                        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                done += 1
                if done % 20 == 0 or done == len(todo):
                    print(f"  抓取进度 {done}/{len(todo)}")
        save_cache(cache)
    else:
        print("  全部命中缓存")

    for e in pending:
        for u in extract_urls(e.get("_text", "")):
            if is_template(u):
                continue
            rec = cache.get(u, {})
            cls = classify(rec.get("http_status"), rec.get("error"))
            url_rows.append(
                {
                    "entry_id": e.get("id"),
                    "url": u,
                    "http_status": rec.get("http_status", ""),
                    "final_url": rec.get("final_url", ""),
                    "error": rec.get("error", ""),
                    "class": cls,
                }
            )

    order = {e.get("id"): i for i, e in enumerate(pending)}
    url_rows.sort(key=lambda r: (order.get(r["entry_id"], 99), r["class"], r["url"]))
    with URL_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["entry_id", "url", "http_status", "final_url", "error", "class"])
        w.writeheader()
        w.writerows(url_rows)

    print("\n== 出处存活汇总 ==")
    print("entry,urls,alive,dead,manual,template")
    for e in pending:
        rows = [r for r in url_rows if r["entry_id"] == e.get("id")]
        c = Counter(r["class"] for r in rows)
        print(
            f"{e.get('id')},{len(rows)},{c['alive']},{c['dead']},{c['manual']},{c['template']}"
        )
    print(f"CSV: {URL_CSV.relative_to(ROOT)}")

    print("\n== 死链/需人工复核明细 ==")
    for e in pending:
        rows = [r for r in url_rows if r["entry_id"] == e.get("id") and r["class"] in ("dead", "manual")]
        if rows:
            print(f"  {e.get('id')}:")
            for r in rows:
                st = r["http_status"] if r["http_status"] != "" else "-"
                err = (r["error"] or "")[:100]
                print(f"    [{r['class']}] {st} {r['url'][:160]} {err}")

    corpus_other = []
    bots_dir = ROOT / "bots"
    for d in sorted(bots_dir.iterdir()):
        if not d.is_dir() or d.name == "quant":
            continue
        edir = d / "entries"
        if not edir.exists():
            continue
        for p in sorted(edir.glob("*.md")):
            e = parse_entry(p)
            if "id" not in e:
                e["id"] = p.stem
            corpus_other.append(e)
    corpus_other += quant
    known = load_known()

    all_docs = corpus_other + known
    weights = build_weights([mechanism_text(e) for e in all_docs])
    qvecs = {e["id"]: vec(mechanism_text(e), weights) for e in pending}
    ovecs = {id(e): vec(mechanism_text(e), weights) for e in corpus_other + known}
    urls_cache = {}

    def urls_for(e):
        key = id(e)
        if key not in urls_cache:
            urls_cache[key] = url_sets(e)
        return urls_cache[key]

    cands = []
    for q in pending:
        uq_all, uq_spec = urls_for(q)
        qid = q.get("id")
        for o in corpus_other + known:
            if o is q:
                continue
            oid = o.get("id")
            if o.get("bot") == "quant" and oid == qid:
                continue
            ts = cosine(qvecs[qid], ovecs[id(o)])
            fs = field_sim(q, o)
            uo_all, uo_spec = urls_for(o)
            shared = sorted(uq_spec & uo_spec)
            us = jaccard(uq_spec, uo_spec)
            score = 0.55 * ts + 0.30 * fs + 0.15 * us
            exact_improve = q.get("improves") not in ("", "-", None) and q.get("improves") == oid
            if exact_improve:
                score = max(score, 0.75)
            if score >= 0.24 or shared or exact_improve:
                cands.append(
                    {
                        "quant_entry": qid,
                        "other_entry": oid,
                        "other_bot": o.get("bot"),
                        "other_path": o.get("_path"),
                        "score": round(score, 4),
                        "text_sim": round(ts, 4),
                        "field_sim": round(fs, 4),
                        "url_sim": round(us, 4),
                        "shared_urls": " ; ".join(shared[:3]),
                        "exact_improve": "yes" if exact_improve else "",
                        "other_name": o.get("name_zh") or "",
                    }
                )

    by_q = {}
    for c in cands:
        by_q.setdefault(c["quant_entry"], []).append(c)
    selected = []
    for q in pending:
        qid = q.get("id")
        rows = sorted(by_q.get(qid, []), key=lambda x: (-x["score"], x["other_entry"]))
        keep = rows[:6]
        for r in rows:
            if r["exact_improve"] == "yes" and r not in keep:
                keep.append(r)
        for i, r in enumerate(keep, 1):
            r["rank"] = i
            selected.append(r)

    for r in selected:
        r["first_commit_quant"] = first_commit(next((e.get("_path") for e in pending if e.get("id") == r["quant_entry"]), ""))
        r["first_commit_other"] = first_commit(r["other_path"])
        a, b = parse_ts(r["first_commit_quant"]), parse_ts(r["first_commit_other"])
        if a and b:
            r["earlier"] = "quant" if a < b else ("other" if b < a else "same")
        elif a:
            r["earlier"] = "quant"
        elif b:
            r["earlier"] = "other"
        else:
            r["earlier"] = "unknown"

    fields = [
        "quant_entry",
        "rank",
        "other_entry",
        "other_bot",
        "other_name",
        "score",
        "text_sim",
        "field_sim",
        "url_sim",
        "shared_urls",
        "exact_improve",
        "first_commit_quant",
        "first_commit_other",
        "earlier",
        "other_path",
    ]
    selected.sort(key=lambda r: (order[r["quant_entry"]], r["rank"]))
    with DUPES_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in selected:
            w.writerow({k: r.get(k, "") for k in fields})

    print("\n== 查重候选（每待核条目 top 6，含 improves 定向） ==")
    for q in pending:
        qid = q.get("id")
        rows = [r for r in selected if r["quant_entry"] == qid]
        print(f"  {qid}:")
        for r in rows:
            print(
                f"    {r['score']:.3f} {r['other_entry']:32s} bot={r['other_bot']:6s} "
                f"text={r['text_sim']:.2f} field={r['field_sim']:.2f} "
                f"shared={r['shared_urls'][:80]} early={r['earlier']}"
            )
    print(f"CSV: {DUPES_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
