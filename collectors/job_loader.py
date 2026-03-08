from collectors.manual_linkedin import load_manual_linkedin_jobs
from collectors.greenhouse import fetch_greenhouse_jobs
from collectors.lever import fetch_lever_jobs


def load_all_jobs() -> list[dict]:
    jobs = []

    jobs.extend(load_manual_linkedin_jobs())
    jobs.extend(fetch_greenhouse_jobs())
    jobs.extend(fetch_lever_jobs())

    return jobs