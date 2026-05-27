"""
SQLite database schema and connection management.

Design principle: append-only. Every source record is timestamped and never
overwritten. Trend scores are derived by comparing current week to prior N-week
windows. The schema supports this from day one.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path


def get_connection(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_schema(db_path: str) -> None:
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
            -- Each weekly pipeline execution
            CREATE TABLE IF NOT EXISTS runs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date        TEXT NOT NULL,          -- ISO date: 2026-05-26
                started_at      TEXT NOT NULL,
                completed_at    TEXT,
                status          TEXT DEFAULT 'running', -- running, completed, failed
                notes           TEXT
            );

            -- Owned content inventory (append-only: new row when content changes)
            CREATE TABLE IF NOT EXISTS content_items (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          INTEGER REFERENCES runs(id),
                collected_at    TEXT NOT NULL,
                url             TEXT NOT NULL,
                title           TEXT,
                meta_title      TEXT,
                meta_description TEXT,
                content_type    TEXT,                  -- episode, blog, resource, landing, other
                publish_date    TEXT,
                modified_date   TEXT,
                word_count      INTEGER,
                full_text       TEXT,
                headings        TEXT,                  -- JSON array
                wines_mentioned TEXT,                  -- JSON array
                varietals       TEXT,                  -- JSON array
                regions         TEXT,                  -- JSON array
                brands          TEXT,                  -- JSON array
                retailers       TEXT,                  -- JSON array
                internal_links  TEXT,                  -- JSON array
                external_links  TEXT,                  -- JSON array
                has_faq_schema  INTEGER DEFAULT 0,
                has_review_schema INTEGER DEFAULT 0
            );

            -- GSC page-level snapshots (one row per page per run)
            CREATE TABLE IF NOT EXISTS gsc_pages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          INTEGER REFERENCES runs(id),
                collected_at    TEXT NOT NULL,
                lookback_days   INTEGER NOT NULL,       -- 7, 28, 91, 365
                page            TEXT NOT NULL,
                clicks          INTEGER DEFAULT 0,
                impressions     INTEGER DEFAULT 0,
                ctr             REAL DEFAULT 0.0,
                position        REAL DEFAULT 0.0
            );

            -- GSC query-level snapshots
            CREATE TABLE IF NOT EXISTS gsc_queries (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          INTEGER REFERENCES runs(id),
                collected_at    TEXT NOT NULL,
                lookback_days   INTEGER NOT NULL,
                query           TEXT NOT NULL,
                clicks          INTEGER DEFAULT 0,
                impressions     INTEGER DEFAULT 0,
                ctr             REAL DEFAULT 0.0,
                position        REAL DEFAULT 0.0
            );

            -- Topic registry (seeds from watchlist + discovered topics)
            CREATE TABLE IF NOT EXISTS topics (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL UNIQUE,
                topic_type      TEXT,                  -- varietal, region, brand, retailer, format, question
                brand_tier      TEXT,                  -- direct, adjacent, watch_only (brands only)
                adjacent_angle  TEXT,                  -- the Wine Pair angle for adjacent brands
                source          TEXT DEFAULT 'watchlist', -- watchlist or discovered
                added_at        TEXT NOT NULL,
                active          INTEGER DEFAULT 1
            );

            -- Per-run topic demand signals from each source
            CREATE TABLE IF NOT EXISTS topic_snapshots (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          INTEGER REFERENCES runs(id),
                topic_id        INTEGER REFERENCES topics(id),
                collected_at    TEXT NOT NULL,
                gsc_impressions_28d  INTEGER,
                gsc_clicks_28d       INTEGER,
                gsc_position_28d     REAL,
                youtube_video_count  INTEGER,
                youtube_total_views  INTEGER,
                rss_mention_count    INTEGER,
                reddit_post_count    INTEGER,           -- null if Reddit not enabled
                trends_index         REAL               -- null if Trends API not enabled
            );

            -- YouTube search results per run
            CREATE TABLE IF NOT EXISTS youtube_results (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          INTEGER REFERENCES runs(id),
                topic_id        INTEGER REFERENCES topics(id),
                collected_at    TEXT NOT NULL,
                video_id        TEXT NOT NULL,
                title           TEXT,
                channel_name    TEXT,
                published_at    TEXT,
                view_count      INTEGER,
                like_count      INTEGER,
                comment_count   INTEGER,
                description_snippet TEXT
            );

            -- RSS feed items per run
            CREATE TABLE IF NOT EXISTS rss_items (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          INTEGER REFERENCES runs(id),
                collected_at    TEXT NOT NULL,
                source_name     TEXT NOT NULL,
                source_type     TEXT,                  -- wine_industry, seo_aeo
                title           TEXT,
                url             TEXT,
                published_at    TEXT,
                summary         TEXT,
                topics_matched  TEXT                   -- JSON array of matched topic names
            );

            -- Computed scores per topic per run
            CREATE TABLE IF NOT EXISTS trend_scores (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          INTEGER REFERENCES runs(id),
                topic_id        INTEGER REFERENCES topics(id),
                scored_at       TEXT NOT NULL,
                demand_score    REAL,
                trend_score     REAL,
                trend_label     TEXT,  -- new_spike, slow_riser, stable_evergreen, seasonal, declining, past_peak, noisy, emerging
                content_gap_score   REAL,
                wine_pair_fit   REAL,
                strategic_advantage REAL,
                existing_authority  REAL,
                performance_leverage REAL,
                aeo_answerability   REAL,
                episode_potential   REAL,
                blog_potential      REAL,
                social_potential    REAL,
                saturation_score    REAL,
                effort_score        REAL,
                composite_score     REAL,
                weeks_of_history    INTEGER            -- how many prior runs contributed to trend
            );

            -- Generated recommendations per run
            CREATE TABLE IF NOT EXISTS recommendations (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          INTEGER REFERENCES runs(id),
                generated_at    TEXT NOT NULL,
                category        TEXT NOT NULL,         -- create_now, refresh, promote, monitor, test_socially, build_cluster, adjacent, watch_only, ignore
                content_type    TEXT,                  -- episode, blog, social, refresh
                topic_id        INTEGER REFERENCES topics(id),
                title           TEXT,
                recommendation  TEXT NOT NULL,
                evidence        TEXT,
                interpretation  TEXT,
                wine_pair_angle TEXT,
                confidence_score REAL,
                related_content TEXT,                  -- JSON array of related URLs
                source_refs     TEXT                   -- JSON array of source links
            );

            -- Source availability per run
            CREATE TABLE IF NOT EXISTS source_status (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          INTEGER REFERENCES runs(id),
                source_name     TEXT NOT NULL,
                status          TEXT NOT NULL,         -- success, failed, skipped, partial
                records_collected INTEGER DEFAULT 0,
                error_message   TEXT,
                checked_at      TEXT NOT NULL
            );

            -- Run logs (errors and warnings)
            CREATE TABLE IF NOT EXISTS run_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          INTEGER REFERENCES runs(id),
                logged_at       TEXT NOT NULL,
                level           TEXT NOT NULL,         -- INFO, WARNING, ERROR
                source          TEXT,
                message         TEXT NOT NULL
            );

            -- Indexes for common queries
            CREATE INDEX IF NOT EXISTS idx_gsc_pages_run ON gsc_pages(run_id, lookback_days);
            CREATE INDEX IF NOT EXISTS idx_gsc_queries_run ON gsc_queries(run_id, lookback_days);
            CREATE INDEX IF NOT EXISTS idx_topic_snapshots_topic ON topic_snapshots(topic_id, run_id);
            CREATE INDEX IF NOT EXISTS idx_trend_scores_topic ON trend_scores(topic_id, run_id);
            CREATE INDEX IF NOT EXISTS idx_content_items_url ON content_items(url, run_id);
        """)
    conn.close()


