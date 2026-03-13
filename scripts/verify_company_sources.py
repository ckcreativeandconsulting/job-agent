import json
import os
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

CANDIDATES = [
    {"name": "Stripe", "slug": "stripe"},
    {"name": "Brex", "slug": "brex"},
    {"name": "Figma", "slug": "figma"},
    {"name": "Airbnb", "slug": "airbnb"},
    {"name": "Databricks", "slug": "databricks"},
    {"name": "Asana", "slug": "asana"},
    {"name": "Coinbase", "slug": "coinbase"},
    {"name": "Instacart", "slug": "instacart"},
    {"name": "Flexport", "slug": "flexport"},
    {"name": "Lyft", "slug": "lyft"},
    {"name": "Robinhood", "slug": "robinhood"},
    {"name": "Coursera", "slug": "coursera"},
    {"name": "Affirm", "slug": "affirm"},
    {"name": "Gusto", "slug": "gusto"},
    {"name": "Discord", "slug": "discord"},
    {"name": "Samsara", "slug": "samsara"},
    {"name": "Scale AI", "slug": "scaleai"},
    {"name": "Hudl", "slug": "hudl"},
    {"name": "TripActions", "slug": "tripactions"},
    {"name": "Checkr", "slug": "checkr"},
    {"name": "Chime", "slug": "chime"},
    {"name": "Blend", "slug": "blend"},
    {"name": "Alchemy", "slug": "alchemy"},
    {"name": "Webflow", "slug": "webflow"},
    {"name": "Calendly", "slug": "calendly"},
    {"name": "Apollo", "slug": "apollo"},
    {"name": "LaunchDarkly", "slug": "launchdarkly"},
    {"name": "Fastly", "slug": "fastly"},
    {"name": "New Relic", "slug": "newrelic"},
    {"name": "Plaid", "slug": "plaid"},
    {"name": "KPMG", "slug": "kpmg"},
    {"name": "Spotify", "slug": "spotify"},
    {"name": "Medium", "slug": "medium"},
    {"name": "Attentive", "slug": "attentive"},
    {"name": "StackAdapt", "slug": "stackadapt"},
]


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

    verified.sort(key=lambda x: (x["ats"], x["name"].lower()))

    os.makedirs("config", exist_ok=True)

    with open("config/verified_company_sources.json", "w", encoding="utf-8") as f:
        json.dump(verified, f, indent=2)

    print(f"\nSaved {len(verified)} verified company sources.")


if __name__ == "__main__":
    main()