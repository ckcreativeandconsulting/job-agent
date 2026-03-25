import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from config import COLLECTOR_MAX_WORKERS

_ASHBY_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

_EMPLOYMENT_TYPE_MAP = {
    "FullTime": "Full-time",
    "PartTime": "Part-time",
    "Contract": "Contract",
    "Contractor": "Contract",
    "Temporary": "Contract",
    "Intern": "Internship",
}


def _clean_html(raw: str) -> str:
    if not raw:
        return ""
    text = html.unescape(raw)
    text = text.replace("\xa0", " ")
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>|</li>|</h1>|</h2>|</h3>|</h4>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fetch_one_ashby(source: dict) -> list[dict]:
    slug = source["slug"]
    company_name = source["name"]
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"

    try:
        response = requests.get(url, headers=_ASHBY_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for job in data.get("jobs", []):
            location = (job.get("location") or "").strip()
            workplace = job.get("workplaceType", "")
            if job.get("isRemote") or workplace in ("Remote", "Distributed"):
                if not location or location.lower() in ("remote", ""):
                    location = "Remote"
                elif "remote" not in location.lower():
                    location = f"{location} (Remote)"
            elif workplace == "Hybrid":
                if not location or location.lower() == "hybrid":
                    location = "Hybrid"
                elif "hybrid" not in location.lower():
                    location = f"{location} (Hybrid)"

            summary = _clean_html(job.get("descriptionHtml") or job.get("descriptionPlain") or "")
            employment_type = _EMPLOYMENT_TYPE_MAP.get(job.get("employmentType", ""), "Unknown")

            jobs.append({
                "job_id": f"ashby:{slug}:{job.get('id', '')}",
                "title": job.get("title", "").strip(),
                "company": company_name,
                "summary": summary[:4000],
                "link": job.get("jobUrl", "").strip(),
                "source": "ashby",
                "location": location,
                "employment_type": employment_type,
                "posted_date": job.get("publishedAt"),
            })
        return jobs

    except Exception as e:
        print(f"Ashby fetch failed for {slug}: {e}")
        return []


def fetch_ashby_jobs(sources: list[dict]) -> list[dict]:
    all_jobs = []
    with ThreadPoolExecutor(max_workers=COLLECTOR_MAX_WORKERS) as executor:
        futures = {executor.submit(_fetch_one_ashby, s): s for s in sources}
        for future in as_completed(futures):
            all_jobs.extend(future.result())
    return all_jobs
