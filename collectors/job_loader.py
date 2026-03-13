from config import COMPANY_SOURCES
from collectors.greenhouse import fetch_greenhouse_jobs
from collectors.lever import fetch_lever_jobs
from collectors.manual_linkedin import load_manual_linkedin_jobs


def load_all_jobs() -> list[dict]:
    jobs = []

    jobs.extend(load_manual_linkedin_jobs())

    greenhouse_sources = [c for c in COMPANY_SOURCES if c["ats"] == "greenhouse"]
    lever_sources = [c for c in COMPANY_SOURCES if c["ats"] == "lever"]

    if greenhouse_sources:
        jobs.extend(fetch_greenhouse_jobs(greenhouse_sources))

    if lever_sources:
        jobs.extend(fetch_lever_jobs(lever_sources))

    return jobs