import json
from config import MANUAL_LINKEDIN_JOBS_FILE


def load_manual_linkedin_jobs() -> list[dict]:
    try:
        with open(MANUAL_LINKEDIN_JOBS_FILE, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        if not isinstance(jobs, list):
            print("manual_linkedin_jobs.json must contain a list of jobs.")
            return []

        return jobs

    except FileNotFoundError:
        print("manual_linkedin_jobs.json not found.")
        return []

    except json.JSONDecodeError:
        print("manual_linkedin_jobs.json is not valid JSON.")
        return []