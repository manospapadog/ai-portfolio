import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from fetch import http_get, extract_page_text

load_dotenv()
client = Anthropic()  # reads ANTHROPIC_API_KEY from .env

MODEL = "claude-sonnet-5"
CHANGES_FILE = Path("changes.json")
LATEST = Path("snapshots/latest")
RUN_LOG = Path("runs.jsonl")
DIGEST_DIR = Path("digests")
BAD_REPLY_FILE = Path("last_bad_reply.txt")
MAX_CHANGES = 40
BATCH_SIZE = 10
MIN_IMPORTANCE = 3
MAX_PAGE_CHARS = 12000
CONTEXT_LINES = 3
MAX_TOKENS = 8000

PROMPT_HEAD = """You are a competitive intelligence analyst for Pipelane, a company that sells AI pipeline visibility and deal-risk software to B2B SaaS revenue teams (RevOps leaders and VPs of Sales). The readers are Pipelane's commercial team.

Below are changes detected this week on public pages of Pipelane's competitors. Decide which ones the commercial team should know about.

Notable: pricing or packaging changes; new features or products that overlap with Pipelane's space (forecasting, pipeline inspection, deal risk); acquisitions, funding or leadership news; new integrations or partnerships; shifts in positioning.
Not notable: minor wording or layout edits; SEO or generic marketing blog posts; awards and analyst-report mentions unless they change the competitive picture; anything you cannot judge from the text provided.

Rules:
- Use only the text provided for each change. Do not use outside knowledge about these companies and do not guess.
- If the content is missing or too thin to judge, mark it not notable and say why.
- Be specific and brief. Never invent numbers, dates or features.

Changes:
"""

PROMPT_TAIL = """

Return ONLY valid JSON, with no markdown and no text around it, in exactly this shape:
{"items": [{"id": <the change number>, "notable": <true or false>, "importance": <1 to 5, where 5 means act now>, "what_changed": "<one sentence>", "why_it_matters": "<one or two sentences for Pipelane, or why it was skipped>", "suggested_action": "<one sentence, or an empty string if not notable>"}]}
Include every change exactly once. Keep every text field under 40 words. Do not use double quotes inside text fields; use single quotes instead."""


def page_excerpt(url):
    try:
        lines = extract_page_text(http_get(url))["lines"]
        return " ".join(lines)[:MAX_PAGE_CHARS] or "(page had no readable text)"
    except Exception:
        return "(content could not be fetched)"


def context_lines(source_id, added_lines):
    path = LATEST / f"{source_id}.json"
    if not path.exists():
        return ""
    lines = json.loads(path.read_text(encoding="utf-8")).get("lines", [])
    picked, seen = [], set()
    for added in added_lines[:5]:
        if added in lines:
            i = lines.index(added)
            for j in range(max(0, i - CONTEXT_LINES), min(len(lines), i + CONTEXT_LINES + 1)):
                if j not in seen:
                    seen.add(j)
                    picked.append(lines[j])
    return "\n".join(picked)


def describe(c):
    t = c["type"]
    if t == "new_item":
        return (f"A new page appeared. Title: {c.get('title') or '(none)'}\nURL: {c['url']}\n"
                f"Page content: {page_excerpt(c['url'])}")
    if t == "removed_item":
        return f"A page or link disappeared. Title: {c.get('title') or '(none)'}\nURL: {c['url']}"
    if t == "many_items":
        return (f"{c['count']} more new pages appeared on this source at once and are not listed. "
                "This usually means a site restructure or a batch of content.")
    if t == "text_added":
        return ("Lines added to the page:\n" + "\n".join(c["lines"][:15]) +
                "\n\nSurrounding text on the page:\n" + context_lines(c["source_id"], c["lines"]))
    if t == "text_removed":
        return "Lines removed from the page:\n" + "\n".join(c["lines"][:15])
    return (f"A large part of the page changed (added {c['added']}, removed {c['removed']} lines). "
            "This is probably a redesign, and the content is not shown.")


