import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from config import GREENHOUSE_COMPANIES


def fetch_greenhouse_jobs() -> list[dict]:
    jobs = []

    for company in GREENHOUSE_COMPANIES:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"

        try:
            with urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            for job in data.get("jobs", []):
                location = (job.get("location") or {}).get("name", "Unknown")
                content = job.get("content", "") or ""

                jobs.append({
                    "title": job.get("title", "").strip(),
                    "company": company.title(),
                    "summary": content[:4000],
                    "link": job.get("absolute_url", "").strip(),
                    "source": "Greenhouse",
                    "location": location,
                    "employment_type": "Unknown",
                })

        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"Greenhouse fetch failed for {company}: {e}")

    return jobs