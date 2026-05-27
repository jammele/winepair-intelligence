# Work Log — Wine Pair Content Intelligence Engine

**Last updated:** 2026-05-26 (Session 1)

---

## Immediate next actions (Joe must do these before Phase 1 can run)

1. **Set up Google Cloud service account** — follow `SETUP.md` Steps 1–2. Takes ~20 min. This is the primary blocker for all data collection.
2. **Get YouTube Data API key** — `SETUP.md` Step 3. Takes ~5 min. Same Google Cloud project.
3. **Add GitHub Actions secrets** — `SETUP.md` Step 5b. Five secrets total. Required for automated weekly runs.
4. **Enable GitHub Actions write permissions** — repo Settings → Actions → General → Workflow permissions → "Read and write permissions." Required for the workflow to commit the database back.
5. **Apply for Google Trends API alpha** — https://developers.google.com/search/apis/trends. Takes 5 min to apply; approval takes weeks. Apply now so we're in queue for Phase 4.

Once steps 1–4 are done: run `python setup_check.py` to verify, then trigger the first run manually via GitHub Actions (Actions tab → Weekly Intelligence Report → Run workflow).

---

## Active project — Phase 1: GSC + Content Inventory + Report

**Phase 0 is complete.** Phase 1 is the next build session.

Phase 1 deliverables:
- GSC data flowing into SQLite (pages + queries, all 4 lookback windows)
- Website content inventory scrape (sitemap + WordPress REST API → `content_items` table)
- Weekly Markdown + HTML report generator (`src/reporting/report.py`)
- End-to-end test: run `python run_weekly_report.py` and get a real report

**Phase 1 is blocked until Joe completes the credential setup above.**

---

## Session log

### Session 1 — 2026-05-26

**BRD reviewed.** Joe submitted `WinePair_Content_Intelligence_BRD.md`. Full analysis completed.

**Architecture decisions made:**
- Language: Python (data pipeline ecosystem stronger than Node.js for this use case)
- Location: Separate repo from podcast-os (`jammele/winepair-intelligence`)
- Scheduling: GitHub Actions cron (machine often sleeps — Task Scheduler unreliable)
- GSC auth: Service account key, not OAuth token (service account keys don't expire; compatible with GitHub Actions secrets)
- Report integration: Weekly report summary will be injected into podcast-os session-startup hook (Phase 1)
- DB strategy: SQLite committed to repo after each run — trend history accumulates automatically

**Phase 0 built and pushed:**
- Full folder structure
- SQLite schema (`src/database.py`) — append-only, timestamped from day one
- Connector skeletons: GSC, YouTube, RSS, website crawl
- `run_weekly_report.py` — main entry point
- `setup_check.py` — credential and dependency verifier
- GitHub Actions workflow (Monday 9 AM Pacific cron + manual trigger)
- Full config: `watchlist.yaml` (80+ topics from BRD), `sources.yaml`, `settings.yaml`
- Docs: `README.md`, `SETUP.md`, `SECURITY.md`, `TROUBLESHOOTING.md`

**Repo:** https://github.com/jammele/winepair-intelligence  
**Local path:** `C:\Users\jamme\winepair-intelligence\`

---

## Reference

- BRD source: `C:\Users\jamme\Downloads\WinePair_Content_Intelligence_BRD.md`
- podcast-os work log entry: `C:\Users\jamme\podcast-os\docs\work-log.md` (section: Content Intelligence Engine)
- Related memory: `C:\Users\jamme\.claude\projects\C--Users-jamme-podcast-os\memory\project_content_intelligence_engine.md`
