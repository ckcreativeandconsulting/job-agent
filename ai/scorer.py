import json
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI

from config import (
    PROFILE_FILE,
    APPLY_THRESHOLD,
    MAYBE_THRESHOLD,
    HYBRID_OPENAI_THRESHOLD,
    AI_MODE,
    OPENAI_MODEL,
    OLLAMA_MODEL,
    OLLAMA_URL,
    OLLAMA_TIMEOUT,
    CLAUDE_MODEL,
)

load_dotenv()

client = OpenAI()
_claude_client = None
_PROFILE_TEXT = None


def get_claude_client():
    global _claude_client
    if _claude_client is None:
        import anthropic
        _claude_client = anthropic.Anthropic()
    return _claude_client


def load_profile_text() -> str:
    global _PROFILE_TEXT
    if _PROFILE_TEXT is None:
        _PROFILE_TEXT = Path(PROFILE_FILE).read_text(encoding="utf-8")
    return _PROFILE_TEXT


def classify_action(score: int) -> str:
    if score >= APPLY_THRESHOLD:
        return "Apply"
    if score >= MAYBE_THRESHOLD:
        return "Maybe"
    return "Ignore"


def coerce_score(value, default: int = 50) -> int:
    try:
        score = int(float(value))
    except (TypeError, ValueError):
        return default

    return max(0, min(100, score))


def extract_json(text: str) -> dict:
    """
    Safely extract JSON from model output.
    """
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {
            "score": 50,
            "resume_fit_score": 50,
            "transformation_fit_score": 50,
            "domain_fit_score": 50,
            "scope_fit_score": 50,
            "why_match": ["Model response parsing failed"],
            "concerns": ["Could not parse JSON"],
            "employment_type_label": "Unknown",
            "builder_signal": "Low",
        }


def build_prompt(job: dict, profile_text: str) -> str:
    candidate_name = profile_text.split('\n')[0].strip()
    return f"""
Evaluate this job for candidate {candidate_name}. Your goal is to assess the PROBABILITY OF CALLBACK — not theoretical fit, but whether a real hiring manager at this specific company would bring this candidate in for an interview based on this posting.

Candidate profile:
{profile_text}

Job:
Title: {job.get("title", "")}
Company: {job.get("company", "")}
Location: {job.get("location", "")}
Summary: {job.get("summary", "")}

Respond ONLY with JSON like this:

{{
  "score": 85,
  "resume_fit_score": 82,
  "transformation_fit_score": 90,
  "domain_fit_score": 75,
  "scope_fit_score": 80,
  "why_match": [
  "<specific reason tied to this job's actual requirements>",
  "<specific reason 2>"
],
"concerns": [
  "<specific concern about this particular role>"
],
  "employment_type_label": "Full-time",
  "builder_signal": "Medium — <one sentence on this specific role's 0→1 or AI builder characteristics>"
}}

Rules:
- score from 0 to 100
- resume_fit_score from 0 to 100
- transformation_fit_score from 0 to 100
- domain_fit_score from 0 to 100
- scope_fit_score from 0 to 100
- employment_type_label: infer from the job posting — one of "Contract", "Interim", "Fractional", "Part-time", "Full-time", or "Unknown"
- why_match and concerns must be concrete and job-specific
- never return placeholder text like "reason1", "reason2", or "issue1"
- prefer enterprise platform transformation, modernization, system consolidation, governance, and operating model roles
- remote roles are preferred; remote-friendly hybrid roles (a few days in office) are also acceptable — do not penalize hybrid if the posting signals remote-first or flexible
- all employment types are acceptable (contract, interim, fractional, part-time, full-time); contract and interim receive a slight preference over full-time
The candidate's value proposition has three anchors — ALL THREE must be present in a strong match:
  ANCHOR 1 (Financial Services Domain): 12+ years in wealth management, advisor platforms, regulated financial systems. This is the primary differentiator. Weight domain_fit_score highest for: WealthTech, FinTech, Payments, Banking Tech, Investment Platforms, Advisor Technology, Financial Infrastructure SaaS.
  ANCHOR 2 (AI Product Builder): Hands-on builder of AI agents, LLM pipelines, and agentic workflows — not a PM who managed AI features, but someone who built systems. Weight transformation_fit_score highest for roles that require building AI-native products, GenAI workflows, or 0→1 AI platforms from scratch.
  ANCHOR 3 (Independent Senior Execution): Operates as a senior IC, fractional leader, or interim executive — not a large org manager. Weight scope_fit_score highest for roles suited to a hands-on leader who can own a product or program independently.

INTERSECTION RULE — this is critical for the overall score:
  - Dual fit (BOTH Anchor 1 strong AND Anchor 2 strong): overall score can reach 80–95
  - Single-dimension only (strong on ONE anchor, weak on the other): cap overall score at 75 max
  - Neither anchor strong: score 65 or below
  - The overall score must reflect callback probability, not theoretical interest
BEFORE returning your JSON: check domain_fit_score and transformation_fit_score. If domain_fit_score is below 65, overall score MUST be 65 or lower. If EITHER domain_fit_score OR transformation_fit_score is below 70, overall score MUST be 75 or lower. Adjust score before outputting if needed.
- do not over-score pure people-manager Director+ roles at large tech companies unless they explicitly involve hands-on platform transformation execution and the scope matches a senior IC or transformation leader, not a large org lead
- penalize customer implementation, client delivery, onboarding, services, or post-sales roles — these are not product leadership roles
- penalize roles that require a deep CS or engineering background: model training, ML infrastructure, distributed systems engineering, or roles where a CS/engineering degree is listed as required or strongly preferred
- penalize pure AI/ML research roles (research scientist, ML researcher, deep learning) — no practitioner fit
- penalize roles at general tech companies with no financial services context unless Anchor 2 is exceptionally strong (score AI-only roles without FS overlap at 65 max)
- penalize "Founding X" or early-stage startup roles that require broad technical generalist depth — these do not fit the senior PM / fractional leader profile
- penalize roles embedded in a single narrow business function (claims, customer ops) with no cross-functional transformation scope
- penalize generic PM roles that only mention AI in passing ("we use AI tools") without substantive AI product ownership
- penalize junior, sales, or heavily customer-support-oriented roles
- Score calibration (callback-oriented):
  90–100: Exceptional dual fit (AI + FS) — clear match on both anchors, scope is right — apply immediately
  80–89: Strong dual fit — one or both anchors is solid, minor gaps — strong maybe / apply
  72–79: Single-dimension fit only — acceptable match on one anchor, weak on the other — maybe, with reservations
  65–71: Weak fit overall — surface only if specifically notable — lean ignore
  Below 65: Do not score above this for roles with no FS context, deep engineering requirements, or research roles
- be conservative: when uncertain, score lower — a 75 should mean "real probability of interest," not "theoretically possible"
- resume_fit_score: how well the candidate's background matches the role overall
- transformation_fit_score: fit for enterprise platform transformation, modernization, system consolidation, governance, and operating model work
- domain_fit_score: fit for the company/domain/problem space (score higher for financial services, fintech, regulated environments, advisor platforms)
- scope_fit_score: fit for level, complexity, and cross-functional scale (benchmark: Senior PM / Group PM / Product Lead at a mid-to-large tech company, or senior interim transformation leader)
- overall score should reflect the total opportunity; do not inflate solely because one subscore is high
- builder_signal: start with "High", "Medium", or "Low" then 1 sentence explaining the 0→1 / applied AI builder characteristics of the role (or lack thereof)
""".strip()


