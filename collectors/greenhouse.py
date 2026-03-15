import json
import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from config import COLLECTOR_MAX_WORKERS


def clean_html_text(raw_html: str) -> str:
    if not raw_html:
        return ""

    text = html.unescape(raw_html)
    text = text.replace("\xa0", " ")
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>|</li>|</h1>|</h2>|</h3>|</h4>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def infer_employment_type(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()
    if any(w in text for w in ["contract", "interim", "temp ", "temporary"]):
        return "Contract"
    if "fractional" in text:
        return "Fractional"
    if "part-time" in text or "part time" in text:
        return "Part-time"
    if "full-time" in text or "full time" in text or "permanent" in text:
        return "Full-time"
    return "Unknown"


def _fetch_one_greenhouse(source: dict) -> list[dict]:
    slug = source["slug"]
    company_name = source["name"]
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"

    try:
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        jobs = []
        for job in data.get("jobs", []):
            location = (job.get("location") or {}).get("name", "Unknown")
            summary = clean_html_text(job.get("content", "") or "")

            jobs.append({
                "job_id": f"greenhouse:{slug}:{job.get('id', '')}",
                "title": job.get("title", "").strip(),
                "company": company_name,
                "summary": summary[:4000],
                "link": job.get("absolute_url", "").strip(),
                "source": "greenhouse",
                "location": location,
                "employment_type": infer_employment_type(job.get("title", ""), summary),
                "posted_date": job.get("updated_at") or job.get("created_at"),
            })
        return jobs

    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"Greenhouse fetch failed for {slug}: {e}")
        return []


def fetch_greenhouse_jobs(sources: list[dict]) -> list[dict]:
    all_jobs = []
    with ThreadPoolExecutor(max_workers=COLLECTOR_MAX_WORKERS) as executor:
        futures = {executor.submit(_fetch_one_greenhouse, s): s for s in sources}
        for future in as_completed(futures):
            all_jobs.extend(future.result())
    return all_jobs