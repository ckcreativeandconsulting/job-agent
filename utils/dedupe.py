def dedupe_same_company_title(jobs: list[dict]) -> list[dict]:
    best_by_key = {}

    for job in jobs:
        key = (
            job.get("company", "").strip().lower(),
            job.get("title", "").strip().lower(),
        )

        existing = best_by_key.get(key)

        if existing is None or job.get("rank_score", 0) > existing.get("rank_score", 0):
            best_by_key[key] = job

    deduped = list(best_by_key.values())
    removed = len(jobs) - len(deduped)

    if removed:
        print(f"Removed {removed} duplicate jobs by company/title")

    return deduped