from collections import defaultdict

from config import (
    RANKING_TITLE_WEIGHTS,
    RANKING_SUMMARY_WEIGHTS,
    RANKING_EMPLOYMENT_WEIGHTS,
    RANKING_NEGATIVE_TITLE_WEIGHTS,
    RANKING_NEGATIVE_SUMMARY_WEIGHTS,
    MAX_JOBS_PER_COMPANY,
)


def compute_rank_score(job: dict) -> int:
    title = job.get("title", "").lower()
    summary = job.get("summary", "").lower()
    location = job.get("location", "").lower()
    employment_type = job.get("employment_type", "").lower()

    score = 0

    for keyword, weight in RANKING_TITLE_WEIGHTS.items():
        if keyword in title:
            score += weight

    for keyword, weight in RANKING_SUMMARY_WEIGHTS.items():
        if keyword in summary:
            score += weight

    for keyword, weight in RANKING_EMPLOYMENT_WEIGHTS.items():
        if keyword in employment_type or keyword in summary:
            score += weight

    if "remote" in location or "remote" in summary:
        score += 4

    for keyword, weight in RANKING_NEGATIVE_TITLE_WEIGHTS.items():
        if keyword in title:
            score += weight

    for keyword, weight in RANKING_NEGATIVE_SUMMARY_WEIGHTS.items():
        if keyword in summary:
            score += weight

    return score


def rank_jobs(jobs: list[dict]) -> list[dict]:
    ranked_jobs = []

    for job in jobs:
        rank_score = compute_rank_score(job)
        ranked_job = {**job, "rank_score": rank_score}
        ranked_jobs.append(ranked_job)

    ranked_jobs.sort(key=lambda job: job["rank_score"], reverse=True)

    company_counts = defaultdict(int)
    diversified_jobs = []

    for job in ranked_jobs:
        company = job.get("company", "Unknown")
        if company_counts[company] < MAX_JOBS_PER_COMPANY:
            diversified_jobs.append(job)
            company_counts[company] += 1

    return diversified_jobs