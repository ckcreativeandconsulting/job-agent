"""
Collector for The Muse public jobs API (https://www.themuse.com/api/public/jobs).
No API key required. Returns up to ~20 jobs per page; we paginate all pages.

Queried categories / levels are tuned for Charles's target roles.
"""

import html
import re
import time

import requests

# Categories and levels to query. The Muse accepts multiple values per param,
# but the API requires separate requests per category.
_MUSE_CATEGORIES = [
    "Product Management",
    "Project Management",
]

_MUSE_LEVELS = [
    "Senior Level",
    "Mid Level",      # catches Group PM / Principal PM postings labelled mid
]

_MUSE_BASE_URL = "https://www.themuse.com/api/public/jobs"

_MUSE_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

# Max pages to fetch per (category, level) pair to bound runtime.
# 20 results/page × 25 pages = 500 results max per combination.
_MAX_PAGES = 25


def _clean_html(raw: str) -> str:
    if not raw:
        return ""
    text = html.unescape(raw)
    text = text.replace("\xa0", " ")
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>|</li>|</h[1-6]>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fetch_category_level(category: str, level: str) -> list[dict]:
    """Fetch all pages for one (category, level) pair."""
    jobs = []
    seen_ids: set[int] = set()

    for page in range(0, _MAX_PAGES):
        try:
            resp = requests.get(
                _MUSE_BASE_URL,
                headers=_MUSE_HEADERS,
                params={"category": category, "level": level, "page": page},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Muse fetch error (category={category!r}, level={level!r}, page={page}): {e}")
            break

        results = data.get("results", [])
        if not results:
            break  # no more pages

        for job in results:
            job_id = job.get("id")
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            title = job.get("name", "").strip()
            company = (job.get("company") or {}).get("name", "Unknown").strip()

            locations = job.get("locations") or []
            location = locations[0].get("name", "Unknown").strip() if locations else "Unknown"

            refs = job.get("refs") or {}
            link = refs.get("landing_page", "").strip()

            summary = _clean_html(job.get("contents", ""))

            # The Muse doesn't surface employment type — infer from title/summary
            text_lower = f"{title} {summary}".lower()
            if any(w in text_lower for w in ["contract", "interim", "temp ", "temporary"]):
                employment_type = "Contract"
            elif "fractional" in text_lower:
                employment_type = "Fractional"
            elif "part-time" in text_lower or "part time" in text_lower:
                employment_type = "Part-time"
            elif "full-time" in text_lower or "full time" in text_lower or "permanent" in text_lower:
                employment_type = "Full-time"
            else:
                employment_type = "Unknown"

            jobs.append({
                "job_id": f"muse:{job_id}",
                "title": title,
                "company": company,
                "summary": summary[:4000],
                "link": link,
                "source": "The Muse",
                "location": location,
                "employment_type": employment_type,
                "posted_date": job.get("publication_date"),
            })

        # Respect rate limits with a small delay between pages
        page_count = data.get("page_count", 0)
        if page >= page_count - 1:
            break
        time.sleep(0.2)

    return jobs


def fetch_muse_jobs() -> list[dict]:
    """Fetch jobs from The Muse across all configured categories and levels."""
    all_jobs: list[dict] = []
    seen_ids: set[str] = set()

    for category in _MUSE_CATEGORIES:
        for level in _MUSE_LEVELS:
            print(f"  Muse: fetching category={category!r} level={level!r}")
            batch = _fetch_category_level(category, level)
            for job in batch:
                if job["job_id"] not in seen_ids:
                    seen_ids.add(job["job_id"])
                    all_jobs.append(job)
            time.sleep(0.5)  # pause between category/level combos

    print(f"  Muse: {len(all_jobs)} unique jobs collected")
    return all_jobs
