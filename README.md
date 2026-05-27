# Wine Pair Content Intelligence & Performance Engine

A weekly automated intelligence system for The Wine Pair Podcast. Tracks what's trending, what's working, and what to create next — using owned data, official APIs, and public RSS feeds.

---

## What it does

Every week, the system:

1. Pulls Google Search Console data (pages, queries, trends)
2. Crawls the website content inventory
3. Checks YouTube for new videos on watchlist topics
4. Scans wine industry and SEO news via RSS feeds
5. Stores everything in a local SQLite database (never overwrites — always appends)
6. Generates a weekly Markdown + HTML report with trend analysis and recommendations

After a few weeks of runs, the system can tell you whether a topic is a new spike, a slow riser, a stable evergreen, seasonal, or declining — and why.

---

## What it outputs

A weekly report structured around:

- **Owned performance** — GSC, podcast downloads (Phase 3), social (Phase 3)
- **SEO/AEO review** — gaining/declining pages, high-impression/low-click opportunities
- **Content coverage and gaps** — what's covered, what's missing, where clusters are weak
- **Trend intelligence** — week-over-week movement for every watchlist topic
- **External signals** — YouTube, news, industry RSS
- **Brand and retailer watchlist** — direct targets, adjacent opportunities, watch-only
- **Recommendations** — episode ideas, blog ideas, social hooks, content refreshes

Each recommendation includes evidence, interpretation, the Wine Pair angle, and a confidence score.

---

## What it does NOT do

- Does not scrape behind logins
- Does not use fake accounts
- Does not require paid subscriptions
- Does not invent data or fake trend confidence
- Does not recommend off-brand topics just because they are trending
- Does not describe The Wine Pair Podcast as a blind tasting podcast

---

## Project status

| Phase | Status | What it covers |
|---|---|---|
| Phase 0 | **Done** | Project structure, config, docs |
| Phase 1 | In progress | GSC + content inventory + SQLite + report |
| Phase 2 | Not started | YouTube + RSS + trend scoring v1 |
| Phase 3 | Not started | Buzzsprout + Instagram |
| Phase 4 | Not started | Google Trends API + Reddit |
| Phase 5 | Not started | Dashboard + charts |

---

## Quick start

```
pip install -r requirements.txt
pip install pyyaml
cp .env.example .env
# Fill in your credentials in .env
python setup_check.py
python run_weekly_report.py --dry-run
```

See `SETUP.md` for full setup instructions.

---

## Running manually

```
python run_weekly_report.py              # Full run
python run_weekly_report.py --dry-run   # Collect data, skip report
python run_weekly_report.py --skip-gsc  # Skip GSC (for testing)
```

---

## Automated weekly runs

The system runs automatically every Monday at 9 AM Pacific via GitHub Actions.

The SQLite database is committed back to this repo after each run, accumulating trend history over time. Reports are saved to `reports/`.

See `SCHEDULER_SETUP.md` and `SETUP.md → Step 5` for configuration.

---

## Files and folders

```
config/          — watchlists, source config, settings
data/sqlite/     — SQLite trend database (committed to repo)
reports/         — generated Markdown and HTML reports
src/connectors/  — GSC, YouTube, RSS, website connectors
src/analysis/    — trend scoring and gap analysis
src/reporting/   — report generation
docs/            — additional documentation
run_weekly_report.py  — main run script
setup_check.py        — setup verifier
```

---

## Documentation

| File | Purpose |
|---|---|
| `docs/work-log.md` | **Start here.** Current status, immediate next actions, session history. |
| `docs/roadmap.md` | Phase-by-phase plan with acceptance criteria and data source status. |
| `docs/decisions.md` | Locked architectural decisions and the reasoning behind each one. |
| `SETUP.md` | Step-by-step credential setup guide (non-technical). |
| `SECURITY.md` | What credentials are used, how to rotate or revoke them. |
| `TROUBLESHOOTING.md` | Common errors and fixes. |

## Credentials and security

See `SECURITY.md`. The short version: service account keys and API keys go in `config/` and `.env` — both are gitignored. GitHub Actions reads them from repository secrets.
