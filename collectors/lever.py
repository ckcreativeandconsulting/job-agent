import json
from datetime import datetime, timezone
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


def fetch_lever_jobs(sources: list[dict]) -> list[dict]:
    jobs = []

    for source in sources:
        slug = source["slug"]
        company_name = source["name"]
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"

        try:
            with urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

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

        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"Lever fetch failed for {slug}: {e}")

    return jobs