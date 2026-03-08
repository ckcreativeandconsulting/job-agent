from config import (
    INCLUDE_KEYWORDS,
    EXCLUDE_KEYWORDS,
    REMOTE_KEYWORDS,
    ENGINEERING_EXCLUDE_TITLE_KEYWORDS,
    NEGATIVE_LOCATION_KEYWORDS,
)


def keyword_filter(jobs: list[dict]) -> list[dict]:
    filtered = []

    strong_title_keywords = [
        "platform",
        "transformation",
        "program",
        "modernization",
        "integration",
        "enterprise",
        "operations",
        "delivery",
        "product manager",
        "program manager",
        "program director",
    ]

    for job in jobs:
        title = job.get("title", "").lower()
        summary = job.get("summary", "").lower()
        location = job.get("location", "").lower()

        text = f"{title} {summary}"

        # Exclude obvious junk
        if any(word in text for word in EXCLUDE_KEYWORDS):
            continue

        # Require remote signal in either location or summary
        remote_match = any(word in location for word in REMOTE_KEYWORDS) or any(
            word in summary for word in REMOTE_KEYWORDS
        )
        if not remote_match:
            continue

        if any(word in title for word in ENGINEERING_EXCLUDE_TITLE_KEYWORDS):
            continue

        negative_location_match = any(word in location for word in NEGATIVE_LOCATION_KEYWORDS) or any(
            word in summary for word in NEGATIVE_LOCATION_KEYWORDS
        )
        if negative_location_match:
            continue

        # Require at least one strong keyword in title
        title_match = any(word in title for word in strong_title_keywords)

        # Require at least two include keywords overall
        include_count = sum(1 for word in INCLUDE_KEYWORDS if word in text)

        if title_match and include_count >= 2:
            filtered.append(job)

    return filtered