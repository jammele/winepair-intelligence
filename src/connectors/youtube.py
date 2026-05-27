"""
YouTube Data API connector.

Uses the YouTube Data API v3 to search for videos related to watchlist topics.
Respects quota by batching requests and limiting results per query.

Setup: See SETUP.md → Step 3: YouTube Data API
"""

import os
from datetime import datetime, timedelta
from typing import Optional

try:
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


def _get_service(api_key: str):
    if not GOOGLE_AVAILABLE:
        raise ImportError("google-api-python-client not installed.")
    return build("youtube", "v3", developerKey=api_key)


def search_topic(topic_name: str, api_key: str, max_results: int = 20,
                 published_after_days: int = 90) -> list[dict]:
    """Search YouTube for videos related to a topic."""
    service = _get_service(api_key)
    published_after = (datetime.utcnow() - timedelta(days=published_after_days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    search_response = service.search().list(
        q=f"{topic_name} wine",
        part="id,snippet",
        type="video",
        maxResults=max_results,
        publishedAfter=published_after,
        relevanceLanguage="en",
        order="relevance",
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
    if not video_ids:
        return []

    stats_response = service.videos().list(
        part="statistics",
        id=",".join(video_ids)
    ).execute()

    stats_by_id = {
        item["id"]: item.get("statistics", {})
        for item in stats_response.get("items", [])
    }

    results = []
    for item in search_response.get("items", []):
        vid_id = item["id"]["videoId"]
        stats = stats_by_id.get(vid_id, {})
        results.append({
            "video_id": vid_id,
            "title": item["snippet"]["title"],
            "channel_name": item["snippet"]["channelTitle"],
            "published_at": item["snippet"]["publishedAt"],
            "description_snippet": item["snippet"].get("description", "")[:300],
            "view_count": int(stats.get("viewCount", 0)),
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
        })

    return results
