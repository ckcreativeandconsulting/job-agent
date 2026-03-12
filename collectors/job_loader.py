from collectors.manual_linkedin import load_manual_linkedin_jobs
from collectors.greenhouse import fetch_greenhouse_jobs
from collectors.lever import fetch_lever_jobs


def load_all_jobs() -> list[dict]:
    jobs = []

    for loader in [
        load_manual_linkedin_jobs,
        fetch_greenhouse_jobs,
        fetch_lever_jobs,
    ]:
        try:
            jobs.extend(loader())
        except Exception as e:
            print(f"Collector failed: {loader.__name__}: {e}")

    return jobs