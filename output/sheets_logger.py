import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
from pathlib import Path


SHEET_NAME = "Job Agent Tracker"
TAB_NAME = "jobs"


def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "google_credentials.json", scope
    )

    client = gspread.authorize(creds)

    return client.open(SHEET_NAME).worksheet(TAB_NAME)


def append_jobs(jobs):

    sheet = get_sheet()

    # Read existing links from column K
    existing_links = set(sheet.col_values(11)[1:])  # skip header

    today = datetime.utcnow().strftime("%Y-%m-%d")

    rows_to_add = []

    for job in jobs:

        link = job.get("link")

        if not link or link in existing_links:
            continue

        rows_to_add.append([
            today,
            job.get("title"),
            job.get("company"),
            job.get("location"),
            job.get("source"),
            job.get("rank_score"),
            job.get("score"),
            job.get("action"),
            ", ".join(job.get("why_match", [])),
            ", ".join(job.get("concerns", [])),
            link,
            "",
            "",
            "",
        ])

    if rows_to_add:
        sheet.append_rows(rows_to_add)
        print(f"Added {len(rows_to_add)} new jobs to sheet")
    else:
        print("No new jobs to add (all duplicates)")

        # --- Export job summary for AI ops system ---

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    ranked_jobs = sorted(
        jobs,
        key=lambda j: j.get("score", 0),
        reverse=True
    )[:5]

    export_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "jobs_after_filtering": len(jobs),
        "ranked_jobs": [
            {
                "title": job.get("title"),
                "company": job.get("company"),
                "score": job.get("score"),
                "rank_score": job.get("rank_score"),
                "action": job.get("action"),
                "why": job.get("why_match", []),
                "link": job.get("link")
            }
            for job in ranked_jobs
        ]
    }

    with open(output_dir / "latest_jobs_output.json", "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)

    print("Exported jobs summary for AI ops")