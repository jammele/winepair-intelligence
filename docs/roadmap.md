# Roadmap — Wine Pair Content Intelligence Engine

The system gets more valuable over time. Week 1 is a snapshot. Week 4 shows trend direction. Week 12 shows seasonal patterns. **Start early.**

---

## Phase 0 — Project Scaffold ✅ COMPLETE (2026-05-26)

**Deliverables:**
- [x] Folder structure
- [x] SQLite schema (`src/database.py`) — append-only, timestamped
- [x] Connector skeletons (GSC, YouTube, RSS, website)
- [x] `run_weekly_report.py` — main entry point with flags
- [x] `setup_check.py` — verifier
- [x] GitHub Actions workflow (Monday cron + manual trigger)
- [x] Config files: `watchlist.yaml`, `sources.yaml`, `settings.yaml`
- [x] Docs: `README.md`, `SETUP.md`, `SECURITY.md`, `TROUBLESHOOTING.md`
- [x] Pushed to https://github.com/jammele/winepair-intelligence

**Acceptance criteria met:** Yes.

---

## Phase 1 — GSC + Content Inventory + Report ⏳ NOT STARTED

**Blocked on:** Joe completing credential setup (see `docs/work-log.md` → Immediate next actions).

**Deliverables:**
- [ ] GSC connector fully working — pulls pages + queries into `gsc_pages` / `gsc_queries` tables across all 4 lookback windows (7, 28, 91, 365 days)
- [ ] Website content inventory — sitemap crawl + WordPress REST API → `content_items` table (URL, title, content type, word count, headings, schema presence, links)
- [ ] Topic snapshot collection — maps GSC data to watchlist topics → `topic_snapshots` table
- [ ] Weekly Markdown report — all 9 sections from BRD Section 12
- [ ] Weekly HTML report — Jinja2 template, same content as Markdown
- [ ] `source_status` table populated — every run logs which sources succeeded, failed, or were skipped
- [ ] End-to-end test: `python run_weekly_report.py` produces a real report with real data
- [ ] podcast-os session-startup hook updated to inject intelligence report summary

**Acceptance criteria (from BRD Section 18):**
- Runs manually with one command ✓ (already works, needs real data)
- Pulls GSC data
- Crawls website content archive
- Stores data locally with dates
- Generates Markdown and HTML report
- Identifies high-impression/low-click opportunities
- Identifies content gaps
- Separates evidence from interpretation
- Saves historical data

---

## Phase 2 — YouTube + RSS + Trend Scoring ⏳ NOT STARTED

**Requires:** Phase 1 complete. YouTube API key set up (should be done in Phase 1 setup).

**Deliverables:**
- [ ] YouTube connector fully working — searches all non-watch-only watchlist topics, stores video metadata
- [ ] RSS connector fully working — fetches all configured feeds, tags matched topics
- [ ] Topic snapshots enriched with YouTube + RSS signals
- [ ] Trend scoring v1 — computes `trend_label` from `topic_snapshots` history (requires ≥3 weeks of data)
- [ ] Demand score, trend score, content gap score, Wine Pair fit score computed per topic
- [ ] Recommendations section in report populated with scored, evidence-backed suggestions
- [ ] Brand/retailer watchlist section in report (direct / adjacent / watch-only classification)

---

## Phase 3 — Podcast + Social Owned Performance ⏳ NOT STARTED

**Requires:** Phase 2 complete. Buzzsprout API key.

**Deliverables:**
- [ ] Buzzsprout API connector — episode downloads, first-7-day, first-30-day, lifetime
- [ ] Podcast performance mapped to topics (episode topic tags)
- [ ] Cross-channel analysis in report (which topics perform on search AND podcast AND social?)
- [ ] Instagram Insights integration (if Meta API access granted — may require app review)

**Notes:**
- Joe does not have a Buzzsprout API key as of 2026-05-26. Get it at: https://www.buzzsprout.com/app → API
- Instagram Insights requires Meta Business App approval — weeks-long process. Start that process before Phase 3 begins.

---

## Phase 4 — Google Trends + Reddit + Brand Intelligence ⏳ NOT STARTED

**Requires:** Phase 3 complete. Google Trends API alpha access (currently waitlisted). Reddit API credentials.

**Deliverables:**
- [ ] Google Trends API connector (waitlisted — apply now)
- [ ] Reddit connector — r/wine, r/Costco, r/traderjoes, r/aldi, r/frugal
- [ ] Adjacent opportunity detection — expensive brand trends → affordable alternative angles
- [ ] Topic cluster mapping
- [ ] Expanded scoring model (all 12 dimensions from BRD Section 11)

---

## Phase 5 — Dashboard + Automation Enhancements ⏳ NOT STARTED

**Requires:** Phases 1–4 producing consistent weekly data.

**Deliverables:**
- [ ] Visual dashboard (topic trend lines, performance tables, gap map)
- [ ] Report archive browser
- [ ] Email delivery of weekly report
- [ ] Long-term charts (Matplotlib or Plotly)
- [ ] Setup wizard improvements

---

## Data sources — access status

| Source | Phase | Status | Notes |
|---|---|---|---|
| Google Search Console | 1 | Blocked — needs service account | Follow SETUP.md Steps 1-2 |
| Website sitemap / WordPress API | 1 | Ready | Public, no auth |
| YouTube Data API | 2 | Blocked — needs API key | Follow SETUP.md Step 3 |
| RSS feeds | 2 | Ready | Public, no auth |
| Buzzsprout | 3 | Not set up | Get key at buzzsprout.com/app → API |
| Instagram Insights | 3 | Not set up | Requires Meta Business App review |
| Google Trends API | 4 | Waitlisted | Apply at https://developers.google.com/search/apis/trends |
| Reddit API | 4 | Not set up | Register at reddit.com/prefs/apps |
| TikTok Research API | 5 | Not available | Requires academic/institutional eligibility |
