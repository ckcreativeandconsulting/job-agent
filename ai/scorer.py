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
)

load_dotenv()

client = OpenAI()
_PROFILE_TEXT = None


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
        }


def build_prompt(job: dict, profile_text: str) -> str:
    return f"""
Evaluate this job for candidate Charles Kang.

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
  "why_match": ["reason1", "reason2"],
  "concerns": ["issue1"],
  "employment_type_label": "Full-time"
}}

Rules:
- score from 0 to 100
- resume_fit_score from 0 to 100
- transformation_fit_score from 0 to 100
- domain_fit_score from 0 to 100
- scope_fit_score from 0 to 100
- prefer enterprise platform transformation, modernization, system consolidation, governance, and operating model roles
- prefer remote roles
- slightly favor contract roles
- score remote full-time roles well if they strongly match platform transformation work
- penalize customer implementation, client delivery, onboarding, services, or post-sales roles unless they clearly involve enterprise platform transformation at scale
- penalize junior, sales, or heavily customer-support-oriented roles
- be conservative: only assign scores above 85 for strong matches
- penalize roles that are primarily embedded within a single business function (for example claims, customer operations, or customer implementation) unless they clearly involve enterprise-wide platform transformation, large-scale system modernization, or operating model redesign across multiple teams or systems
- do not over-score roles solely because they mention AI
- for prescoring, be strict and avoid scores above 85 unless the role is an unusually strong fit
- resume_fit_score: how well the candidate's background matches the role overall
- transformation_fit_score: fit for enterprise platform transformation, modernization, system consolidation, governance, and operating model work
- domain_fit_score: fit for the company/domain/problem space
- scope_fit_score: fit for level, complexity, and cross-functional scale
- overall score should reflect the total opportunity, but do not inflate it solely because one subscore is high
- be especially strict: only assign scores above 90 for unusually strong matches, and use 70-85 for decent but not exceptional fits
- AI-related roles should only receive high scores if they involve enterprise platform transformation, operating model redesign, governance, or large-scale system modernization
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

    return score_job_openai(job, profile_text)