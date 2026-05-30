# Job Agent

An AI-powered job discovery and scoring system that replaces manual job searching with an automated, multi-stage pipeline — surfacing the right roles, ranking them by fit, and logging results to a Google Sheets tracker.

---

## Why I Built This

Job searching is one of the most repetitive knowledge-work tasks that exists — scanning postings, pattern-matching against a resume, tracking what you've already seen. It's exactly the kind of work an AI agent should handle.

I built Job Agent as a hands-on exploration of multi-model LLM orchestration: what does it look like to coordinate a local model, a cloud model, and a semantic search layer around a real decision problem with immediate feedback? The job search domain was a perfect forcing function — the stakes are real, the signal is clear (callback or not), and the volume of input data is large enough to make filtering non-trivial.

This project is also part of a broader personal AI ops system ([AI Ops](https://github.com/ckcreativeandconsulting/ai_ops)) that can schedule and trigger Job Agent automatically as part of a unified agent pipeline.

---

## What It Does

A five-stage pipeline runs on demand (or on a schedule via AI Ops):

### 1. Multi-Source Collection
Pulls jobs in parallel from:
- **Greenhouse ATS** — 82 company boards (Stripe, Databricks, Coinbase, Figma, Brex, and more)
- **Lever ATS** — 6 company boards (Plaid, Spotify, etc.)
- **Ashby ATS** — 16 company boards (OpenAI, Ramp, etc.)
- **The Muse API** — public job listings, no auth required
- **RSS feeds** — We Work Remotely and others
- **Manual picks** — paste any ATS or job page URL; title/company auto-enriched via JSON-LD and OG tags

### 2. Smart Filtering
Drops irrelevant roles before any AI runs:
- 80+ keyword rules for include/exclude signals
- US-only location check (blocks India, UK, Canada, EMEA, APAC, and other non-US locations)
- Bay Area hybrid gate — hybrid jobs must be in a commutable SF Bay Area location
- Engineering title exclusion — drops software engineer, ML engineer, architect, etc.

### 3. Keyword Ranking
Scores every surviving job with a multi-factor ranking system:
- 30+ weighted title and summary keywords (e.g. "genai" = +9, "wealthtech" = +8, "sales" = −8)
- Company priority tiers (Tier 1: Stripe, OpenAI, Anthropic = +15; Tier 4: solid companies = +7)
- Employment type preference (contract/interim > full-time)
- Semantic similarity against candidate profile using local `all-minilm` embeddings
- Learned company signal — repeated "No" decisions in the tracker lower future rank scores

### 4. Hybrid AI Scoring
Top-ranked jobs get scored by a two-model pipeline:
- **qwen2.5:14b** (local Ollama) — fast pre-screen; clear misses never reach the cloud
- **gpt-4.1-mini** (OpenAI) — deep evaluation for any job scoring ≥ 75 from Ollama

Each job is scored on four dimensions with an enforced intersection rule:
- `domain_fit_score` — how well the role's industry/domain matches the candidate
- `transformation_fit_score` — AI builder and platform transformation fit
- `scope_fit_score` — seniority and role scope alignment
- `resume_fit_score` — overall background match

**Intersection rule:** a job must score strongly on *both* financial services domain fit *and* AI-builder fit to reach 80+. Strong on only one dimension caps at 75. This reflects callback probability, not theoretical fit.

Each job also gets a `builder_signal` label (High / Medium / Low) indicating how much hands-on 0→1 AI building the role requires.

### 5. Google Sheets Output
Results are appended to a shared tracker with:
- AI score, action (Apply / Maybe / Ignore), and sub-scores
- Why-match bullets and concerns — job-specific, not templated
- Builder signal, employment type, Ollama pre-score
- Deduplication — existing rows are updated, not duplicated
- Feedback loop — marking a row "No" in column M excludes it from future runs and counts toward the company's rejection signal

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Local LLM | Ollama + qwen2.5:14b (pre-screening) |
| Cloud LLM | OpenAI gpt-4.1-mini (final scoring) |
| Optional LLM | Anthropic Claude Haiku (via `AI_MODE=claude`) |
| Embeddings | Ollama + all-minilm (local, cached) |
| Job sources | Greenhouse / Lever / Ashby ATS APIs, The Muse API, RSS |
| Output | Google Sheets via gspread + service account auth |
| Parallelism | ThreadPoolExecutor (collection + scoring) |
| Config | python-dotenv — all settings in `.env` |

---

## Setup

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) (optional — required for `AI_MODE=hybrid` or `ollama_only`)
- OpenAI API key
- Google Cloud service account with Sheets + Drive access

### Install

```bash
git clone https://github.com/ckcreativeandconsulting/job-agent.git
cd job-agent
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# Edit .env — add your OpenAI API key and other settings
```

If using Ollama (recommended for hybrid mode):
```bash
ollama pull qwen2.5:14b
ollama pull all-minilm
```

### Google Sheets Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com) → create a service account
2. Grant it Editor access to your target spreadsheet
3. Download the JSON key file → save as `google_credentials.json` in the project root
4. Create a Google Sheet named **"Job Agent Tracker"** with a tab named **"jobs"**
5. Share the sheet with the service account email

### Candidate Profile

Edit `profile.txt` with your own background. This file drives both the AI scoring prompt and the semantic similarity embedding — it should describe your experience, target roles, and key differentiators in plain text.

### Run

```bash
python main.py
```

---

## Configuration Reference

All settings are controlled via `.env` (see `.env.example` for the full list). Key options:

| Variable | Default | Description |
|---|---|---|
| `AI_MODE` | `openai_only` | `hybrid` \| `openai_only` \| `ollama_only` \| `claude` |
| `HYBRID_OPENAI_THRESHOLD` | `75` | Ollama score threshold to trigger OpenAI re-score |
| `MAX_AI_JOBS` | `25` | Max auto-sourced jobs scored per run |
| `OPENAI_MODEL` | `gpt-4.1-mini` | OpenAI model for scoring |
| `OLLAMA_MODEL` | `qwen2.5:14b` | Local Ollama model for pre-screening |
| `GOOGLE_CREDENTIALS_FILE` | `google_credentials.json` | Path to service account JSON |

---

## How It Fits the Bigger Picture

Job Agent is part of a personal AI operations stack:

```
AI Ops (Orchestrator)
├── Job Agent          ← this repo
├── Trading Agent      (daily market briefing)
└── Ops Briefing       (aggregated daily digest)
```

[AI Ops](https://github.com/ckcreativeandconsulting/ai_ops) can schedule Job Agent on a cadence, collect its output, and route results — so the full pipeline runs with minimal manual intervention.

---

## Key Design Decisions

- **Local-first for cost**: Ollama handles 100% of pre-screening at zero API cost. Only the top candidates touch OpenAI.
- **Intersection rule over averaging**: A job that's strong on AI fit but has no financial services context is capped at 75 — because callback probability depends on *both* dimensions, not their average.
- **Feedback loop from the tracker**: Human decisions ("Yes"/"No" in the sheet) feed back into the ranking system, lowering scores for companies that consistently surface poor matches.
- **Enrichment over manual data entry**: Paste a URL; title, company, and summary are scraped automatically from Greenhouse, Ashby, Lever, and other ATS pages via JSON-LD and OG tags.

---

## About

Built by [Charles Kang](https://charleskang.com) · [LinkedIn](https://www.linkedin.com/in/ck-charleskang) · Part of the CK Creative and Consulting AI portfolio
