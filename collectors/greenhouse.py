import json
import html
import re
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


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


def fetch_greenhouse_jobs(sources: list[dict]) -> list[dict]:
    jobs = []

    for source in sources:
        slug = source["slug"]
        company_name = source["name"]
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"

        try:
            with urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

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
                    "employment_type": "Unknown",
                    "posted_date": job.get("updated_at") or job.get("created_at"),
                })

        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"Greenhouse fetch failed for {slug}: {e}")

    return jobs