#!/usr/bin/env python3
"""
Wine Pair Content Intelligence Engine — Weekly Report Runner

Usage:
  python run_weekly_report.py              # Run for today
  python run_weekly_report.py --run-now   # Alias for immediate run
  python run_weekly_report.py --date 2026-05-26  # Run for a specific date (historical)
  python run_weekly_report.py --dry-run   # Collect data but skip report generation
"""

import argparse
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import database
from src.connectors import gsc, youtube, rss, website
from src.analysis import trends
from src.reporting import report as reporter


def parse_args():
    p = argparse.ArgumentParser(description="Run the Wine Pair weekly intelligence report")
    p.add_argument("--run-now", action="store_true", help="Run immediately")
    p.add_argument("--date", help="Run for a specific date (YYYY-MM-DD)")
    p.add_argument("--dry-run", action="store_true", help="Collect data but skip report generation")
    p.add_argument("--skip-gsc", action="store_true", help="Skip GSC collection (for testing)")
    p.add_argument("--skip-youtube", action="store_true", help="Skip YouTube collection")
    p.add_argument("--skip-rss", action="store_true", help="Skip RSS collection")
    p.add_argument("--skip-website", action="store_true", help="Skip website inventory crawl")
    return p.parse_args()


def load_watchlist(watchlist_path: str = "config/watchlist.yaml") -> list[dict]:
    try:
        import yaml
        with open(watchlist_path) as f:
            data = yaml.safe_load(f)
    except ImportError:
        # yaml not installed — use a basic parser fallback or require it
        raise ImportError("PyYAML not installed. Run: pip install pyyaml")

    topics = []
    for category, items in data.items():
        for item in (items or []):
            topics.append({
                "name": item["name"],
                "topic_type": item.get("topic_type", category.rstrip("s")),
                "brand_tier": item.get("brand_tier"),
                "adjacent_angle": item.get("adjacent_angle"),
            })
    return topics


def ensure_topics_in_db(db_path: str, topics: list[dict]) -> dict[str, int]:
    """Insert any missing topics into the topics table. Returns name→id map."""
    conn = database.get_connection(db_path)
    now = datetime.utcnow().isoformat()
    topic_ids = {}
    with conn:
        for t in topics:
            existing = conn.execute(
                "SELECT id FROM topics WHERE name = ?", (t["name"],)
            ).fetchone()
            if existing:
                topic_ids[t["name"]] = existing["id"]
            else:
                cursor = conn.execute(
                    """INSERT INTO topics (name, topic_type, brand_tier, adjacent_angle, added_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (t["name"], t["topic_type"], t.get("brand_tier"), t.get("adjacent_angle"), now)
                )
                topic_ids[t["name"]] = cursor.lastrowid
    conn.close()
    return topic_ids


def store_gsc_data(db_path: str, run_id: int, pages: list[dict], queries: list[dict]) -> None:
    conn = database.get_connection(db_path)
    now = datetime.utcnow().isoformat()
    with conn:
        for page in pages:
            conn.execute(
                """INSERT INTO gsc_pages (run_id, collected_at, lookback_days, page,
                   clicks, impressions, ctr, position)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, now, page["lookback_days"], page["page"],
                 page["clicks"], page["impressions"], page["ctr"], page["position"])
            )
        for query in queries:
            conn.execute(
                """INSERT INTO gsc_queries (run_id, collected_at, lookback_days, query,
                   clicks, impressions, ctr, position)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, now, query["lookback_days"], query["query"],
                 query["clicks"], query["impressions"], query["ctr"], query["position"])
            )
    conn.close()


def store_youtube_data(db_path: str, run_id: int, topic_id: int,
                       videos: list[dict]) -> None:
    conn = database.get_connection(db_path)
    now = datetime.utcnow().isoformat()
    with conn:
        for v in videos:
            conn.execute(
                """INSERT INTO youtube_results (run_id, topic_id, collected_at, video_id,
                   title, channel_name, published_at, view_count, like_count,
                   comment_count, description_snippet)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, topic_id, now, v["video_id"], v["title"], v["channel_name"],
                 v["published_at"], v["view_count"], v["like_count"],
                 v["comment_count"], v["description_snippet"])
            )
    conn.close()


