import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from config import LEVER_COMPANIES


def fetch_lever_jobs() -> list[dict]:
    jobs = []

    for company in LEVER_COMPANIES:
        url = f"https://api.lever.co/v0/postings/{company}?mode=json"

        try:
            with urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            for job in data:
                categories = job.get("categories", {}) or {}
                description = (
                    job.get("descriptionPlain")
                    or job.get("description")
                    or ""
                )

                jobs.append({
                    "job_id": f"lever:{company}:{job.get('id', '')}".strip(),
                    "title": job.get("text", "").strip(),
                    "company": company.title(),
                    "summary": description[:4000],
                    "link": job.get("hostedUrl", "").strip(),
                    "source": "lever",
                    "location": categories.get("location", "Unknown").strip(),
                    "employment_type": categories.get("commitment", "Unknown").strip() or "Unknown",
                    "department": categories.get("team", "").strip(),
                    "posted_at": job.get("createdAt"),
                })

        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"Lever fetch failed for {company}: {e}")

    return jobs