def start_run(db_path: str) -> int:
    conn = get_connection(db_path)
    now = datetime.utcnow().isoformat()
    with conn:
        cursor = conn.execute(
            "INSERT INTO runs (run_date, started_at) VALUES (?, ?)",
            (datetime.utcnow().date().isoformat(), now)
        )
        run_id = cursor.lastrowid
    conn.close()
    return run_id


def complete_run(db_path: str, run_id: int, status: str = "completed", notes: str = None) -> None:
    conn = get_connection(db_path)
    now = datetime.utcnow().isoformat()
    with conn:
        conn.execute(
            "UPDATE runs SET completed_at = ?, status = ?, notes = ? WHERE id = ?",
            (now, status, notes, run_id)
        )
    conn.close()


def log(db_path: str, run_id: int, level: str, message: str, source: str = None) -> None:
    conn = get_connection(db_path)
    now = datetime.utcnow().isoformat()
    with conn:
        conn.execute(
            "INSERT INTO run_logs (run_id, logged_at, level, source, message) VALUES (?, ?, ?, ?, ?)",
            (run_id, now, level, source, message)
        )
    conn.close()


def record_source_status(db_path: str, run_id: int, source_name: str, status: str,
                          records: int = 0, error: str = None) -> None:
    conn = get_connection(db_path)
    now = datetime.utcnow().isoformat()
    with conn:
        conn.execute(
            """INSERT INTO source_status
               (run_id, source_name, status, records_collected, error_message, checked_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (run_id, source_name, status, records, error, now)
        )
    conn.close()
