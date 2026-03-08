from collectors.job_loader import load_all_jobs
from filters.keyword_filter import keyword_filter
from filters.ranker import rank_jobs
from ai.scorer import score_job
from output.digest import build_digest
from utils.file_utils import save_json
from config import FILTERED_JOBS_FILE, SCORED_JOBS_FILE, MAX_AI_JOBS, MIN_RANK_SCORE
from output.sheets_logger import append_jobs


def main():
    jobs = load_all_jobs()
    print(f"\nCollected {len(jobs)} total jobs")

    filtered_jobs = keyword_filter(jobs)
    ignored_jobs = [job for job in jobs if job not in filtered_jobs]

    print(f"Jobs after filtering: {len(filtered_jobs)}")
    print(f"Jobs ignored before scoring: {len(ignored_jobs)}")

    ranked_jobs = rank_jobs(filtered_jobs)
    save_json(FILTERED_JOBS_FILE, ranked_jobs)

    jobs_to_score = [
    job for job in ranked_jobs
    if job.get("rank_score", 0) >= MIN_RANK_SCORE
    ][:MAX_AI_JOBS]

    print(f"Scoring top {len(jobs_to_score)} ranked jobs with AI")

    scored_jobs = []
    for job in jobs_to_score:
        result = score_job(job)
        scored_job = {**job, **result}
        scored_jobs.append(scored_job)

    append_jobs(scored_jobs)

    save_json(SCORED_JOBS_FILE, scored_jobs)

    digest = build_digest(scored_jobs, ignored_jobs)

    print("\n" + digest + "\n")


if __name__ == "__main__":
    main()