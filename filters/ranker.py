from collections import defaultdict
from datetime import datetime, timezone
from utils.company_learning import learned_company_boost
from ai.embeddings import job_semantic_similarity
from config import SEMANTIC_WEIGHT, SEMANTIC_MIN_SIM, EMBED_CANDIDATE_LIMIT

from config import (
    RANKING_TITLE_WEIGHTS,
    RANKING_SUMMARY_WEIGHTS,
    RANKING_EMPLOYMENT_WEIGHTS,
    RANKING_NEGATIVE_TITLE_WEIGHTS,
    RANKING_NEGATIVE_SUMMARY_WEIGHTS,
    MAX_JOBS_PER_COMPANY,
    COMPANY_PRIORITY,
    APPLIED_COMPANY_BOOST,
)


def freshness_boost(posted_date):
    if not posted_date:
        return 0

    try:
        posted = datetime.fromisoformat(posted_date.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - posted).days
    except Exception:
        return 0

    if age_days <= 2:
        return 20
    elif age_days <= 5:
        return 12
    elif age_days <= 10:
        return 6
    elif age_days <= 20:
        return 2
    else:
        return 0


def compute_rank_score_fast(job: dict, applied_companies: set = None) -> int:
    """Keyword/rule-based rank score without semantic embedding (fast pass)."""
    title = job.get("title", "").lower()
    summary = job.get("summary", "").lower()
    location = job.get("location", "").lower()
    employment_type = job.get("employment_type", "").lower()
    company = job.get("company", "").lower()
    posted_date = job.get("posted_date")

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

    score += COMPANY_PRIORITY.get(company, 0)
    if applied_companies and company in applied_companies:
        score += APPLIED_COMPANY_BOOST
    score += learned_company_boost(company)
    score += freshness_boost(posted_date)

    return score


def rank_jobs(jobs: list[dict], applied_companies: set = None) -> list[dict]:
    # Pass 1: fast keyword/rule-based scoring for all jobs
    for job in jobs:
        job["rank_score"] = compute_rank_score_fast(job, applied_companies)
        job["semantic_similarity"] = None

    jobs.sort(key=lambda j: j["rank_score"], reverse=True)

    # Pass 2: semantic boost for top EMBED_CANDIDATE_LIMIT candidates only
    for job in jobs[:EMBED_CANDIDATE_LIMIT]:
        try:
            sim = job_semantic_similarity(job)
        except Exception as e:
            sim = 0.0
            job["semantic_similarity_error"] = str(e)

        job["semantic_similarity"] = round(sim, 4)
        if sim >= SEMANTIC_MIN_SIM:
            job["rank_score"] += int((sim - SEMANTIC_MIN_SIM) * SEMANTIC_WEIGHT * 10)

    jobs.sort(key=lambda j: j["rank_score"], reverse=True)

    company_counts = defaultdict(int)
    diversified_jobs = []

    for job in jobs:
        company = job.get("company", "Unknown")
        if company_counts[company] < MAX_JOBS_PER_COMPANY:
            diversified_jobs.append(job)
            company_counts[company] += 1

    return diversified_jobs