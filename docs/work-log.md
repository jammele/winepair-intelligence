# Work Log — Wine Pair Content Intelligence Engine

**Last updated:** 2026-05-26 (Session 1 — mid-session update)

---

## Immediate next actions

1. **Reopen terminal and verify Python** — Python 3.13 was just installed. Close and reopen the Claude Code terminal, then run `! python --version` to confirm it's recognized.
2. **Run setup check** — once Python is confirmed: `! cd C:\Users\jamme\winepair-intelligence && python setup_check.py`. This verifies GSC credentials are working end-to-end.
3. **Get YouTube Data API key** — `SETUP.md` Step 3. Takes ~5 min. Same Google Cloud project.
4. **Add GitHub Actions secrets** — `SETUP.md` Step 5b. Five secrets total. Required for automated weekly runs.
5. **Enable GitHub Actions write permissions** — repo Settings → Actions → General → Workflow permissions → "Read and write permissions."
6. **Apply for Google Trends API alpha** — https://developers.google.com/search/apis/trends. Takes 5 min to apply; approval takes weeks. Apply now so we're in queue for Phase 4.

---

## Credential setup — current status

| Item | Status | Notes |
|---|---|---|
| Google Cloud project | ✅ Done | Project: winepair-intelligence |
| Service account created | ✅ Done | |
| Service account key downloaded | ✅ Done | Renamed to `config/service_account.json` |
| Search Console access granted | ✅ Done | Service account added as Restricted user |
| `.env` file created | ✅ Done | All paths set; YouTube key blank until Step 3 |
| Python installed | ✅ Done | Python 3.13.13 — needs terminal restart to activate |
| `pip install -r requirements.txt` | ❌ Not yet | Run after terminal restart |
| `python setup_check.py` | ❌ Not yet | Run after pip install |
| YouTube API key | ❌ Not yet | Next step after setup check passes |
| GitHub Actions secrets | ❌ Not yet | After YouTube key |
| GitHub Actions write permissions | ❌ Not yet | After secrets |

---

## Active project — Phase 1: GSC + Content Inventory + Report

**Phase 0 is complete.** Phase 1 begins once setup check passes.

Phase 1 deliverables:
- GSC data flowing into SQLite (pages + queries, all 4 lookback windows)
- Website content inventory scrape (sitemap + WordPress REST API → `content_items` table)
- Weekly Markdown + HTML report generator (`src/reporting/report.py`)
- End-to-end test: `python run_weekly_report.py` produces a real report with real data

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
- Documentation system: `docs/work-log.md`, `docs/roadmap.md`, `docs/decisions.md`

**Credential setup completed this session:**
- Google Cloud project created
- Service account created, key downloaded, renamed to `config/service_account.json`
- Search Console access granted to service account
- `.env` file created with all paths configured
- Python 3.13 installed (terminal restart required to activate)

**Repo:** https://github.com/jammele/winepair-intelligence
**Local path:** `C:\Users\jamme\winepair-intelligence\`

---

## Reference

- BRD source: `C:\Users\jamme\Downloads\WinePair_Content_Intelligence_BRD.md`
- podcast-os work log entry: `C:\Users\jamme\podcast-os\docs\work-log.md` (section: Content Intelligence Engine)
- Related memory: `C:\Users\jamme\.claude\projects\C--Users-jamme-podcast-os\memory\project_content_intelligence_engine.md`
