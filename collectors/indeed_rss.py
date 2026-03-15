import hashlib
import html
import re
from datetime import datetime, timezone

import feedparser

from config import RSS_URLS


def _clean_html(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_location(entry) -> str:
    # Indeed-specific 'where' attribute
    where = getattr(entry, "where", None)
    if where:
        return str(where).strip()
    # Tags (some feeds encode location here)
    for tag in getattr(entry, "tags", []):
        term = getattr(tag, "term", "")
        if term and not term.startswith("http"):
            return term.strip()
    return "Unknown"


def _parse_posted_date(entry) -> str | None:
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return None


def fetch_indeed_jobs() -> list[dict]:
    if not RSS_URLS:
        return []

    jobs = []
    seen_links: set[str] = set()

    for url in RSS_URLS:
        print(f"Checking RSS feed: {url}")
        try:
            feed = feedparser.parse(url, agent="Mozilla/5.0")
        except Exception as e:
            print(f"RSS feed error ({url}): {e}")
            continue

        if feed.bozo and not feed.entries:
            print(f"RSS feed returned no entries ({url})")
            continue

        print(f"  entries found: {len(feed.entries)}")

        for entry in feed.entries:
            link = getattr(entry, "link", "").strip()
            if not link or link in seen_links:
                continue
            seen_links.add(link)

            jobs.append({
                "job_id": "rss:" + hashlib.md5(link.encode()).hexdigest()[:16],
                "title": _clean_html(getattr(entry, "title", "")).strip(),
                "company": _clean_html(getattr(entry, "author", "Unknown")).strip()
                           if hasattr(entry, "author") else "Unknown",
                "summary": _clean_html(getattr(entry, "summary", "")),
                "link": link,
                "source": "Indeed RSS",
                "location": _parse_location(entry),
                "employment_type": "Unknown",
                "posted_date": _parse_posted_date(entry),
            })

    return jobs
