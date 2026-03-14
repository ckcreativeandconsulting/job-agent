# CLAUDE.md — Job Agent App

## Project Overview
A Python-based autonomous job agent that scrapes custom job boards, uses Ollama (local LLM) and OpenAI APIs to process and evaluate listings, and outputs structured results for downstream consumption (used by the AI Ops briefing app).

---

## Architecture

- **Language**: Python 3.10+
- **AI Providers**: Ollama (local) and OpenAI — abstracted behind a provider interface; do not call either API directly from business logic
- **Scraping**: Custom job board scrapers — keep each scraper isolated in its own module
- **Output**: Structured data (JSON or similar) consumed by the AI Ops briefing app — do not change output schema without explicit instruction

---

## AI Provider Rules

- All LLM calls must go through a single provider abstraction layer (e.g., `services/llm_provider.py`) — never instantiate `openai.Client` or call `ollama` directly in business logic
- The provider interface must support swapping between Ollama, OpenAI, and future providers (e.g., Anthropic Claude) with a config change, not a code change
- Always include retry logic with exponential backoff on LLM API calls — they fail; handle it gracefully
- Log every LLM call: provider used, model, prompt token estimate, and response time — use structured logging, not print statements
- Prompt strings must live in a dedicated `prompts/` directory or a prompts module — never hardcode prompts inline in business logic

---

## Scraping Rules

- Each job board gets its own scraper class/module in `scrapers/`
- Scrapers must be polite: include delays between requests, respect `robots.txt` where applicable
- Use `requests` + `BeautifulSoup` or `playwright` — flag if a different library is needed and why
- Never store raw HTML — parse and store only structured extracted fields
- All scrapers must return a consistent data schema (same fields) regardless of source board

---

## Coding Standards

- **Type hints**: Required on all function signatures and class attributes — use `from __future__ import annotations` at the top of each file
- **Docstrings**: Required on all public functions and classes — use Google style
- **Error handling**: Never use bare `except:` — always catch specific exceptions and log them
- **Logging**: Use Python's `logging` module with structured output — no `print()` statements
- **Config**: All secrets and config (API keys, URLs, model names) via environment variables or a `.env` file — never hardcoded; use `python-dotenv`
- **Dependencies**: Managed via `requirements.txt` or `pyproject.toml` — flag any new dependency before adding it

---

## File Structure
```
scrapers/           # One file per job board scraper
services/
  llm_provider.py   # Provider abstraction (Ollama / OpenAI / etc.)
  job_evaluator.py  # Scoring and filtering logic
prompts/            # All prompt templates
models/             # Data models / dataclasses / Pydantic schemas
output/             # Generated output files consumed by App 3
utils/              # Helpers, retry logic, logging setup
config.py           # Loads env vars and app configuration
main.py             # Entry point
```

---

## Output Contract (important — App 3 depends on this)

- Output must be valid JSON written to `output/jobs_<YYYY-MM-DD>.json`
- Schema changes require explicit approval — the AI Ops briefing app reads this file
- Always include at minimum: `title`, `company`, `url`, `source_board`, `scraped_at`, `score`, `summary`

---

## What NOT to Do

- Do not make LLM calls without going through the provider abstraction layer
- Do not hardcode API keys, model names, or job board URLs in source files
- Do not change the output JSON schema without flagging it
- Do not use `time.sleep()` as the only retry mechanism — use proper backoff
- Do not add scraping targets without confirming the target's terms of service are acceptable

---

## Testing

- Unit test each scraper with fixture HTML — do not hit live sites in tests
- Unit test the provider abstraction with mocked LLM responses
- Use `pytest` — place tests in `/tests/` mirroring the source structure

---

## Git

- Commit messages: imperative mood — e.g., `Add retry logic to OpenAI provider`
- Never commit `.env` files or API keys
- Tag output schema changes clearly in commit messages: `[BREAKING] Update output schema — add salary_range field`
