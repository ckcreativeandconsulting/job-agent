import hashlib
import html
import json
import re

import requests

from config import MANUAL_LINKEDIN_JOBS_FILE

_LI_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_EMPLOYMENT_TYPE_MAP = {
    "FULL_TIME": "Full-time",
    "PART_TIME": "Part-time",
    "CONTRACTOR": "Contract",
    "TEMPORARY": "Contract",
    "INTERN": "Internship",
    "OTHER": "Unknown",
}


def _clean_html(text: str) -> str:
    """Strip HTML tags and decode entities."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _enrich_from_linkedin(url: str) -> dict:
    """
    Fetch a LinkedIn public job page and extract structured data.
    Tries JSON-LD first (full detail), then falls back to <title> tag.
    Returns a partial dict with whatever could be extracted, or {} on failure.
    """
    try:
        resp = requests.get(url, headers=_LI_HEADERS, timeout=12, allow_redirects=True)
        resp.raise_for_status()
        page = resp.text
    except Exception as e:
        print(f"[LinkedIn] Could not fetch {url}: {e}")
        return {}

    # Strategy 1: JSON-LD structured data — best quality
    for match in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        page,
        re.DOTALL | re.IGNORECASE,
    ):
        try:
            data = json.loads(match.group(1))
            if not isinstance(data, dict) or data.get("@type") != "JobPosting":
                continue

            # Location
            loc_raw = data.get("jobLocation") or {}
            if isinstance(loc_raw, list):
                loc_raw = loc_raw[0] if loc_raw else {}
            addr = loc_raw.get("address", {}) if isinstance(loc_raw, dict) else {}
            location = ", ".join(
                p for p in [addr.get("addressLocality", ""), addr.get("addressRegion", "")] if p
            )

            # Employment type
            emp_raw = (data.get("employmentType") or "").upper()
            employment_type = _EMPLOYMENT_TYPE_MAP.get(emp_raw, "Unknown")

            # Company
            org = data.get("hiringOrganization") or {}
            company = (org.get("name", "") if isinstance(org, dict) else "").strip()

            return {
                "title": html.unescape(data.get("title", "")).strip(),
                "company": company,
                "location": location,
                "summary": _clean_html(data.get("description", ""))[:4000],
                "employment_type": employment_type,
                "posted_date": data.get("datePosted"),
            }
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    # Strategy 2: <title> tag — "Job Title at Company | LinkedIn"
    title_match = re.search(r"<title[^>]*>(.*?)</title>", page, re.IGNORECASE | re.DOTALL)
    if title_match:
        raw_title = html.unescape(title_match.group(1)).strip()
        raw_title = re.sub(r"\s*\|\s*LinkedIn\s*$", "", raw_title, flags=re.IGNORECASE).strip()
        if " at " in raw_title:
            parts = raw_title.split(" at ", 1)
            print(f"[LinkedIn] Partial enrichment from title tag: {raw_title!r}")
            return {
                "title": parts[0].strip(),
                "company": parts[1].strip(),
                "location": "",
                "summary": "",
                "employment_type": "Unknown",
                "posted_date": None,
            }

    print(f"[LinkedIn] Could not extract job data from page: {url}")
    return {}


def load_manual_linkedin_jobs() -> list[dict]:
    """
    Load manual LinkedIn jobs from JSON file.

    Minimum required field per entry: "link".
    All other fields (title, company, location, summary, employment_type)
    are auto-enriched from the LinkedIn public page if missing.

    Example minimal entry:
        [{"link": "https://www.linkedin.com/jobs/view/1234567890/"}]
    """
    try:
        with open(MANUAL_LINKEDIN_JOBS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        print("manual_linkedin_jobs.json not found.")
        return []
    except json.JSONDecodeError:
        print("manual_linkedin_jobs.json is not valid JSON.")
        return []

    if not isinstance(raw, list):
        print("manual_linkedin_jobs.json must contain a list of jobs.")
        return []

    jobs = []
    for entry in raw:
        link = (entry.get("link") or "").strip()
        if not link:
            print("[LinkedIn] Skipping entry with no 'link' field.")
            continue

        job = dict(entry)  # copy, don't mutate original

        # Auto-enrich if title or company is missing
        if not job.get("title") or not job.get("company"):
            print(f"[LinkedIn] Fetching job details from page: {link}")
            enriched = _enrich_from_linkedin(link)
            if enriched:
                # Merge: explicitly provided fields take priority over enriched values
                job = {**enriched, **job}
            else:
                print(
                    f"[LinkedIn] Enrichment failed for {link}. "
                    f"Provided: title={job.get('title')!r}, company={job.get('company')!r}"
                )

        # Skip if still no title and no company — scorer can't do anything useful
        if not job.get("title") and not job.get("company"):
            print(f"[LinkedIn] Skipping {link} — no title or company available after enrichment.")
            continue

        # Fill in required defaults
        job.setdefault("job_id", "manual:" + hashlib.md5(link.encode()).hexdigest()[:16])
        job.setdefault("source", "LinkedIn")
        job.setdefault("employment_type", "Unknown")
        job.setdefault("summary", "")
        job.setdefault("location", "")
        job.setdefault("posted_date", None)
        job["link"] = link  # normalize

        jobs.append(job)

    print(f"[LinkedIn] Loaded {len(jobs)} manual job(s).")
    return jobs
