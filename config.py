from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

MAX_AI_JOBS = int(os.getenv("MAX_AI_JOBS", 10))


# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

RAW_JOBS_FILE = DATA_DIR / "raw_jobs.json"
FILTERED_JOBS_FILE = DATA_DIR / "filtered_jobs.json"
SCORED_JOBS_FILE = DATA_DIR / "scored_jobs.json"
MANUAL_LINKEDIN_JOBS_FILE = DATA_DIR / "manual_linkedin_jobs.json"

PROFILE_FILE = BASE_DIR / "profile.txt"

# Job filtering keywords
INCLUDE_KEYWORDS = [
    "platform",
    "transformation",
    "modernization",
    "integration",
    "enterprise",
    "program",
    "operating model",
    "governance",
    "systems",
    "migration",
    "consolidation",
]

EXCLUDE_KEYWORDS = [
    "onsite only",
    "entry level",
    "junior",
    "campus",
    "sales representative",
    "customer support",
    "field sales",
    "door to door",
]

ENGINEERING_EXCLUDE_TITLE_KEYWORDS = [
    "engineer",
    "engineering manager",
    "software engineer",
    "staff engineer",
    "senior engineer",
    "principal engineer",
    "developer",
    "architect",
    "machine learning engineer",
    "ml engineer",
    "data engineer",
    "site reliability",
    "sre",
]

REMOTE_KEYWORDS = [
    "remote",
    "work from home",
    "distributed",
]

NEGATIVE_LOCATION_KEYWORDS = [
    "hybrid",
    "onsite",
    "on-site",
    "in office",
    "office-based",
]

RANKING_TITLE_WEIGHTS = {
    "program manager": 7,
    "program director": 8,
    "transformation": 8,
    "platform": 3,
    "modernization": 7,
    "operating": 4,
    "delivery lead": 5,
    "product manager": 2,
    "strategy": 1,
    "operations": 1,
}

RANKING_SUMMARY_WEIGHTS = {
    "operating model": 7,
    "governance": 6,
    "modernization": 5,
    "consolidation": 8,
    "integration": 4,
    "enterprise": 3,
    "cross-functional": 3,
    "regulated": 3,
    "financial services": 4,
    "wealth": 3,
    "platform": 3,
    "transformation": 4,
}

RANKING_EMPLOYMENT_WEIGHTS = {
    "contract": 3,
    "interim": 3,
    "temporary": 2,
    "fractional": 2,
    "full-time": 1,
    "full time": 1,
    "fte": 1,
}

RANKING_NEGATIVE_TITLE_WEIGHTS = {
    "engineer": -8,
    "developer": -8,
    "architect": -6,
    "customer success": -7,
    "implementation": -5,
    "support": -6,
    "sales": -8,
    "marketing": -6,
    "campaign": -7,
    "growth": -5,
    "account executive": -10,
}

RANKING_NEGATIVE_SUMMARY_WEIGHTS = {
    "customer implementation": -6,
    "client delivery": -5,
    "post-sales": -6,
    "quota": -10,
    "territory": -10,
    "on-call": -4,
    "marketing operations": -6,
    "campaign management": -7,
    "campaign production": -7,
    "demand generation": -7,
    "product-led growth": -6,
    "customer lifecycle": -5,
}

GREENHOUSE_COMPANIES = [
    "stripe",
    "brex",
]

LEVER_COMPANIES = [
    # add later as needed
]

# Scoring thresholds
APPLY_THRESHOLD = 85
MAYBE_THRESHOLD = 70

# Runtime settings
MAX_JOBS_PER_RUN = 50

MIN_RANK_SCORE = 16

MAX_JOBS_PER_COMPANY = 4