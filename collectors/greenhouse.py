import json
import html
import re
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from config import GREENHOUSE_COMPANIES


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


def fetch_greenhouse_jobs() -> list[dict]:
    jobs = []

    for company in GREENHOUSE_COMPANIES:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"

        try:
            with urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            for job in data.get("jobs", []):
                location = (job.get("location") or {}).get("name", "Unknown")
                raw_content = job.get("content", "") or ""
                summary = clean_html_text(raw_content)

                jobs.append({
                    "job_id": f"greenhouse:{company}:{job.get('id', '')}",
                    "title": job.get("title", "").strip(),
                    "company": company.title(),
                    "summary": summary[:4000],
                    "link": job.get("absolute_url", "").strip(),
                    "source": "greenhouse",
                    "location": location,
                    "employment_type": "Unknown",
                })

        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"Greenhouse fetch failed for {company}: {e}")

    return jobs