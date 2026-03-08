import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from config import PROFILE_FILE, APPLY_THRESHOLD, MAYBE_THRESHOLD

load_dotenv()

client = OpenAI()


def load_profile_text() -> str:
    return Path(PROFILE_FILE).read_text(encoding="utf-8")


def classify_action(score: int) -> str:
    if score >= APPLY_THRESHOLD:
        return "Apply"
    if score >= MAYBE_THRESHOLD:
        return "Maybe"
    return "Ignore"


def extract_json(text: str):
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
            "why_match": ["Model response parsing failed"],
            "concerns": ["Could not parse JSON"],
            "employment_type_label": "Unknown",
        }


def score_job(job: dict) -> dict:
    profile_text = load_profile_text()

    prompt = f"""
Evaluate this job for candidate Charles Kang.

Candidate profile:
{profile_text}

Job:
Title: {job.get("title","")}
Company: {job.get("company","")}
Location: {job.get("location","")}
Summary: {job.get("summary","")}

Respond ONLY with JSON like this:

{{
"score": 85,
"why_match": ["reason1","reason2"],
"concerns": ["issue1"],
"employment_type_label": "Full-time"
}}

Rules:
- score from 0 to 100
- prefer enterprise platform transformation, modernization, system consolidation, governance, and operating model roles
- prefer remote roles
- slightly favor contract roles
- score remote full-time roles well if they strongly match platform transformation work
- penalize customer implementation, client delivery, onboarding, services, or post-sales roles unless they clearly involve enterprise platform transformation at scale
- penalize junior, sales, or heavily customer-support-oriented roles
- be conservative: only assign scores above 85 for strong matches
- penalize roles that are primarily embedded within a single business function (for example claims, customer operations, or customer implementation) unless they clearly involve enterprise-wide platform transformation, large-scale system modernization, or operating model redesign across multiple teams or systems.
- Do not over-score roles solely because they mention AI. AI-related roles should only receive high scores if they involve enterprise platform transformation, operating model redesign, governance, or large-scale system modernization.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    raw_text = response.output_text

    parsed = extract_json(raw_text)

    score = int(parsed.get("score", 50))
    parsed["score"] = score
    parsed["action"] = classify_action(score)

    return parsed