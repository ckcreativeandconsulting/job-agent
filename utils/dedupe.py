import re


def normalize_title(title: str) -> str:
    """
    Normalize job titles so small wording differences don't bypass dedupe.
    """

    if not title:
        return ""

    title = title.lower()

    # normalize common abbreviations
    replacements = {
        "sr.": "senior",
        "sr ": "senior ",
        "staff+": "staff",
        "tpm": "technical program manager",
        "pm ": "product manager ",
    }

    for k, v in replacements.items():
        title = title.replace(k, v)

    # remove punctuation
    title = re.sub(r"[^\w\s]", " ", title)

    # collapse whitespace
    title = re.sub(r"\s+", " ", title).strip()

    return title


def dedupe_same_company_title(jobs: list[dict]) -> list[dict]:
    """
    Remove duplicate jobs using normalized (company, title).
    Keep the job with the highest rank_score.
    """

    best_by_key = {}

    for job in jobs:

        company = job.get("company", "").strip().lower()
        title = normalize_title(job.get("title", ""))

        key = (company, title)

        existing = best_by_key.get(key)

        if existing is None or job.get("rank_score", 0) > existing.get("rank_score", 0):
            best_by_key[key] = job

    deduped = list(best_by_key.values())

    removed = len(jobs) - len(deduped)

    if removed:
        print(f"Removed {removed} duplicate jobs after title normalization")

    return deduped