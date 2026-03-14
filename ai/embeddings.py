import math
import requests
from functools import lru_cache

from config import OLLAMA_EMBED_URL, OLLAMA_EMBED_MODEL, OLLAMA_TIMEOUT, PROFILE_FILE


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def embed_text(text: str) -> list[float]:
    clean_text = (text or "").strip()

    if not clean_text:
        return []

    # keep prompts short for stability
    clean_text = clean_text[:1200]

    print(f"[EMBED] model={OLLAMA_EMBED_MODEL} chars={len(clean_text)}")

    response = requests.post(
        OLLAMA_EMBED_URL,
        json={
            "model": OLLAMA_EMBED_MODEL,
            "prompt": clean_text,
        },
        timeout=OLLAMA_TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()

    if "embedding" in data and data["embedding"]:
        return data["embedding"]

    raise RuntimeError(f"Unexpected embedding response: {data}")


@lru_cache(maxsize=1)
def get_profile_embedding() -> list[float]:
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        profile_text = f.read()

    return embed_text(profile_text[:1200])


def job_semantic_similarity(job: dict) -> float:
    profile_embedding = get_profile_embedding()

    job_text = " | ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("summary", "")[:1200],
    ]).strip()

    if not job_text:
        return 0.0

    job_embedding = embed_text(job_text)
    return cosine_similarity(profile_embedding, job_embedding)