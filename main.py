from concurrent.futures import ThreadPoolExecutor, as_completed

from collectors.job_loader import load_all_jobs
from filters.keyword_filter import keyword_filter
from filters.ranker import rank_jobs
from ai.scorer import score_job, load_profile_text
from ai import embedding_cache
from output.digest import build_digest
from utils.file_utils import save_json
from config import (
    FILTERED_JOBS_FILE, SCORED_JOBS_FILE, MAX_AI_JOBS, MAX_MANUAL_SCORE, MIN_RANK_SCORE,
    SCORER_MAX_WORKERS, EMBEDDING_CACHE_FILE, EMBEDDING_CACHE_ENABLED,
)
from output.sheets_logger import append_jobs, get_applied_data
from utils.dedupe import dedupe_same_company_title


def main():
    if EMBEDDING_CACHE_ENABLED:
        embedding_cache.load(EMBEDDING_CACHE_FILE)

    all_jobs = load_all_jobs()
    print(f"\nCollected {len(all_jobs)} total jobs")

    # Separate manual LinkedIn picks (pre-screened by user) from automated sources.
    # Manual jobs bypass keyword filter and MIN_RANK_SCORE — they're always AI-scored.
    manual_jobs = [j for j in all_jobs if j.get("source") == "LinkedIn"]
    auto_jobs   = [j for j in all_jobs if j.get("source") != "LinkedIn"]

    filtered_auto = keyword_filter(auto_jobs)
    ignored_jobs  = [j for j in auto_jobs if j not in filtered_auto]

    print(f"Manual LinkedIn picks: {len(manual_jobs)} loaded")
    print(f"Automated jobs after keyword filter: {len(filtered_auto)} (ignored: {len(ignored_jobs)})")

    applied_links, applied_companies, rejected_links, scored_manual_links, rejected_companies_count = get_applied_data()
    seen_links = applied_links | rejected_links  # all previously-reviewed jobs
    print(
        f"Sheet feedback: {len(applied_links)} applied ('Yes'), "
        f"{len(rejected_links)} rejected ('No'), "
        f"{len(scored_manual_links)} LinkedIn already scored"
    )

    # Rank all jobs together (manual jobs benefit from rank_score display on sheet)
    all_for_ranking = filtered_auto + manual_jobs
    ranked_jobs = rank_jobs(all_for_ranking, applied_companies)
    after_rank_count = len(ranked_jobs)

    ranked_jobs = dedupe_same_company_title(ranked_jobs)
    after_dedupe_count = len(ranked_jobs)

    save_json(FILTERED_JOBS_FILE, ranked_jobs)

    # Log why any loaded manual jobs are being skipped before scoring
    for job in ranked_jobs:
        if job.get("source") != "LinkedIn":
            continue
        link = job.get("link", "")
        label = job.get("title") or job.get("company") or link
        if link in seen_links:
            print(f"  [Manual] SKIP (already reviewed in sheet): {label}")
        elif link in scored_manual_links:
            print(f"  [Manual] SKIP (already scored — exists in sheet): {label}")

    # Manual picks: always score regardless of rank threshold.
    # Skip already-reviewed (seen_links) AND already-scored (scored_manual_links)
    # to avoid paying OpenAI again for the same URL.
    manual_to_score = [
        job for job in ranked_jobs
        if job.get("source") == "LinkedIn"
        and job.get("link") not in seen_links
        and job.get("link") not in scored_manual_links
    ][:MAX_MANUAL_SCORE]

    # Automated: normal rank threshold + cap
    normal_to_score = [
        job for job in ranked_jobs
        if job.get("source") != "LinkedIn"
        and job.get("rank_score", 0) >= MIN_RANK_SCORE
        and job.get("link") not in seen_links
    ][:MAX_AI_JOBS]

    # Manual jobs listed first so they always appear in the digest
    jobs_to_score = manual_to_score + normal_to_score

    print(
        f"Queued for AI scoring: {len(manual_to_score)} manual + "
        f"{len(normal_to_score)} automated = {len(jobs_to_score)} total"
    )

    load_profile_text()  # pre-warm before threads to avoid lazy-load race

    scored_jobs = []
    with ThreadPoolExecutor(max_workers=SCORER_MAX_WORKERS) as executor:
        future_to_job = {executor.submit(score_job, job): job for job in jobs_to_score}
        for future in as_completed(future_to_job):
            job = future_to_job[future]
            try:
                result = future.result()
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

            scored_jobs.append({**job, **result})

    if EMBEDDING_CACHE_ENABLED:
        embedding_cache.flush(EMBEDDING_CACHE_FILE)

    from utils.company_learning import update_company_outcomes, sync_company_rejections
    update_company_outcomes(scored_jobs)
    sync_company_rejections(rejected_companies_count)
    append_jobs(scored_jobs)

    save_json(SCORED_JOBS_FILE, scored_jobs)

    digest = build_digest(scored_jobs, ignored_jobs)

    apply_count = sum(1 for job in scored_jobs if job.get("action") == "Apply")
    maybe_count = sum(1 for job in scored_jobs if job.get("action") == "Maybe")
    ignore_count = len(ignored_jobs) + sum(1 for job in scored_jobs if job.get("action") == "Ignore")

    print("\nRUN SUMMARY")
    print("--------------------------------------------------")
    print(f"Collected: {len(all_jobs)}")
    print(f"After keyword filter: {len(filtered_auto)}")
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
