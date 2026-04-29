import json
from pathlib import Path
from datetime import datetime

COMPANY_OUTCOMES_FILE = Path("data/company_outcomes.json")


def load_company_outcomes() -> dict:
    if not COMPANY_OUTCOMES_FILE.exists():
        return {}

    try:
        with COMPANY_OUTCOMES_FILE.open("r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return {}


def save_company_outcomes(data: dict) -> None:
    COMPANY_OUTCOMES_FILE.parent.mkdir(exist_ok=True)
    with COMPANY_OUTCOMES_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update_company_outcomes(scored_jobs: list[dict]) -> None:
    data = load_company_outcomes()

    for job in scored_jobs:
        company = job.get("company", "").strip().lower()
        if not company:
            continue

        record = data.get(company, {
            "seen": 0,
            "scored": 0,
            "apply": 0,
            "maybe": 0,
            "average_score": 0.0,
            "last_seen": None,
        })

        record["seen"] += 1
        record["scored"] += 1
        record["last_seen"] = datetime.utcnow().date().isoformat()

        action = job.get("action")
        if action == "Apply":
            record["apply"] += 1
        elif action == "Maybe":
            record["maybe"] += 1

        old_avg = float(record.get("average_score", 0.0))
        old_count = max(record["scored"] - 1, 0)
        new_score = float(job.get("score", 0))

        if record["scored"] > 0:
            record["average_score"] = ((old_avg * old_count) + new_score) / record["scored"]
        else:
            record["average_score"] = new_score

        data[company] = record

    save_company_outcomes(data)


def sync_company_rejections(rejected_companies_count: dict) -> None:
    """
    Update human_rejected_count for every company in company_outcomes.json
    using the counts read from the Google Sheet (col M = "No", col C = company).
    The sheet is the source of truth — any company not in rejected_companies_count
    gets its human_rejected_count reset to 0.
    """
    data = load_company_outcomes()

    # Reset counts for all tracked companies (sheet is source of truth)
    for company_key in data:
        data[company_key]["human_rejected_count"] = rejected_companies_count.get(company_key, 0)

    # Also create stub records for companies rejected on the sheet but not yet tracked
    for company_key, count in rejected_companies_count.items():
        if company_key not in data:
            data[company_key] = {
                "seen": 0,
                "scored": 0,
                "apply": 0,
                "maybe": 0,
                "average_score": 0.0,
                "last_seen": None,
                "human_rejected_count": count,
            }

    save_company_outcomes(data)
    total_rejections = sum(rejected_companies_count.values())
    print(f"[company] Synced rejection counts: {len(rejected_companies_count)} companies, {total_rejections} total 'No' decisions")


def learned_company_boost(company: str) -> int:
    data = load_company_outcomes()
    record = data.get(company.strip().lower())

    if not record:
        return 0

    scored = record.get("scored", 0)
    apply_count = record.get("apply", 0)
    avg_score = record.get("average_score", 0)
    apply_rate = apply_count / scored if scored else 0
    human_rejected = record.get("human_rejected_count", 0)

    if scored < 4 and human_rejected < 3:
        return 0

    boost = 0

    # Strong history of good matches
    if apply_count >= 2:
        boost += 1

    # High average score
    if avg_score >= 80:
        boost += 2
    elif avg_score >= 70:
        boost += 1

    # Strong apply rate
    if apply_rate >= 0.5:
        boost += 1
    elif apply_rate >= 0.3:
        boost += 0.5

    # Human rejection penalty: 3+ "No" decisions with zero applies → rank penalty
    if human_rejected >= 3 and apply_count == 0:
        boost -= 2

    return max(-2, min(int(boost), 3))