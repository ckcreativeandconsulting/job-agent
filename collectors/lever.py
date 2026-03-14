import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from config import COLLECTOR_MAX_WORKERS


def _fetch_one_lever(source: dict) -> list[dict]:
    slug = source["slug"]
    company_name = source["name"]
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"

    try:
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        jobs = []
        for job in data:
            categories = job.get("categories", {}) or {}
            description = job.get("descriptionPlain") or job.get("description") or ""

            created_at = job.get("createdAt")
            posted_date = None

            if created_at:
                try:
                    posted_date = datetime.fromtimestamp(
                        created_at / 1000,
                        tz=timezone.utc
                    ).isoformat()
                except Exception:
                    posted_date = None

            jobs.append({
                "job_id": f"lever:{slug}:{job.get('id', '')}",
                "title": job.get("text", "").strip(),
                "company": company_name,
                "summary": description[:4000],
                "link": job.get("hostedUrl", "").strip(),
                "source": "lever",
                "location": categories.get("location", "Unknown").strip(),
                "employment_type": categories.get("commitment", "Unknown").strip() or "Unknown",
                "department": categories.get("team", "").strip(),
                "posted_date": posted_date,
            })
        return jobs

    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"Lever fetch failed for {slug}: {e}")
        return []


def fetch_lever_jobs(sources: list[dict]) -> list[dict]:
    all_jobs = []
    with ThreadPoolExecutor(max_workers=COLLECTOR_MAX_WORKERS) as executor:
        futures = {executor.submit(_fetch_one_lever, s): s for s in sources}
        for future in as_completed(futures):
            all_jobs.extend(future.result())
    return all_jobs