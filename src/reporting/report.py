"""
Report generator — Phase 1 placeholder.

TODO Phase 1: Implement full Markdown + HTML report generation using Jinja2 templates.

The report should include:
  1. Executive Summary
  2. Owned Performance (GSC, podcast, social)
  3. SEO/AEO Performance Review
  4. Content Coverage and Gap Map
  5. Trend Intelligence (with week-over-week movement)
  6. External Conversation Scan (YouTube, RSS)
  7. Brand and Retailer Watchlist
  8. Recommendations (episodes, blogs, social, refreshes)
  9. Data Quality Notes (sources used, failed, partial)

Each section must separate evidence from interpretation.
"""


def generate(db_path: str, run_id: int, output_dir: str = "reports") -> dict:
    """
    Generate Markdown and HTML reports for a completed run.
    Returns dict with output file paths.
    """
    raise NotImplementedError(
        "Report generation is a Phase 1 deliverable. "
        "Run with --dry-run to collect data without generating a report."
    )
