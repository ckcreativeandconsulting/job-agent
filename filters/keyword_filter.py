from config import (
    INCLUDE_KEYWORDS,
    EXCLUDE_KEYWORDS,
    REMOTE_KEYWORDS,
    HYBRID_KEYWORDS,
    HYBRID_ALLOWED_LOCATIONS,
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
        # builder / applied AI signal
        "innovation",
        "applied ai",
        "ai product",
        "ai platform",
        # AI × FinTech Tier 1 titles
        "genai",
        "ai enablement",
        "advisor technology",
        "ai strategy",
        "ai transformation",
        "wealthtech",
        # Tier 2 adjacent titles
        "digital transformation",
        "product operations",
    ]

    for job in jobs:
        title = job.get("title", "").lower()
        summary = job.get("summary", "").lower()
        location = job.get("location", "").lower()

        text = f"{title} {summary}"

        # Exclude obvious junk
        if any(word in text for word in EXCLUDE_KEYWORDS):
            continue

        # Require remote or hybrid signal in either location or summary
        remote_match = any(word in location for word in REMOTE_KEYWORDS) or any(
            word in summary for word in REMOTE_KEYWORDS
        )
        is_hybrid = any(word in location for word in HYBRID_KEYWORDS) or any(
            word in summary for word in HYBRID_KEYWORDS
        )
        if not (remote_match or is_hybrid):
            continue

        # Hybrid-only jobs must be in a commutable Bay Area location.
        # Blank location or bare "hybrid" (no city) → ambiguous, let AI scorer decide.
        if is_hybrid and not remote_match:
            location_ok = (
                not location
                or location.strip() == "hybrid"
                or any(city in location for city in HYBRID_ALLOWED_LOCATIONS)
            )
            if not location_ok:
                continue

        if any(word in title for word in ENGINEERING_EXCLUDE_TITLE_KEYWORDS):
            continue

        # Only apply negative location filter to non-hybrid jobs —
        # a hybrid posting saying "2 days in office" should not be blocked
        if not is_hybrid:
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