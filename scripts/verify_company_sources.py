import json
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

CANDIDATES = [
    {"name": "Stripe", "slug": "stripe"},
    {"name": "Figma", "slug": "figma"},
    {"name": "Databricks", "slug": "databricks"},
    {"name": "Coinbase", "slug": "coinbase"},
    {"name": "Airbnb", "slug": "airbnb"},
]

def check_greenhouse(slug: str) -> bool:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return "jobs" in data
    except (HTTPError, URLError, json.JSONDecodeError):
        return False

def check_lever(slug: str) -> bool:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return isinstance(data, list)
    except (HTTPError, URLError, json.JSONDecodeError):
        return False

def main():
    verified = []

    for candidate in CANDIDATES:
        slug = candidate["slug"]
        name = candidate["name"]

        if check_greenhouse(slug):
            verified.append({"name": name, "ats": "greenhouse", "slug": slug})
            print(f"Verified Greenhouse: {name} ({slug})")
            continue

        if check_lever(slug):
            verified.append({"name": name, "ats": "lever", "slug": slug})
            print(f"Verified Lever: {name} ({slug})")
            continue

        print(f"Not verified: {name} ({slug})")

    with open("config/verified_company_sources.json", "w", encoding="utf-8") as f:
        json.dump(verified, f, indent=2)

if __name__ == "__main__":
    main()