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
                location = categories.get("location", "Unknown")
                description = job.get("descriptionPlain", "") or ""

                jobs.append({
                    "title": job.get("text", "").strip(),
                    "company": company.title(),
                    "summary": description[:4000],
                    "link": job.get("hostedUrl", "").strip(),
                    "source": "Lever",
                    "location": location,
                    "employment_type": "Unknown",
                })

        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"Lever fetch failed for {company}: {e}")

    return jobs