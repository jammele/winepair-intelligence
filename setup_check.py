#!/usr/bin/env python3
"""
Wine Pair Content Intelligence Engine — Setup Verifier

Checks that all required dependencies and credentials are in place.
Run this after initial setup to verify everything is working before the first report.

Usage: python setup_check.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

PASS = "  [PASS]"
FAIL = "  [FAIL]"
SKIP = "  [SKIP]"
WARN = "  [WARN]"


def check(label: str, ok: bool, fix: str = "", warn_only: bool = False) -> bool:
    symbol = PASS if ok else (WARN if warn_only else FAIL)
    print(f"{symbol} {label}")
    if not ok and fix:
        print(f"        Fix: {fix}")
    return ok


def section(title: str):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def main():
    print("\nWine Pair Content Intelligence Engine — Setup Check")
    print(f"Python {sys.version}")

    all_ok = True

    # --- Python packages ---
    section("Python Dependencies")

    def pkg(name, import_name=None):
        nonlocal all_ok
        import_name = import_name or name
        try:
            __import__(import_name)
            check(f"{name} installed", True)
        except ImportError:
            ok = check(f"{name} installed", False,
                       fix=f"Run: pip install -r requirements.txt")
            all_ok = False

    pkg("python-dotenv", "dotenv")
    pkg("requests")
    pkg("google-api-python-client", "googleapiclient")
    pkg("google-auth", "google.oauth2")
    pkg("feedparser")
    pkg("beautifulsoup4", "bs4")
    pkg("lxml")
    pkg("Jinja2", "jinja2")
    pkg("PyYAML", "yaml")

    # --- Environment variables ---
    section("Environment Variables (.env)")

    gsc_key_path = os.getenv("GSC_SERVICE_ACCOUNT_KEY", "config/service_account.json")
    gsc_site = os.getenv("GSC_SITE_URL", "")
    youtube_key = os.getenv("YOUTUBE_API_KEY", "")

    if not check("GSC_SERVICE_ACCOUNT_KEY set", bool(gsc_key_path),
                 fix="Add GSC_SERVICE_ACCOUNT_KEY=config/service_account.json to .env"):
        all_ok = False

    if not check("GSC_SITE_URL set", bool(gsc_site),
                 fix="Add GSC_SITE_URL=https://thewinepairpodcast.com/ to .env"):
        all_ok = False

    check("YOUTUBE_API_KEY set", bool(youtube_key),
          fix="Add YOUTUBE_API_KEY=... to .env (required for YouTube data)",
          warn_only=True)

    # --- Files and directories ---
    section("Files and Directories")

    if not check("config/service_account.json exists", Path(gsc_key_path).exists(),
                 fix="See SETUP.md → Step 2: Create a Google Cloud service account and download the JSON key to config/service_account.json"):
        all_ok = False

    check("config/watchlist.yaml exists", Path("config/watchlist.yaml").exists())
    check("config/sources.yaml exists", Path("config/sources.yaml").exists())
    check("config/settings.yaml exists", Path("config/settings.yaml").exists())

    for folder in ["data/sqlite", "data/raw", "reports/markdown", "reports/html", "logs"]:
        Path(folder).mkdir(parents=True, exist_ok=True)
        check(f"{folder}/ writable", os.access(folder, os.W_OK))

    # --- GSC connection ---
    section("Google Search Console API")

    if Path(gsc_key_path).exists() and gsc_site:
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            creds = service_account.Credentials.from_service_account_file(
                gsc_key_path,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
            )
            service = build("webmasters", "v3", credentials=creds, cache_discovery=False)
            sites = service.sites().list().execute()
            site_urls = [s["siteUrl"] for s in sites.get("siteEntry", [])]

            if gsc_site in site_urls or gsc_site.rstrip("/") in [s.rstrip("/") for s in site_urls]:
                check(f"GSC access to {gsc_site}", True)
            else:
                check(f"GSC access to {gsc_site}", False,
                      fix=f"Grant the service account 'Restricted' access to {gsc_site} in Google Search Console → Settings → Users and permissions")
                all_ok = False
        except Exception as e:
            check("GSC API connection", False, fix=f"Error: {e}")
            all_ok = False
    else:
        print(f"{SKIP} GSC API check skipped (missing credentials or site URL)")

    # --- YouTube API ---
    section("YouTube Data API")

    if youtube_key:
        try:
            import requests
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={"part": "id", "q": "test", "maxResults": 1, "key": youtube_key},
                timeout=10
            )
            if resp.status_code == 200:
                check("YouTube API key valid", True)
            else:
                check("YouTube API key valid", False,
                      fix=f"HTTP {resp.status_code}: {resp.json().get('error', {}).get('message', 'Unknown error')}")
                all_ok = False
        except Exception as e:
            check("YouTube API connection", False, fix=str(e))
    else:
        print(f"{SKIP} YouTube API check skipped (YOUTUBE_API_KEY not set)")

    # --- RSS feeds ---
    section("RSS Feed Access")

    try:
        import feedparser
        test = feedparser.parse("https://www.decanter.com/feed/")
        check("Decanter RSS feed accessible", bool(test.entries),
              fix="Check your internet connection")
    except Exception as e:
        check("RSS feed access", False, fix=str(e))

    # --- Website sitemap ---
    section("Website Sitemap")

    sitemap_url = os.getenv("SITEMAP_URL", "https://thewinepairpodcast.com/sitemap_index.xml")
    try:
        import requests
        resp = requests.get(sitemap_url, timeout=10)
        check(f"Sitemap accessible ({sitemap_url})", resp.status_code == 200,
              fix=f"Check SITEMAP_URL in .env — got HTTP {resp.status_code}")
    except Exception as e:
        check("Sitemap accessible", False, fix=str(e))

    # --- Summary ---
    print("\n" + "=" * 50)
    if all_ok:
        print("  All required checks passed. Ready to run.")
        print("  Run: python run_weekly_report.py")
    else:
        print("  Some checks failed. Fix the issues above before running.")
        print("  See SETUP.md for detailed instructions.")
    print("=" * 50 + "\n")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
