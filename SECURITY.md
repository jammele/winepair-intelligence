# Security — Wine Pair Content Intelligence Engine

---

## What credentials this system uses

| Credential | Stored where | What it can do |
|---|---|---|
| Google service account key | `config/service_account.json` (local only) + GitHub secret | Read-only access to Search Console |
| YouTube API key | `.env` (local only) + GitHub secret | Read-only search queries |
| Buzzsprout API key (Phase 3) | `.env` (local only) + GitHub secret | Read-only podcast analytics |
| Reddit app credentials (Phase 4) | `.env` (local only) + GitHub secret | Read-only public posts |

---

## What is and is NOT committed to git

**Never committed:**
- `config/service_account.json`
- `.env`
- Any file matching `*.json` (credentials)

**Committed intentionally:**
- `config/watchlist.yaml`, `config/sources.yaml`, `config/settings.yaml`
- `data/sqlite/intelligence.db` (the trend database — contains no credentials)
- `reports/` (generated Markdown and HTML)

If you ever accidentally commit a credential:
1. Immediately revoke and rotate the key (instructions below)
2. Remove the file from git history using `git filter-branch` or BFG
3. Force-push (only acceptable case for force push on this repo)

---

## Rotating credentials

### Service account key

1. Google Cloud Console → IAM & Admin → Service Accounts
2. Select `winepair-intelligence` → Keys
3. Add Key → Create new key → JSON (download new key)
4. Delete the old key
5. Replace `config/service_account.json` with the new file
6. Update the `GSC_SERVICE_ACCOUNT_JSON` GitHub secret

### YouTube API key

1. Google Cloud Console → APIs & Services → Credentials
2. Delete the old key
3. Create a new API key
4. Update `.env` and the `YOUTUBE_API_KEY` GitHub secret

### Revoking access entirely

To remove all access for this system:

1. Delete the service account in Google Cloud Console
2. Remove the service account user from Search Console
3. Delete the YouTube API key
4. Delete all GitHub secrets

---

## Data that is collected and stored

**What is stored in the database:**
- GSC page and query performance data (impressions, clicks, CTR, position)
- YouTube video metadata (title, channel, view count, publish date)
- RSS feed article titles and summaries
- Website content inventory (URLs, titles, word counts, headings)
- Computed trend scores and recommendations

**What is NOT stored:**
- Social media user data or usernames (unless the user is a public creator being tracked by name, which requires explicit configuration)
- Passwords or login credentials of any kind
- Data collected behind authentication walls

---

## Source risk rules

This system is explicitly designed to avoid:
- Scraping behind logins (Instagram, TikTok, etc.)
- Automated browser behavior that could violate platform terms
- Fake accounts
- Captcha bypassing
- Collecting unnecessary personal information

If a source requires any of the above, it is not used. Unavailable sources are logged and noted in the report rather than worked around.
