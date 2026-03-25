from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

MAX_AI_JOBS = int(os.getenv("MAX_AI_JOBS", 20))
COLLECTOR_MAX_WORKERS = int(os.getenv("COLLECTOR_MAX_WORKERS", 10))
SCORER_MAX_WORKERS = int(os.getenv("SCORER_MAX_WORKERS", 5))
EMBED_CANDIDATE_LIMIT = int(os.getenv("EMBED_CANDIDATE_LIMIT", 30))
EMBEDDING_CACHE_ENABLED = os.getenv("EMBEDDING_CACHE_ENABLED", "true").lower() == "true"
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")

AI_MODE = os.getenv("AI_MODE", "openai_only")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", 90))
# embeddings
OLLAMA_EMBED_URL = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434/api/embed")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "all-minilm")

SEMANTIC_WEIGHT = float(os.getenv("SEMANTIC_WEIGHT", 12))
SEMANTIC_MIN_SIM = float(os.getenv("SEMANTIC_MIN_SIM", 0.30))


HYBRID_OPENAI_THRESHOLD = int(os.getenv("HYBRID_OPENAI_THRESHOLD", 90))


# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

RAW_JOBS_FILE = DATA_DIR / "raw_jobs.json"
FILTERED_JOBS_FILE = DATA_DIR / "filtered_jobs.json"
SCORED_JOBS_FILE = DATA_DIR / "scored_jobs.json"
EMBEDDING_CACHE_FILE = DATA_DIR / "embedding_cache.json"
MANUAL_LINKEDIN_JOBS_FILE = DATA_DIR / "manual_linkedin_jobs.json"

PROFILE_FILE = BASE_DIR / "profile.txt"

# The Muse API — set to False to disable
THEMUSE_ENABLED = os.getenv("THEMUSE_ENABLED", "true").lower() == "true"

# Indeed RSS search feeds — set to [] to disable
RSS_URLS = [
    # Indeed RSS — currently blocked (returns 0 entries); kept for if it recovers
    "https://www.indeed.com/rss?q=senior+product+manager+platform&l=remote&sort=date",
    "https://www.indeed.com/rss?q=program+manager+transformation&l=remote&sort=date",
    "https://www.indeed.com/rss?q=enterprise+platform+program+manager&l=remote&sort=date",
    "https://www.indeed.com/rss?q=contract+interim+product+manager&l=remote&sort=date",
    # We Work Remotely — product + management categories (working)
    "https://weworkremotely.com/categories/remote-product-jobs.rss",
]

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

HYBRID_KEYWORDS = [
    "hybrid",
]

NEGATIVE_LOCATION_KEYWORDS = [
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
    "infrastructure": 5,
    "internal systems": 5,
    "group product manager": 6,
    "product lead": 5,
    "principal product": 4,
    "advisor": 3,
}

RANKING_SUMMARY_WEIGHTS = {
    "operating model": 7,
    "governance": 6,
    "modernization": 5,
    "consolidation": 8,
    "integration": 4,
    "enterprise": 3,
    "cross-functional": 3,
    "regulated": 4,
    "financial services": 4,
    "wealth": 3,
    "wealth management": 4,
    "platform": 3,
    "transformation": 4,
    "internal systems": 5,
    "infrastructure": 5,
    "api-first": 4,
    "control plane": 6,
    "harmonize": 5,
    "unify": 4,
    "decommission": 4,
    "legacy modernization": 4,
    "advisor": 3,
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
    "regulatory": -3,
    "risk": -2,
    "alliances": -5,
    "channels": -5,
    "claims": -6,
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
    "claims": -6,
    "third party risk": -5,
    "regulatory risk": -5,
    "alliances": -5,
    "channels": -5,
    "content development": -6,
    "training": -4,
    "adoption": -3,
    "communication": -3,
    "within the claims organization": -8,
    "risk operations": -4,
    "content solutions": -5,
    "alliances and channels": -6,
}

COMPANY_PRIORITY = {

    # Tier 1 – top targets
    "stripe": 15,
    "databricks": 15,
    "snowflake": 15,
    "openai": 15,
    "anthropic": 15,

    # Tier 2 – very strong companies
    "coinbase": 12,
    "mongodb": 12,
    "cloudflare": 12,
    "okta": 12,
    "confluent": 12,
    "snowflake": 12,

    # Tier 3 – strong tech companies
    "figma": 10,
    "notion": 10,
    "airbnb": 10,
    "asana": 10,
    "flexport": 10,
    "instacart": 10,
    "samsara": 10,
    "brex": 10,
    "affirm": 10,
    "plaid": 10,
    "ramp": 10,
    "linear": 10,
    "cursor": 10,

    # Tier 3 (continued) – strong AI/product companies
    "cohere": 10,
    "perplexity": 10,

    # Tier 4 – solid companies
    "chime": 7,
    "bill.com": 7,
    "webflow": 7,
    "launchdarkly": 7,
    "fastly": 7,
    "new relic": 7,
    "checkr": 7,
    "scale ai": 7,
    "ironclad": 7,
    "vanta": 7,
    "rubrik": 7,
    "grafana labs": 7,
    "deel": 7,
    "zapier": 7,
    "supabase": 7,
    "pagerduty": 5,
    "modal": 5,
    "airbyte": 5,
    "betterment": 10,   # wealth management platform, direct domain overlap
    "sofi": 7,
    "marqeta": 7,

    # Tier 5 – neutral companies
    # (anything not listed gets 0)
}

# Boost applied to companies where the user has already applied (read from sheet col M)
APPLIED_COMPANY_BOOST = 10

GREENHOUSE_COMPANIES = [
    "stripe",
    "brex",
    "figma",
    "airbnb",
    "databricks",
    "asana",
    "coinbase",
    "instacart",
    "flexport",
    "lyft",
    "robinhood",
    "coursera",
    "affirm",
    "gusto",
    "discord",
    "samsara",
    "scaleai",
    "hudl",
    "tripactions",
    "checkr",
    "chime",
    "blend",
    "alchemy",
    "webflow",
    "calendly",
    "apollo",
    "launchdarkly",
    "fastly",
    "newrelic",
    ]

LEVER_COMPANIES = [
    "plaid",
    "kpmg",
    "spotify",
    "medium",
    "attentive",
    "stackadapt",
    ]

COMPANY_SOURCES = [
    {"name": "Stripe", "ats": "greenhouse", "slug": "stripe"},
    {"name": "Brex", "ats": "greenhouse", "slug": "brex"},
    {"name": "Databricks", "ats": "greenhouse", "slug": "databricks"},
    {"name": "Coinbase", "ats": "greenhouse", "slug": "coinbase"},
    {"name": "Figma", "ats": "greenhouse", "slug": "figma"},
    {"name": "Airbnb", "ats": "greenhouse", "slug": "airbnb"},
    {"name": "Asana", "ats": "greenhouse", "slug": "asana"},
]


# Scoring thresholds
APPLY_THRESHOLD = 80
MAYBE_THRESHOLD = 70

# Runtime settings
MAX_JOBS_PER_RUN = 50

MIN_RANK_SCORE = 18

MAX_JOBS_PER_COMPANY = 4