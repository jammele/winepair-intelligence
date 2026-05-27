"""
Website content inventory connector.

Crawls the site via sitemap + WordPress REST API to build a content inventory.
Falls back to sitemap-only if the REST API is unavailable.
"""

import re
import json
import requests
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


def _get(url: str, timeout: int = 15) -> Optional[requests.Response]:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "WinePairIntelligence/1.0"})
        r.raise_for_status()
        return r
    except Exception:
        return None


def _extract_text(soup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ").split())


def fetch_sitemap_urls(sitemap_url: str) -> list[str]:
    """Parse sitemap (including sitemap index) and return all page URLs."""
    resp = _get(sitemap_url)
    if not resp:
        return []

    if not BS4_AVAILABLE:
        # Basic regex fallback
        return re.findall(r"<loc>(https?://[^<]+)</loc>", resp.text)

    soup = BeautifulSoup(resp.text, "lxml-xml")
    # Sitemap index → recurse
    sitemap_tags = soup.find_all("sitemap")
    if sitemap_tags:
        urls = []
        for sm in sitemap_tags:
            loc = sm.find("loc")
            if loc:
                urls.extend(fetch_sitemap_urls(loc.text.strip()))
        return urls

    # Regular sitemap
    return [loc.text.strip() for loc in soup.find_all("loc")]


def fetch_wordpress_posts(api_base: str, per_page: int = 100) -> list[dict]:
    """Fetch post metadata from WordPress REST API."""
    posts = []
    page = 1
    while True:
        resp = _get(f"{api_base}/posts?per_page={per_page}&page={page}&_fields=id,link,title,date,modified,excerpt,status")
        if not resp or not resp.json():
            break
        batch = resp.json()
        if not batch:
            break
        posts.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return posts


def classify_url(url: str) -> str:
    """Classify a URL as episode, blog, resource, landing, or other."""
    path = urlparse(url).path.lower()
    if "/episode" in path or "/ep" in path:
        return "episode"
    if "/blog" in path:
        return "blog"
    if path in ("/", ""):
        return "landing"
    return "other"


def scrape_page(url: str) -> dict:
    """Scrape a single page for content signals."""
    resp = _get(url)
    if not resp:
        return {}

    if not BS4_AVAILABLE:
        return {"url": url, "error": "beautifulsoup4 not installed"}

    soup = BeautifulSoup(resp.text, "lxml")

    title = soup.title.string.strip() if soup.title else ""
    meta_desc = ""
    meta_tag = soup.find("meta", {"name": "description"})
    if meta_tag:
        meta_desc = meta_tag.get("content", "")

    headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]
    text = _extract_text(soup)
    word_count = len(text.split())

    has_faq = bool(soup.find(attrs={"@type": "FAQPage"})) or '"FAQPage"' in resp.text
    has_review = '"Review"' in resp.text or '"AggregateRating"' in resp.text

    internal_links = []
    external_links = []
    base_domain = urlparse(url).netloc
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/") or base_domain in href:
            internal_links.append(href)
        elif href.startswith("http"):
            external_links.append(href)

    return {
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "content_type": classify_url(url),
        "word_count": word_count,
        "full_text": text[:5000],
        "headings": json.dumps(headings[:20]),
        "internal_links": json.dumps(list(set(internal_links))[:50]),
        "external_links": json.dumps(list(set(external_links))[:30]),
        "has_faq_schema": int(has_faq),
        "has_review_schema": int(has_review),
    }
