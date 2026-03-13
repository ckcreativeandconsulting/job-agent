from collectors.job_loader import load_all_jobs
from filters.keyword_filter import keyword_filter
from filters.ranker import rank_jobs
from ai.scorer import score_job
from output.digest import build_digest
from utils.file_utils import save_json
from config import FILTERED_JOBS_FILE, SCORED_JOBS_FILE, MAX_AI_JOBS, MIN_RANK_SCORE
from output.sheets_logger import append_jobs
from utils.dedupe import dedupe_same_company_title


def main():
    jobs = load_all_jobs()
    print(f"\nCollected {len(jobs)} total jobs")

    filtered_jobs = keyword_filter(jobs)
    ignored_jobs = [job for job in jobs if job not in filtered_jobs]

    print(f"Jobs after filtering: {len(filtered_jobs)}")
    print(f"Jobs ignored before scoring: {len(ignored_jobs)}")

    ranked_jobs = rank_jobs(filtered_jobs)
    after_rank_count = len(ranked_jobs)

    ranked_jobs = dedupe_same_company_title(ranked_jobs)
    after_dedupe_count = len(ranked_jobs)

    save_json(FILTERED_JOBS_FILE, ranked_jobs)

    jobs_to_score = [
        job for job in ranked_jobs
        if job.get("rank_score", 0) >= MIN_RANK_SCORE
    ][:MAX_AI_JOBS]

    print(f"Scoring top {len(jobs_to_score)} ranked jobs with AI (limit: {MAX_AI_JOBS})")

    scored_jobs = []
    for job in jobs_to_score:
        try:
            result = score_job(job)
        except Exception as e:
            result = {
                "score": 50,
                "why_match": ["Scoring failed"],
                "concerns": [str(e)],
                "employment_type_label": job.get("employment_type", "Unknown"),
                "action": "Ignore",
                "backend": "error",
                "model": "none",
            }

        backend = result.get("backend", "unknown")
        pre_backend = result.get("pre_backend")
        score = result.get("score")

        if pre_backend:
            print(
                f"[AI] {job.get('company', 'Unknown')} — {job.get('title', 'Unknown')} "
                f"=> final={backend}, pre={pre_backend}, score={score}, pre_score={result.get('pre_score')}"
            )
        else:
            print(
                f"[AI] {job.get('company', 'Unknown')} — {job.get('title', 'Unknown')} "
                f"=> backend={backend}, score={score}"
            )

        scored_job = {**job, **result}
        scored_jobs.append(scored_job)

    from utils.company_learning import update_company_outcomes
    update_company_outcomes(scored_jobs)
    append_jobs(scored_jobs)

    save_json(SCORED_JOBS_FILE, scored_jobs)

    digest = build_digest(scored_jobs, ignored_jobs)

    apply_count = sum(1 for job in scored_jobs if job.get("action") == "Apply")
    maybe_count = sum(1 for job in scored_jobs if job.get("action") == "Maybe")
    ignore_count = len(ignored_jobs) + sum(1 for job in scored_jobs if job.get("action") == "Ignore")

    print("\nRUN SUMMARY")
    print("--------------------------------------------------")
    print(f"Collected: {len(jobs)}")
    print(f"After keyword filter: {len(filtered_jobs)}")
    print(f"Ignored before scoring: {len(ignored_jobs)}")
    print(f"After ranking/company cap: {after_rank_count}")
    print(f"After dedupe: {after_dedupe_count}")
    print(f"AI scored: {len(scored_jobs)}")
    print(f"Apply: {apply_count}")
    print(f"Maybe: {maybe_count}")
    print(f"Ignore: {ignore_count}")

    print("\n" + digest + "\n")


if __name__ == "__main__":
    main()