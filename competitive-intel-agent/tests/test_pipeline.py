import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import diff
import digest
import fetch
import send_email


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def items_snapshot(sid, urls, kind="links", company="TestCo"):
    return {"id": sid, "company": company, "kind": kind, "url": "https://x.test",
            "items": [{"url": u, "title": u} for u in urls]}


def text_snapshot(sid, lines, company="TestCo"):
    return {"id": sid, "company": company, "kind": "page_text", "url": "https://x.test",
            "lines": lines}


# ---------- diff ----------

def test_diff_new_item_is_reported():
    new = items_snapshot("s", ["https://x.test/a", "https://x.test/b"])
    old = items_snapshot("s", ["https://x.test/a"])
    changes = diff.diff_items(new, old, {})
    assert [c["type"] for c in changes] == ["new_item"]
    assert changes[0]["url"] == "https://x.test/b"


def test_diff_sitemap_removals_are_ignored():
    new = items_snapshot("s", ["https://x.test/a"], kind="sitemap")
    old = items_snapshot("s", ["https://x.test/a", "https://x.test/gone"], kind="sitemap")
    assert diff.diff_items(new, old, {}) == []


def test_diff_ignore_list_filters_noise():
    new = items_snapshot("s", ["https://x.test/topic/foo"], kind="sitemap")
    old = items_snapshot("s", [], kind="sitemap")
    assert diff.diff_items(new, old, {"ignore_contains": ["/topic/"]}) == []


def test_diff_caps_new_items_per_source():
    urls = [f"https://x.test/{i}" for i in range(20)]
    changes = diff.diff_items(items_snapshot("s", urls, kind="sitemap"),
                              items_snapshot("s", [], kind="sitemap"), {})
    assert sum(c["type"] == "new_item" for c in changes) == diff.MAX_NEW_PER_SOURCE
    assert changes[-1]["type"] == "many_items"


def test_diff_text_detects_added_line():
    old_lines = [f"line {i}" for i in range(30)]
    old_hashes = [fetch.line_hash(line) for line in old_lines]
    changes = diff.diff_text(old_lines + ["a brand new line"], old_hashes)
    assert changes[0]["type"] == "text_added"
    assert "a brand new line" in changes[0]["lines"]


def test_diff_text_flags_redesign_instead_of_listing_everything():
    old_hashes = [fetch.line_hash(f"old {i}") for i in range(10)]
    new_lines = [f"new {i}" for i in range(10)]
    assert diff.diff_text(new_lines, old_hashes)[0]["type"] == "large_text_change"


def test_diff_text_counts_removed_lines_without_storing_them():
    old_lines = [f"line {i}" for i in range(30)]
    old_hashes = [fetch.line_hash(line) for line in old_lines]
    changes = diff.diff_text(old_lines[:-1], old_hashes)
    assert changes[0]["type"] == "text_removed" and changes[0]["lines"] == []


def test_diff_reads_older_snapshot_format():
    assert diff.old_hashes({"lines": ["a"]}) == [fetch.line_hash("a")]


def test_saved_snapshot_never_contains_page_text(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "LATEST", tmp_path / "latest")
    monkeypatch.setattr(fetch, "PREVIOUS", tmp_path / "previous")
    monkeypatch.setattr(fetch, "TEXT_CACHE", tmp_path / "text")
    fetch.save_snapshot({"id": "s", "company": "C", "kind": "page_text",
                         "url": "https://x.test", "lines": ["secret competitor sentence"]})
    committed = (tmp_path / "latest" / "s.json").read_text()
    assert "secret competitor sentence" not in committed
    assert "line_hashes" in committed
    assert "secret competitor sentence" in (tmp_path / "text" / "s.json").read_text()


