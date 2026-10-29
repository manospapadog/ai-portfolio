import hashlib
import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urldefrag

import requests
from bs4 import BeautifulSoup

from sources import SOURCES

HEADERS = {"User-Agent": "Mozilla/5.0 (personal portfolio project; weekly check)"}
LATEST = Path("snapshots/latest")
PREVIOUS = Path("snapshots/previous")
TEXT_CACHE = Path("snapshots/text")   # full page text for this run only; never committed
RUN_LOG = Path("runs.jsonl")


def line_hash(line):
    return hashlib.sha256(line.encode("utf-8")).hexdigest()[:16]


def normalize(url):
    """Drop #fragments, ?query strings and trailing slashes, so one page has one address."""
    url, _ = urldefrag(url)
    return url.split("?")[0].rstrip("/")


def http_get(url):
    last_error = None
    for _ in range(2):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return r
        except Exception as e:
            last_error = e
            time.sleep(2)
    raise last_error


def extract_page_text(r):
    soup = BeautifulSoup(r.content, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer"]):
        tag.decompose()
    lines = [" ".join(line.split()) for line in soup.get_text("\n").split("\n")]
    return {"lines": [line for line in lines if line]}


def extract_links(r, source):
    soup = BeautifulSoup(r.content, "html.parser")
    base = normalize(source["url"])
    items = {}
    for a in soup.find_all("a", href=True):
        href = normalize(urljoin(r.url, a["href"]))
        if href == base or not any(m in href for m in source["link_contains"]):
            continue
        title = " ".join(a.get_text(" ").split())
        if len(title) > len(items.get(href, "")):   # keep the longest text per URL
            items[href] = title
    return {"items": [{"url": u, "title": t[:200]} for u, t in items.items()]}


def extract_sitemap(r, source):
    urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", r.text)
    must = source.get("url_contains")
    if must:
        urls = [u for u in urls if must in u]
    urls = sorted(set(normalize(u) for u in urls))
    return {"is_index": "<sitemapindex" in r.text, "items": [{"url": u} for u in urls]}


def fetch_source(source):
    r = http_get(source["url"])
    kind = source["kind"]
    if kind == "page_text":
        data = extract_page_text(r)
        count, minimum = len(data["lines"]), 20
    elif kind == "links":
        data = extract_links(r, source)
        count, minimum = len(data["items"]), 1
    elif kind == "sitemap":
        data = extract_sitemap(r, source)
        count, minimum = len(data["items"]), 1
    else:
        raise ValueError(f"unknown kind: {kind}")

    if count < minimum:
        raise ValueError(f"suspiciously little content ({count}), keeping old snapshot")

    snapshot = {
        "id": source["id"],
        "company": source["company"],
        "kind": kind,
        "url": source["url"],
        "final_url": r.url,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **data,
    }
    note = []
    if normalize(r.url) != normalize(source["url"]):
        note.append(f"redirected to {r.url}")
    if data.get("is_index"):
        note.append("sitemap index (lists sub-sitemaps)")
    return snapshot, count, "; ".join(note)


def save_snapshot(snapshot):
    LATEST.mkdir(parents=True, exist_ok=True)
    PREVIOUS.mkdir(parents=True, exist_ok=True)
    TEXT_CACHE.mkdir(parents=True, exist_ok=True)
    snapshot = dict(snapshot)
    if "lines" in snapshot:
        # Page text is not stored in the committed snapshot: only a hash of each line.
        lines = snapshot.pop("lines")
        (TEXT_CACHE / f"{snapshot['id']}.json").write_text(
            json.dumps({"lines": lines}, ensure_ascii=False), encoding="utf-8")
        snapshot["line_hashes"] = [line_hash(line) for line in lines]
    path = LATEST / f"{snapshot['id']}.json"
    if path.exists():
        shutil.copy(path, PREVIOUS / path.name)
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    results = []
    for source in SOURCES:
        try:
            snapshot, count, note = fetch_source(source)
            save_snapshot(snapshot)
            results.append({"id": source["id"], "status": "ok", "count": count, "note": note})
        except Exception as e:
            results.append({"id": source["id"], "status": "FAILED", "count": 0, "note": str(e)[:150]})
        time.sleep(1)  # be polite: one request per second

    print(f"{'source':26} {'status':8} {'count':>6}  note")
    for r in results:
        print(f"{r['id']:26} {r['status']:8} {r['count']:>6}  {r['note']}")

    with RUN_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "results": results,
        }) + "\n")

    failed = [r for r in results if r["status"] != "ok"]
    if failed:
        print(f"\n{len(failed)} source(s) FAILED. Old snapshots were kept.")
        sys.exit(1)


if __name__ == "__main__":
    main()