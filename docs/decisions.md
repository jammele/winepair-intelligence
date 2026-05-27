# Architecture Decisions — Wine Pair Content Intelligence Engine

Locked decisions. Do not re-litigate without new data that changes the analysis.

---

## Language: Python

**Decision:** Python for the entire system.

**Why:** This is fundamentally a data pipeline. Python's ecosystem (feedparser, google-api-python-client, SQLAlchemy, Jinja2, Pandas when needed) is significantly stronger than Node.js for this use case. The existing podcast-os codebase is Node.js, but language coupling between the two systems is not needed — the only integration point is a file handoff (the weekly report).

**Implication:** Python 3.11+ required. Run `pip install -r requirements.txt` to install all dependencies.

---

## Repository: Separate from podcast-os

**Decision:** `jammele/winepair-intelligence` — a standalone GitHub repo, not a subdirectory of podcast-os.

**Why:** This system has its own dependencies, scheduler, credentials, and release cadence. It will grow to be substantial. Keeping it out of podcast-os prevents both repos from becoming unwieldy.

**Integration point:** The weekly report file is saved to a path that the podcast-os session-startup hook reads. That's the only coupling between the two systems.

---

## Scheduling: GitHub Actions cron

**Decision:** GitHub Actions, running every Monday at 9 AM Pacific (17:00 UTC).

**Why:** Joe's machine often sleeps or is off. Windows Task Scheduler fails silently when the machine is off. GitHub Actions runs in the cloud regardless of machine state.

**Cron:** `0 17 * * 1`

**Manual trigger:** Available via GitHub Actions UI (Actions → Weekly Intelligence Report → Run workflow) and via `python run_weekly_report.py` locally.

---

## GSC Authentication: Service account key (not OAuth token)

**Decision:** Google Cloud service account with a JSON key file.

**Why:** OAuth tokens expire and require interactive re-authorization — not compatible with automated GitHub Actions runs. Service account keys don't expire and can be stored as GitHub secrets. The service account is granted "Restricted" read-only access to the Search Console property.

**Security:** The key file (`config/service_account.json`) is gitignored. In GitHub Actions, the full JSON content is stored as the `GSC_SERVICE_ACCOUNT_JSON` secret and written to a temp file that is deleted before any git commit.

---

## Database: SQLite, append-only, committed to repo

**Decision:** SQLite at `data/sqlite/intelligence.db`, committed to the repository after each run.

**Why:**
- SQLite is built into Python — no separate database server to manage or pay for.
- Committing the `.db` file to the repo is the simplest way to persist trend history across GitHub Actions runs (no external storage service needed).
- Append-only design means every source record is timestamped and never overwritten. Trend scores are derived by comparing current week to prior N-week windows. This is the core architecture that makes week-over-week trend analysis possible.

**Note:** SQLite files compress well. Revisit this decision if the DB grows unwieldy (unlikely for years at weekly granularity).

---

## Trend-first architecture

**Decision:** The database is the system. The weekly report is a product of the database, not the system itself.

**Why:** A topic that spikes once is "noisy." A topic that rises steadily over 8 weeks is a "slow riser." The system cannot tell the difference without history. Building trend analysis as a core primitive (not a future feature) means the system earns its value automatically over time — it just needs to run.

**Implication for schema:** Every source record has a `run_id` and `collected_at`. The `topic_snapshots` table stores one row per topic per run. The `trend_scores` table computes labels from `topic_snapshots` history. Both tables grow every week. Neither is ever cleared.

**Implication for timing:** Every week the system does NOT run is a week of trend history that will never exist. Start Phase 1 as early as possible.

---

## Report integration with podcast-os

**Decision:** The weekly report summary will be injected into the podcast-os session-startup hook alongside the work log.

**Why:** Every podcast-os session currently opens with Claude reconstructing the same context from scratch. A weekly intelligence briefing at session start — 3-5 lines summarizing what moved this week, what's worth acting on, and what to watch — would make every session faster and better-informed.

**Implementation (Phase 1):** The GitHub Actions workflow saves the weekly report to a path that the podcast-os `scripts/hooks/session-startup.js` reads. The startup hook includes a summary line in its output. No code coupling between the two repos — just a shared file path.

---

## What is NOT in scope (non-goals from BRD)

- No spreadsheet maintenance
- No paid subscriptions (ever, for v1)
- No scraping behind logins
- No fake accounts
- No captcha bypassing
- No inventing data or fake trend confidence
- No off-brand recommendations just because something is trending
- No describing The Wine Pair Podcast as a blind tasting podcast
