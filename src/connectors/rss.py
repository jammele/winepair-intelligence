"""
RSS feed connector.

Fetches wine industry and SEO/AEO news from configured RSS feeds.
No auth required. Fails gracefully if a feed is unavailable.
"""

import re
from datetime import datetime
from typing import Optional

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False


def _extract_text(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html or "").strip()


def fetch_feed(source_name: str, url: str, topic_names: list[str],
               max_age_days: int = 14) -> list[dict]:
    """Fetch a single RSS feed and return items that match any watchlist topic."""
    if not FEEDPARSER_AVAILABLE:
        raise ImportError("feedparser not installed. Run: pip install -r requirements.txt")

    feed = feedparser.parse(url)
    if feed.bozo and not feed.entries:
        return []

    cutoff = None
    if max_age_days:
        cutoff = datetime.utcnow().timestamp() - (max_age_days * 86400)

    results = []
    for entry in feed.entries:
        published_ts = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            import calendar
            published_ts = calendar.timegm(entry.published_parsed)

        if cutoff and published_ts and published_ts < cutoff:
            continue

        title = entry.get("title", "")
        summary = _extract_text(entry.get("summary", ""))
        combined_text = (title + " " + summary).lower()

        matched = [t for t in topic_names if t.lower() in combined_text]

        results.append({
            "source_name": source_name,
            "title": title,
            "url": entry.get("link", ""),
            "published_at": entry.get("published", ""),
            "summary": summary[:500],
            "topics_matched": matched,
        })

    return results


def collect_all(feed_configs: list[dict], topic_names: list[str]) -> list[dict]:
    """Fetch all configured feeds, return combined results. Continues on failure."""
    all_items = []
    for feed in feed_configs:
        try:
            items = fetch_feed(
                source_name=feed["name"],
                url=feed["url"],
                topic_names=topic_names,
            )
            all_items.extend(items)
        except Exception as e:
            print(f"[RSS] Failed to fetch {feed['name']}: {e}")
    return all_items
