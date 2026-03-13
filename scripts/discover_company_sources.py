import json
import os
import re
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError, URLError


CANDIDATES_FILE = Path("config/discovery_candidates.json")
VERIFIED_FILE = Path("config/verified_company_sources.json")


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = slug.replace("&", "and")
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "", slug)
    return slug


def generate_slug_candidates(name: str) -> list[str]:
    base = slugify(name)

    variants = {
        base,
        base.replace("inc", ""),
        base.replace("labs", ""),
        base.replace("tech", ""),
        base.replace("ai", "ai"),
    }

    # common alternates
    if " " in name.strip():
        compact = re.sub(r"\s+", "", name.lower())
        hyphen = re.sub(r"\s+", "-", name.lower())
        variants.add(re.sub(r"[^a-z0-9-]", "", compact))
        variants.add(re.sub(r"[^a-z0-9-]", "", hyphen))

    # hand-tuned alternates for common patterns
    if base.endswith("ai"):
        variants.add(base.replace("ai", ""))
    if "newrelic" in base:
        variants.add("newrelic")
    if "launchdarkly" in base:
        variants.add("launchdarkly")
    if "scaleai" in base:
        variants.add("scaleai")

    return [v for v in sorted(variants) if v]


def check_greenhouse(slug: str) -> bool:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return isinstance(data, dict) and "jobs" in data and isinstance(data["jobs"], list)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return False


def check_lever(slug: str) -> bool:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return isinstance(data, list)
    except TimeoutError:
        print(f"Timeout checking Lever: {slug}")
        return False
    except (HTTPError, URLError, json.JSONDecodeError):
        return False


def load_candidates() -> list[str]:
    if not CANDIDATES_FILE.exists():
        return []
    with CANDIDATES_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_verified() -> list[dict]:
    if not VERIFIED_FILE.exists():
        return []
    with VERIFIED_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_verified(records: list[dict]) -> None:
    os.makedirs("config", exist_ok=True)
    records = sorted(records, key=lambda x: (x["ats"], x["name"].lower(), x["slug"]))
    with VERIFIED_FILE.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def main():
    candidates = load_candidates()
    existing = load_verified()

    existing_keys = {(r["name"].lower(), r["ats"], r["slug"]) for r in existing}
    verified = existing[:]

    added_count = 0

    for name in candidates:
        found = False
        slug_candidates = generate_slug_candidates(name)

        for slug in slug_candidates:
            if check_greenhouse(slug):
                record = {"name": name, "ats": "greenhouse", "slug": slug}
                key = (name.lower(), "greenhouse", slug)
                if key not in existing_keys:
                    verified.append(record)
                    existing_keys.add(key)
                    added_count += 1
                    print(f"Verified Greenhouse: {name} ({slug})")
                found = True
                break

            if check_lever(slug):
                record = {"name": name, "ats": "lever", "slug": slug}
                key = (name.lower(), "lever", slug)
                if key not in existing_keys:
                    verified.append(record)
                    existing_keys.add(key)
                    added_count += 1
                    print(f"Verified Lever: {name} ({slug})")
                found = True
                break

        if not found:
            print(f"Not verified: {name}")

    save_verified(verified)
    print(f"\nAdded {added_count} new verified company sources.")
    print(f"Total verified company sources: {len(verified)}")


if __name__ == "__main__":
    main()