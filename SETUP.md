# Setup Guide — Wine Pair Content Intelligence Engine

This guide walks through every step to get the system running. No coding experience required.

---

## Overview of what you need

1. A Google Cloud project (free) with a service account
2. The service account granted access to your Search Console property
3. A YouTube Data API key (free, same Google Cloud project)
4. A GitHub repository for this project (runs the weekly job automatically)
5. Python 3.11+ installed locally (for setup verification and manual runs)

Total setup time: about 45 minutes.

---

## Step 1: Create a Google Cloud Project

You already have a Google account. You need a Google Cloud project.

1. Go to https://console.cloud.google.com
2. Click the project dropdown at the top → **New Project**
3. Name it `winepair-intelligence` (or anything you like)
4. Click **Create**
5. Wait for the project to be created, then select it

---

## Step 2: Create a Service Account for Google Search Console

A service account is a special kind of Google account that a program uses to authenticate. Unlike your personal OAuth tokens, service account keys do not expire — which is why we use them for automated weekly runs.

### 2a. Enable the Search Console API

1. In Google Cloud Console, go to **APIs & Services → Library**
2. Search for "Google Search Console API"
3. Click it → **Enable**

### 2b. Create the service account

1. Go to **IAM & Admin → Service Accounts**
2. Click **+ Create Service Account**
3. Name: `winepair-intelligence`
4. Description: `Weekly content intelligence pipeline`
5. Click **Create and Continue**
6. Skip the optional role assignment steps → **Done**

### 2c. Download the service account key

1. Click on the service account you just created
2. Go to the **Keys** tab
3. **Add Key → Create new key → JSON**
4. A JSON file will download to your computer
5. Move it to `config/service_account.json` inside this project folder
   - **Never commit this file to git** (it's already in `.gitignore`)

### 2d. Grant the service account access to Search Console

1. Go to https://search.google.com/search-console
2. Select your property (`thewinepairpodcast.com`)
3. Go to **Settings → Users and permissions**
4. Click **+ Add user**
5. Enter the service account email (looks like `winepair-intelligence@your-project.iam.gserviceaccount.com`)
6. Set permission to **Restricted**
7. Click **Add**

---

## Step 3: Create a YouTube Data API Key

1. In Google Cloud Console, go to **APIs & Services → Library**
2. Search for "YouTube Data API v3"
3. Click it → **Enable**
4. Go to **APIs & Services → Credentials**
5. Click **+ Create Credentials → API key**
6. Copy the key
7. Optionally: click **Restrict Key** → restrict to YouTube Data API v3 only

---

## Step 4: Set up this project locally

### 4a. Install Python 3.11+

Download from https://www.python.org/downloads/ if not already installed.

Verify: open a terminal and run `python --version`

### 4b. Install dependencies

```
pip install -r requirements.txt
pip install pyyaml  # also needed
```

### 4c. Create your .env file

Copy `.env.example` to `.env`:

```
cp .env.example .env
```

Open `.env` and fill in:

```
GSC_SERVICE_ACCOUNT_KEY=config/service_account.json
GSC_SITE_URL=https://thewinepairpodcast.com/
YOUTUBE_API_KEY=your-key-here
SITEMAP_URL=https://thewinepairpodcast.com/sitemap_index.xml
DB_PATH=data/sqlite/intelligence.db
```

### 4d. Verify the setup

```
python setup_check.py
```

All required checks should pass before you run the first report.

---

## Step 5: Set up GitHub for automated weekly runs

### 5a. Push the project to GitHub

The repository should already exist at https://github.com/jammele/winepair-intelligence

```
git remote add origin https://github.com/jammele/winepair-intelligence.git
git push -u origin main
```

### 5b. Add secrets to GitHub

Go to your GitHub repository → **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

| Secret name | Value |
|---|---|
| `GSC_SERVICE_ACCOUNT_JSON` | The full JSON content of `config/service_account.json` |
| `GSC_SITE_URL` | `https://thewinepairpodcast.com/` |
| `YOUTUBE_API_KEY` | Your YouTube API key |
| `SITEMAP_URL` | `https://thewinepairpodcast.com/sitemap_index.xml` |

To get the JSON content: open `config/service_account.json` in a text editor and copy the entire contents.

### 5c. Test the GitHub Actions workflow

1. Go to your GitHub repository
2. Click **Actions → Weekly Intelligence Report**
3. Click **Run workflow → Run workflow**
4. Watch the run complete (takes 2-5 minutes)
5. Check that the database and reports were committed back to the repo

---

## Step 6: Apply for Google Trends API alpha access (do this now)

The Google Trends API is waitlisted. Apply now so you're in the queue for Phase 4.

- Application: https://developers.google.com/search/apis/trends

Takes about 5 minutes to apply. Approval can take weeks.

---

## Manual runs

To run the report manually from your computer:

```
python run_weekly_report.py               # Full run
python run_weekly_report.py --dry-run     # Collect data only, no report
python run_weekly_report.py --skip-gsc    # Skip GSC (for testing other sources)
```

---

## Troubleshooting

See `TROUBLESHOOTING.md` for common error messages and fixes.
