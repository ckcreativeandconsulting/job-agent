import feedparser
from config import RSS_URLS, MAX_JOBS_PER_RUN


def fetch_indeed_jobs() -> list[dict]:
    jobs = []

    for url in RSS_URLS:
        print(f"Checking feed: {url}")
        feed = feedparser.parse(url)

        print(f"Feed entries found: {len(feed.entries)}")

        for entry in feed.entries:
            job = {
                "title": getattr(entry, "title", "").strip(),
                "company": getattr(entry, "author", "Unknown").strip() if hasattr(entry, "author") else "Unknown",
                "summary": getattr(entry, "summary", "").strip(),
                "link": getattr(entry, "link", "").strip(),
                "source": "Indeed",
                "location": "Unknown",
                "employment_type": "Unknown",
            }
            jobs.append(job)

            if len(jobs) >= MAX_JOBS_PER_RUN:
                return jobs

    return jobs