def parse_json(text):
    text = (text or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found")
    return json.loads(text[start:end + 1])


def ask_claude(prompt):
    last_error = None
    for _ in range(2):
        response = client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        text = next((b.text for b in response.content if b.type == "text"), None)
        try:
            if response.stop_reason == "max_tokens":
                raise ValueError("reply was cut off (max_tokens reached)")
            result = parse_json(text)
            if not isinstance(result.get("items"), list):
                raise ValueError("missing 'items' list")
            return result
        except Exception as e:
            last_error = e
            BAD_REPLY_FILE.write_text(
                f"stop_reason={response.stop_reason}\n\n{text}", encoding="utf-8")
    raise ValueError(f"Claude did not return valid JSON: {last_error} (see {BAD_REPLY_FILE})")


def assess(changes):
    """Ask Claude about the changes in batches. Returns {position in changes (1-based): item}."""
    assessed = {}
    for start in range(0, len(changes), BATCH_SIZE):
        batch = changes[start:start + BATCH_SIZE]
        blocks = [f"### Change {i}\nCompany: {c['company']}\nSource: {c['source_id']}\n"
                  f"Type: {c['type']}\n{describe(c)}" for i, c in enumerate(batch, 1)]
        try:
            result = ask_claude(PROMPT_HEAD + "\n\n".join(blocks) + PROMPT_TAIL)
        except Exception as e:
            print(f"Batch starting at change {start + 1} could not be assessed: {e}")
            continue
        for item in result["items"]:
            i = item.get("id")
            if isinstance(i, int) and 1 <= i <= len(batch) and (start + i) not in assessed:
                assessed[start + i] = item
    return assessed


def failed_sources():
    if not RUN_LOG.exists():
        return []
    last = json.loads(RUN_LOG.read_text(encoding="utf-8").strip().splitlines()[-1])
    return [r for r in last["results"] if r["status"] != "ok"]


def label(c):
    return c.get("title") or c.get("url") or c["source_id"]


def render(date, summary, notable, other, unassessed, failures, skipped):
    out = [f"# Competitive intelligence digest: {date}", "", summary, ""]
    if notable:
        out += ["## Worth your attention", ""]
        for n, (c, a) in enumerate(notable, 1):
            out += [f"### {n}. {c['company']}: {a['what_changed']} (importance {a['importance']}/5)",
                    f"- **Why it matters:** {a['why_it_matters']}",
                    f"- **Suggested action:** {a['suggested_action'] or 'None'}",
                    f"- **Source:** {c.get('url') or c['source_url']}", ""]
    if other:
        out += [f"## Checked, not notable ({len(other)})", ""]
        out += [f"- [{c['company']}] {label(c)[:80]}: {a['why_it_matters']}" for c, a in other]
        out.append("")
    if unassessed:
        out += ["## Not assessed by the model", ""]
        out += [f"- [{c['company']}] {label(c)[:80]}" for c in unassessed]
        out.append("")
    if skipped:
        out += [f"_{skipped} further change(s) were not reviewed (limit of {MAX_CHANGES} per run)._", ""]
    if failures:
        out += ["## Source problems", ""]
        out += [f"- {r['id']}: {r['note']}" for r in failures]
        out.append("")
    return "\n".join(out)


def is_notable(a):
    try:
        return bool(a.get("notable")) and int(a.get("importance", 0)) >= MIN_IMPORTANCE
    except (TypeError, ValueError):
        return False


def main():
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data = json.loads(CHANGES_FILE.read_text(encoding="utf-8"))
    if data.get("detected_at", "")[:10] != date:
        sys.exit("changes.json is not from today. Run diff.py first.")

    changes = data["changes"][:MAX_CHANGES]
    skipped = len(data["changes"]) - len(changes)
    failures = failed_sources()

    if not changes:
        digest = render(date, "No changes detected on any tracked source this week.",
                        [], [], [], failures, 0)
    else:
        assessed = assess(changes)
        notable = sorted(
            [(changes[i - 1], a) for i, a in assessed.items() if is_notable(a)],
            key=lambda pair: -int(pair[1]["importance"]))
        other = [(changes[i - 1], a) for i, a in assessed.items() if not is_notable(a)]
        unassessed = [c for i, c in enumerate(changes, 1) if i not in assessed]
        summary = (f"{len(changes)} change(s) reviewed across "
                   f"{len({c['source_id'] for c in changes})} source(s); "
                   f"{len(notable)} worth your attention.")
        digest = render(date, summary, notable, other, unassessed, failures, skipped)

    DIGEST_DIR.mkdir(exist_ok=True)
    path = DIGEST_DIR / f"{date}.md"
    path.write_text(digest, encoding="utf-8")
    print(digest)
    print(f"\nSaved to {path}")


if __name__ == "__main__":
    main()