def normalize_parsed_result(parsed: dict) -> dict:
    score = coerce_score(parsed.get("score", 50))
    parsed["score"] = score
    parsed["action"] = classify_action(score)
    parsed["resume_fit_score"] = coerce_score(parsed.get("resume_fit_score", parsed.get("score", 50)))
    parsed["transformation_fit_score"] = coerce_score(parsed.get("transformation_fit_score", parsed.get("score", 50)))
    parsed["domain_fit_score"] = coerce_score(parsed.get("domain_fit_score", parsed.get("score", 50)))
    parsed["scope_fit_score"] = coerce_score(parsed.get("scope_fit_score", parsed.get("score", 50)))

    if not isinstance(parsed.get("why_match"), list):
        parsed["why_match"] = ["Model did not return valid why_match list"]

    if not isinstance(parsed.get("concerns"), list):
        parsed["concerns"] = ["Model did not return valid concerns list"]

    if not parsed.get("employment_type_label"):
        parsed["employment_type_label"] = "Unknown"

    if not parsed.get("builder_signal"):
        parsed["builder_signal"] = "Low"

    return parsed


def score_job_openai(job: dict, profile_text: str) -> dict:
    prompt = build_prompt(job, profile_text)

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt,
    )

    raw_text = response.output_text
    parsed = extract_json(raw_text)
    parsed["backend"] = "openai"
    parsed["model"] = OPENAI_MODEL

    return normalize_parsed_result(parsed)


def score_job_ollama(job: dict, profile_text: str) -> dict:
    prompt = build_prompt(job, profile_text)

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=OLLAMA_TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()
    raw_text = data.get("response", "")

    parsed = extract_json(raw_text)
    parsed["backend"] = "ollama"
    parsed["model"] = OLLAMA_MODEL

    return normalize_parsed_result(parsed)


def score_job_claude(job: dict, profile_text: str) -> dict:
    prompt = build_prompt(job, profile_text)

    claude = get_claude_client()
    response = claude.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text
    parsed = extract_json(raw_text)
    parsed["backend"] = "claude"
    parsed["model"] = CLAUDE_MODEL

    return normalize_parsed_result(parsed)


def score_job_hybrid(job: dict, profile_text: str) -> dict:
    try:
        rough = score_job_ollama(job, profile_text)

        if rough["score"] >= HYBRID_OPENAI_THRESHOLD:
            final = score_job_openai(job, profile_text)
            final["pre_score"] = rough["score"]
            final["pre_backend"] = "ollama"
            return final

        return rough

    except Exception as e:
        fallback = score_job_openai(job, profile_text)
        fallback["fallback_reason"] = "ollama_failed"
        fallback["fallback_error"] = str(e)
        return fallback


def score_job(job: dict) -> dict:
    profile_text = load_profile_text()

    if AI_MODE == "ollama_only":
        try:
            return score_job_ollama(job, profile_text)
        except Exception as e:
            return {
                "score": 50,
                "why_match": ["Ollama scoring failed"],
                "concerns": [str(e)],
                "employment_type_label": "Unknown",
                "action": classify_action(50),
                "backend": "ollama",
                "model": OLLAMA_MODEL,
            }

    if AI_MODE == "hybrid":
        return score_job_hybrid(job, profile_text)

    if AI_MODE == "claude":
        return score_job_claude(job, profile_text)

    return score_job_openai(job, profile_text)