def test_diff_ignores_failed_source(tmp_path, monkeypatch):
    monkeypatch.setattr(diff, "LATEST", tmp_path / "latest")
    monkeypatch.setattr(diff, "PREVIOUS", tmp_path / "previous")
    monkeypatch.setattr(diff, "RUN_LOG", tmp_path / "runs.jsonl")
    monkeypatch.setattr(diff, "CHANGES_FILE", tmp_path / "changes.json")
    monkeypatch.setattr(diff, "CONFIG", {"good": {}, "bad": {}})
    for sid, extra in (("good", "https://x.test/new"), ("bad", "https://x.test/new-but-failed")):
        write(tmp_path / "previous" / f"{sid}.json", items_snapshot(sid, ["https://x.test/a"]))
        write(tmp_path / "latest" / f"{sid}.json", items_snapshot(sid, ["https://x.test/a", extra]))
    (tmp_path / "runs.jsonl").write_text(json.dumps({"results": [
        {"id": "good", "status": "ok"}, {"id": "bad", "status": "FAILED"}]}) + "\n")
    diff.main()
    changes = json.loads((tmp_path / "changes.json").read_text())["changes"]
    assert {c["source_id"] for c in changes} == {"good"}


# ---------- fetch ----------

def test_fetch_normalize_removes_noise():
    assert fetch.normalize("https://x.test/a/?utm=1#top") == "https://x.test/a"


def test_fetch_failed_source_does_not_overwrite_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "LATEST", tmp_path / "latest")
    monkeypatch.setattr(fetch, "PREVIOUS", tmp_path / "previous")
    monkeypatch.setattr(fetch, "RUN_LOG", tmp_path / "runs.jsonl")
    monkeypatch.setattr(fetch, "SOURCES", [{"id": "s", "company": "C", "kind": "page_text",
                                            "url": "https://x.test"}])
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    good = tmp_path / "latest" / "s.json"
    write(good, {"marker": "good snapshot"})

    def boom(url):
        raise RuntimeError("network down")
    monkeypatch.setattr(fetch, "http_get", boom)

    with pytest.raises(SystemExit) as exit_info:
        fetch.main()
    assert exit_info.value.code == 1
    assert json.loads(good.read_text())["marker"] == "good snapshot"
    assert "FAILED" in (tmp_path / "runs.jsonl").read_text()


# ---------- digest ----------

def test_digest_threshold_filters_low_importance():
    assert digest.is_notable({"notable": True, "importance": 5})
    assert digest.is_notable({"notable": True, "importance": digest.MIN_IMPORTANCE})
    assert not digest.is_notable({"notable": True, "importance": 2})
    assert not digest.is_notable({"notable": False, "importance": 5})
    assert not digest.is_notable({"notable": True, "importance": "high"})
    assert not digest.is_notable({})


def test_digest_parse_json_handles_wrapped_reply():
    assert digest.parse_json('Sure:\n```json\n{"items": []}\n```') == {"items": []}
    with pytest.raises(Exception):
        digest.parse_json("no json here")


def test_digest_renders_failures_and_never_invents_links():
    change = {"company": "Gong", "source_id": "g", "source_url": "https://src.test",
              "url": "https://real.test/page", "title": "t", "type": "new_item"}
    assessment = {"what_changed": "Something", "importance": 4, "why_it_matters": "Because",
                  "suggested_action": "Act", "notable": True}
    out = digest.render("2026-01-01", "summary", [(change, assessment)], [], [],
                        [{"id": "broken", "note": "404"}], 0)
    assert "https://real.test/page" in out
    assert "## Source problems" in out and "broken" in out


def test_digest_refuses_stale_changes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(digest, "CHANGES_FILE", tmp_path / "changes.json")
    write(tmp_path / "changes.json", {"detected_at": "2020-01-01T00:00:00+00:00", "changes": []})
    with pytest.raises(SystemExit):
        digest.main()


# ---------- send_email ----------

def test_send_email_refuses_old_digest(tmp_path, monkeypatch):
    monkeypatch.setattr(send_email, "DIGEST_DIR", tmp_path)
    (tmp_path / "2020-01-01.md").write_text("old news")
    with pytest.raises(SystemExit):
        send_email.todays_digest()


def test_send_email_finds_todays_digest(tmp_path, monkeypatch):
    monkeypatch.setattr(send_email, "DIGEST_DIR", tmp_path)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (tmp_path / f"{today}.md").write_text("today")
    assert send_email.todays_digest().name == f"{today}.md"