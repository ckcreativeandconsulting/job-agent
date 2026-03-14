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


def learned_company_boost(company: str) -> int:
    data = load_company_outcomes()
    record = data.get(company.strip().lower())

    if not record:
        return 0

    scored = record.get("scored", 0)
    apply_count = record.get("apply", 0)
    avg_score = record.get("average_score", 0)
    apply_rate = apply_count / scored if scored else 0

    if scored < 4:
        return 0

    boost = 0

# strong history of good matches
    if apply_count >= 2:
        boost += 1

# high average score
    if avg_score >= 80:
        boost += 2
    elif avg_score >= 70:
        boost += 1

# NEW: strong apply rate
    if apply_rate >= 0.5:
        boost += 1
    elif apply_rate >= 0.3:
        boost += 0.5

    return min(int(boost), 3)