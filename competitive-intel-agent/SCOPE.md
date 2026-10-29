# Competitive Intelligence Agent: Scope

## Purpose
Every week, check five competitors for meaningful changes and send the
commercial team a short digest: what changed, why it matters, and a
suggested action. Silence is a valid output when nothing important happened.

## Context
Built for Pipelane (fictional), which sells AI pipeline visibility and
deal-risk software to B2B SaaS revenue teams.

Competitors tracked: Gong, Salesloft (which now includes Clari), Aviso,
Terret (formerly BoostUp), Backstory (formerly People.ai).

## Sources (checked with a plain HTTP fetch, 27-28 Oct 2026)
| Company | Source | Detection method |
|---|---|---|
| Gong | help.gong.io release notes and monthly updates | New dated sections |
| Gong | gong.io/press, plus sitemap | New links compared with last run |
| Salesloft | community.salesloft.com/product-updates | New dated release notes |
| Aviso | aviso.com/press and aviso.com/blog | New links compared with last run |
| Terret | terret.ai homepage and sitemap | Text diff and new URLs |
| Backstory | backstory.ai homepage and sitemap | Text diff and new URLs |

Each source is saved as a snapshot every run, so the next run can detect change.

## Outputs
- A weekly email digest, ranked by importance, with a link for every claim
- A run log: what was checked, what was found, what failed
- Saved snapshots in the repo

## What counts as notable
Pricing or packaging changes, new features that overlap with Pipelane,
funding, acquisitions or leadership news, new integrations and partnerships,
and shifts in positioning. Ignore: minor wording edits, SEO blog posts,
awards and analyst-report mentions unless they change the competitive picture.

## Findings from the source check
- No competitor publishes list pricing. Pricing pages are demo forms or
  redirects, so pricing is recorded only as "page exists or not".
- Old addresses break after mergers: Clari's community and pricing URLs now
  redirect to Salesloft.
- Some press pages (Salesloft newsroom) load through JavaScript and cannot be
  read by a plain fetch, so they are out of scope.
- Aviso's blog publishes several posts a month, mostly SEO content, so
  relevance filtering matters more than collection.
- Sitemap "last modified" dates are unreliable (many pages share one
  timestamp), so new items are found by comparing URL lists between runs.

## Out of scope
Pricing monitoring, social media, paid data sources, pages behind a login,
pages that need a browser to render, and anything needing JavaScript.

## How it runs
Python script, scheduled weekly with GitHub Actions. API key stored as a
repository secret. Snapshots stored in the repo.

## How I will know it works
- Seed a known change into a snapshot and confirm it is reported
- Run with no changes and confirm the digest says so instead of inventing news
- Feed it a high-volume, low-value source (Aviso blog) and confirm it reports
  nothing notable
- Every claim in the digest links to its source
- A failed fetch is logged and reported, never silently skipped

## Known risks
- Pages change layout and break the parsing
- Raw page diffs are noisy (dates, tracking tokens, cookie banners)
- The model may over-report or invent significance
- Scheduled jobs fail quietly unless failures are surfaced
- Some sources may block scripts in future