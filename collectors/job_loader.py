import json
from pathlib import Path

from collectors.manual_linkedin import load_manual_linkedin_jobs
from collectors.greenhouse import fetch_greenhouse_jobs
from collectors.lever import fetch_lever_jobs
from collectors.ashby import fetch_ashby_jobs
from collectors.indeed_rss import fetch_indeed_jobs
from collectors.themuse import fetch_muse_jobs
from config import RSS_URLS, THEMUSE_ENABLED


VERIFIED_SOURCES_FILE = Path("config/verified_company_sources.json")


def load_verified_sources() -> list[dict]:
    if not VERIFIED_SOURCES_FILE.exists():
        print("No verified company sources file found.")
        return []

    with VERIFIED_SOURCES_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_all_jobs() -> list[dict]:
    jobs = []

    jobs.extend(load_manual_linkedin_jobs())

    sources = load_verified_sources()

    greenhouse_sources = [s for s in sources if s.get("ats") == "greenhouse"]
    lever_sources = [s for s in sources if s.get("ats") == "lever"]
    ashby_sources = [s for s in sources if s.get("ats") == "ashby"]

    print(f"Verified sources loaded: {len(sources)}")
    print(f"  Greenhouse: {len(greenhouse_sources)} | Lever: {len(lever_sources)} | Ashby: {len(ashby_sources)}")

    if greenhouse_sources:
        jobs.extend(fetch_greenhouse_jobs(greenhouse_sources))

    if lever_sources:
        jobs.extend(fetch_lever_jobs(lever_sources))

    if ashby_sources:
        jobs.extend(fetch_ashby_jobs(ashby_sources))

    if RSS_URLS:
        jobs.extend(fetch_indeed_jobs())

    if THEMUSE_ENABLED:
        print("Fetching jobs from The Muse...")
        jobs.extend(fetch_muse_jobs())

    return jobs
