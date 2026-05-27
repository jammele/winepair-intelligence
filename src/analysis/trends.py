"""
Trend scoring and label computation.

Derives trend labels from historical topic_snapshots. Requires at least
TREND_MIN_WEEKS weeks of history before assigning a directional label.
"""

import sqlite3
from typing import Optional


TREND_MIN_WEEKS = 3

TREND_LABELS = {
    "new_spike": "New spike",
    "slow_riser": "Slow riser",
    "stable_evergreen": "Stable evergreen",
    "seasonal": "Seasonal",
    "declining": "Declining",
    "past_peak": "Past peak",
    "noisy": "Noisy/uncertain",
    "emerging": "Emerging (low confidence)",
    "insufficient_data": "Insufficient data",
}


def get_topic_history(conn: sqlite3.Connection, topic_id: int,
                      metric: str = "gsc_impressions_28d",
                      last_n_weeks: int = 12) -> list[Optional[float]]:
    """Return ordered list of weekly metric values (oldest first)."""
    rows = conn.execute(
        f"""
        SELECT ts.{metric}
        FROM topic_snapshots ts
        JOIN runs r ON ts.run_id = r.id
        WHERE ts.topic_id = ?
          AND r.status = 'completed'
        ORDER BY r.run_date DESC
        LIMIT ?
        """,
        (topic_id, last_n_weeks)
    ).fetchall()
    values = [row[0] for row in rows]
    values.reverse()
    return values


def compute_trend_label(values: list[Optional[float]]) -> tuple[str, int]:
    """
    Compute a trend label from a time series of weekly values.
    Returns (label, weeks_of_history).
    """
    clean = [v for v in values if v is not None]
    n = len(clean)

    if n < TREND_MIN_WEEKS:
        return "insufficient_data", n

    recent = clean[-2:]
    older = clean[:-2] if len(clean) > 2 else clean[:1]

    recent_avg = sum(recent) / len(recent)
    older_avg = sum(older) / len(older) if older else recent_avg

    if older_avg == 0:
        if recent_avg > 0:
            return "emerging", n
        return "insufficient_data", n

    change_pct = (recent_avg - older_avg) / older_avg

    # Spike: >100% increase in last 2 weeks
    if change_pct > 1.0:
        return "new_spike", n

    # Declining: >30% drop
    if change_pct < -0.3:
        if recent_avg < older_avg * 0.5:
            return "past_peak", n
        return "declining", n

    # Slow riser: 15-100% increase over longer trend
    if change_pct > 0.15:
        return "slow_riser", n

    # Stable: within ±15%
    if abs(change_pct) <= 0.15:
        return "stable_evergreen", n

    return "noisy", n


def compute_demand_score(snapshot: dict) -> float:
    """
    Normalize demand signals from a topic snapshot into a 0-1 score.
    Each contributing signal is weighted and capped.
    """
    score = 0.0

    impressions = snapshot.get("gsc_impressions_28d") or 0
    score += min(impressions / 10000, 0.35)

    yt_videos = snapshot.get("youtube_video_count") or 0
    score += min(yt_videos / 50, 0.25)

    yt_views = snapshot.get("youtube_total_views") or 0
    score += min(yt_views / 100000, 0.20)

    rss_mentions = snapshot.get("rss_mention_count") or 0
    score += min(rss_mentions / 10, 0.10)

    reddit_posts = snapshot.get("reddit_post_count") or 0
    score += min(reddit_posts / 20, 0.10)

    return round(min(score, 1.0), 3)


def compute_performance_leverage(page_data: list[dict]) -> float:
    """
    Score based on existing GSC pages that are close to working:
    high impressions + low CTR, or ranking 8-20.
    """
    if not page_data:
        return 0.0

    scores = []
    for page in page_data:
        impressions = page.get("impressions", 0)
        ctr = page.get("ctr", 1.0)
        position = page.get("position", 50)

        if impressions > 1000 and ctr < 0.02:
            scores.append(0.9)
        elif impressions > 500 and ctr < 0.05:
            scores.append(0.7)
        elif 8 <= position <= 20:
            scores.append(0.6)
        elif impressions > 200:
            scores.append(0.3)

    return round(max(scores, default=0.0), 3)
