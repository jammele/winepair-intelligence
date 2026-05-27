"""
Google Search Console connector.

Uses a service account key (not OAuth tokens) so it can run unattended
in GitHub Actions without interactive login.

Setup: See SETUP.md → Step 2: Google Search Console
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def _get_service(key_file: str):
    if not GOOGLE_AVAILABLE:
        raise ImportError("google-api-python-client not installed. Run: pip install -r requirements.txt")
    if not os.path.exists(key_file):
        raise FileNotFoundError(
            f"Service account key not found at {key_file}. "
            "See SETUP.md → Step 2 for instructions."
        )
    credentials = service_account.Credentials.from_service_account_file(
        key_file, scopes=SCOPES
    )
    return build("webmasters", "v3", credentials=credentials, cache_discovery=False)


def fetch_pages(site_url: str, key_file: str, lookback_days: int = 28,
                row_limit: int = 500) -> list[dict]:
    """Fetch page-level GSC performance data."""
    service = _get_service(key_file)
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=lookback_days)

    response = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["page"],
            "rowLimit": row_limit,
        }
    ).execute()

    return [
        {
            "page": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": row.get("ctr", 0.0),
            "position": row.get("position", 0.0),
            "lookback_days": lookback_days,
        }
        for row in response.get("rows", [])
    ]


def fetch_queries(site_url: str, key_file: str, lookback_days: int = 28,
                  row_limit: int = 1000) -> list[dict]:
    """Fetch query-level GSC performance data."""
    service = _get_service(key_file)
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=lookback_days)

    response = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["query"],
            "rowLimit": row_limit,
        }
    ).execute()

    return [
        {
            "query": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": row.get("ctr", 0.0),
            "position": row.get("position", 0.0),
            "lookback_days": lookback_days,
        }
        for row in response.get("rows", [])
    ]


def collect_all(site_url: str, key_file: str, lookback_windows: list[int] = None) -> dict:
    """Run all GSC collections across all configured lookback windows."""
    if lookback_windows is None:
        lookback_windows = [7, 28, 91, 365]

    results = {"pages": [], "queries": []}

    for days in lookback_windows:
        results["pages"].extend(fetch_pages(site_url, key_file, lookback_days=days))
        results["queries"].extend(fetch_queries(site_url, key_file, lookback_days=days))

    return results
