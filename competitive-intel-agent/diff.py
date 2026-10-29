import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from fetch import line_hash
from sources import SOURCES

LATEST = Path("snapshots/latest")
PREVIOUS = Path("snapshots/previous")
TEXT_CACHE = Path("snapshots/text")
RUN_LOG = Path("runs.jsonl")
CHANGES_FILE = Path("changes.json")
LAYOUT_CHANGE_RATIO = 0.5   # if more than half the page changed, flag a probable layout change
MAX_LINES_KEPT = 100
MAX_NEW_PER_SOURCE = 8
CONFIG = {s["id"]: s for s in SOURCES}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sources_ok_in_last_run():
    # Only compare sources fetched successfully in the latest run. A failed fetch
    # leaves old snapshots in place, and comparing those would repeat old news.
    last = json.loads(RUN_LOG.read_text(encoding="utf-8").strip().splitlines()[-1])
    return [r["id"] for r in last["results"] if r["status"] == "ok"]


def old_hashes(old):
    if "line_hashes" in old:
        return old["line_hashes"]
    return [line_hash(line) for line in old.get("lines", [])]   # older snapshot format


def diff_items(new, old, config):
    ignore = config.get("ignore_contains", [])
    old_urls = {i["url"] for i in old["items"]}
    new_urls = {i["url"] for i in new["items"]}
    added = [i for i in new["items"]
             if i["url"] not in old_urls and not any(s in i["url"] for s in ignore)]
    changes = [{"type": "new_item", "url": i["url"], "title": i.get("title", "")}
               for i in added[:MAX_NEW_PER_SOURCE]]
    if len(added) > MAX_NEW_PER_SOURCE:
        changes.append({"type": "many_items", "count": len(added) - MAX_NEW_PER_SOURCE})
    if new["kind"] != "sitemap":   # removed pages only matter for press and release lists
        for i in old["items"]:
            if i["url"] not in new_urls:
                changes.append({"type": "removed_item", "url": i["url"], "title": i.get("title", "")})
    return changes


def diff_text(new_lines, old_hash_list):
    old_set = set(old_hash_list)
    new_set = {line_hash(line) for line in new_lines}
    added = [line for line in new_lines if line_hash(line) not in old_set]
    removed = len(old_set - new_set)
    if not added and not removed:
        return []
    ratio = (len(added) + removed) / max(len(old_set), 1)
    if ratio > LAYOUT_CHANGE_RATIO:
        return [{"type": "large_text_change", "added": len(added), "removed": removed}]
    changes = []
    if added:
        changes.append({"type": "text_added", "total": len(added), "lines": added[:MAX_LINES_KEPT]})
    if removed:
        changes.append({"type": "text_removed", "total": removed, "lines": []})
    return changes


def main():
    if not RUN_LOG.exists():
        print("No run log found. Run fetch.py first.")
        sys.exit(1)

    all_changes, baseline = [], []
    for source_id in sources_ok_in_last_run():
        new_path, old_path = LATEST / f"{source_id}.json", PREVIOUS / f"{source_id}.json"
        if not old_path.exists():
            baseline.append(source_id)
            continue
        new, old = load(new_path), load(old_path)
        if new["kind"] == "page_text":
            text_path = TEXT_CACHE / f"{source_id}.json"
            if not text_path.exists():
                sys.exit(f"Missing page text for {source_id}. Run fetch.py first.")
            changes = diff_text(load(text_path)["lines"], old_hashes(old))
        else:
            changes = diff_items(new, old, CONFIG[source_id])
        for c in changes:
            c.update({"source_id": source_id, "company": new["company"], "source_url": new["url"]})
        all_changes.extend(changes)

    CHANGES_FILE.write_text(json.dumps({
        "detected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "baseline_only": baseline,
        "changes": all_changes,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    if baseline:
        print("First snapshot only (nothing to compare yet):", ", ".join(baseline))
    if not all_changes:
        print("No changes detected.")
        return
    print(f"{len(all_changes)} change(s) detected:\n")
    for c in all_changes:
        label = f"[{c['company']}] {c['source_id']}: {c['type']}"
        if c["type"] in ("new_item", "removed_item"):
            print(label, "-", c["title"][:70] or c["url"])
        elif c["type"] == "many_items":
            print(label, f"({c['count']} more new pages not listed)")
        elif c["type"] == "text_added":
            print(label, f"({c['total']} lines) e.g. {c['lines'][0][:70]}")
        elif c["type"] == "text_removed":
            print(label, f"({c['total']} lines removed)")
        else:
            print(label, f"(added {c['added']}, removed {c['removed']}: probable layout change)")


if __name__ == "__main__":
    main()