def store_rss_items(db_path: str, run_id: int, items: list[dict],
                    source_type: str) -> None:
    conn = database.get_connection(db_path)
    now = datetime.utcnow().isoformat()
    with conn:
        for item in items:
            conn.execute(
                """INSERT INTO rss_items (run_id, collected_at, source_name, source_type,
                   title, url, published_at, summary, topics_matched)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, now, item["source_name"], source_type,
                 item["title"], item["url"], item["published_at"],
                 item["summary"], json.dumps(item["topics_matched"]))
            )
    conn.close()


def main():
    args = parse_args()

    db_path = os.getenv("DB_PATH", "data/sqlite/intelligence.db")
    gsc_key = os.getenv("GSC_SERVICE_ACCOUNT_KEY", "config/service_account.json")
    gsc_site = os.getenv("GSC_SITE_URL", "https://thewinepairpodcast.com/")
    youtube_key = os.getenv("YOUTUBE_API_KEY", "")
    sitemap_url = os.getenv("SITEMAP_URL", "https://thewinepairpodcast.com/sitemap_index.xml")

    print("=" * 60)
    print("Wine Pair Content Intelligence Engine")
    print(f"Run started: {datetime.utcnow().isoformat()}")
    print("=" * 60)

    # Initialize DB
    database.initialize_schema(db_path)
    run_id = database.start_run(db_path)
    print(f"Run ID: {run_id}")

    topics = load_watchlist()
    topic_ids = ensure_topics_in_db(db_path, topics)
    topic_names = [t["name"] for t in topics]
    print(f"Watchlist: {len(topics)} topics loaded")

    errors = []

    # --- GSC ---
    if not args.skip_gsc:
        print("\n[1/4] Collecting Google Search Console data...")
        try:
            gsc_data = gsc.collect_all(gsc_site, gsc_key)
            store_gsc_data(db_path, run_id, gsc_data["pages"], gsc_data["queries"])
            total = len(gsc_data["pages"]) + len(gsc_data["queries"])
            database.record_source_status(db_path, run_id, "gsc", "success", records=total)
            print(f"  GSC: {len(gsc_data['pages'])} page records, {len(gsc_data['queries'])} query records")
        except Exception as e:
            database.record_source_status(db_path, run_id, "gsc", "failed", error=str(e))
            errors.append(f"GSC: {e}")
            print(f"  GSC FAILED: {e}")
    else:
        print("\n[1/4] GSC skipped (--skip-gsc)")

    # --- YouTube ---
    if not args.skip_youtube and youtube_key:
        print("\n[2/4] Collecting YouTube data...")
        yt_total = 0
        for topic in topics:
            if topic.get("brand_tier") == "watch_only":
                continue
            try:
                videos = youtube.search_topic(topic["name"], youtube_key)
                if videos:
                    tid = topic_ids[topic["name"]]
                    store_youtube_data(db_path, run_id, tid, videos)
                    yt_total += len(videos)
            except Exception as e:
                errors.append(f"YouTube/{topic['name']}: {e}")
        database.record_source_status(db_path, run_id, "youtube", "success", records=yt_total)
        print(f"  YouTube: {yt_total} video records")
    else:
        reason = "--skip-youtube" if args.skip_youtube else "YOUTUBE_API_KEY not set"
        database.record_source_status(db_path, run_id, "youtube", "skipped", error=reason)
        print(f"\n[2/4] YouTube skipped ({reason})")

    # --- RSS ---
    if not args.skip_rss:
        print("\n[3/4] Collecting RSS feed data...")
        import yaml
        with open("config/sources.yaml") as f:
            sources_config = yaml.safe_load(f)

        for source_type, feeds in sources_config.get("rss_feeds", {}).items():
            items = rss.collect_all(feeds, topic_names)
            store_rss_items(db_path, run_id, items, source_type)
            print(f"  RSS/{source_type}: {len(items)} items")
        database.record_source_status(db_path, run_id, "rss", "success")
    else:
        print("\n[3/4] RSS skipped (--skip-rss)")

    # --- Website ---
    if not args.skip_website:
        print("\n[4/4] Crawling website content inventory...")
        try:
            urls = website.fetch_sitemap_urls(sitemap_url)
            print(f"  Sitemap: {len(urls)} URLs found")
            # TODO Phase 1: scrape each URL and store in content_items
            # For now, record the URL count
            database.record_source_status(db_path, run_id, "website", "partial",
                                           records=len(urls),
                                           error="Full page scrape not yet implemented (Phase 1)")
        except Exception as e:
            database.record_source_status(db_path, run_id, "website", "failed", error=str(e))
            errors.append(f"Website: {e}")
            print(f"  Website FAILED: {e}")
    else:
        print("\n[4/4] Website skipped (--skip-website)")

    # --- Complete run ---
    status = "completed" if not errors else "completed_with_errors"
    error_summary = "; ".join(errors) if errors else None
    database.complete_run(db_path, run_id, status=status, notes=error_summary)

    if not args.dry_run:
        print("\n[Reporting] Generating weekly report...")
        # TODO Phase 1: implement reporter.generate()
        print("  Report generation not yet implemented (Phase 1)")
    else:
        print("\n[Dry run] Skipping report generation")

    print("\n" + "=" * 60)
    print(f"Run {run_id} complete — status: {status}")
    if errors:
        print(f"Errors ({len(errors)}):")
        for err in errors:
            print(f"  - {err}")
    print("=" * 60)


if __name__ == "__main__":
    main()
