import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timezone
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

    all_values = sheet.get_all_values()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Build map of existing links -> row number
    # Row 1 is the header, so sheet rows start at 2 for data
    existing_link_to_row = {}
    for i, row in enumerate(all_values[1:], start=2):
        if len(row) >= 11:
            link = row[10].strip()  # column K
            if link:
                existing_link_to_row[link] = i

    rows_to_add = []
    pending_updates = []
    updated_count = 0

    for job in jobs:
        link = job.get("link")
        if not link:
            continue

        if link in existing_link_to_row:
            row_num = existing_link_to_row[link]

            # Update only rank_score, ai_score, action, why_match, concerns
            # Columns F:J
            pending_updates.append({
                "range": f"F{row_num}:J{row_num}",
                "values": [[
                    job.get("rank_score"),
                    job.get("score"),
                    job.get("action"),
                    ", ".join(job.get("why_match", [])),
                    ", ".join(job.get("concerns", [])),
                ]],
            })
            updated_count += 1

        else:
            rows_to_add.append([
                today,  # A: first-seen date
                job.get("title"),  # B
                job.get("company"),  # C
                job.get("location"),  # D
                job.get("source"),  # E
                job.get("rank_score"),  # F
                job.get("score"),  # G
                job.get("action"),  # H
                ", ".join(job.get("why_match", [])),  # I
                ", ".join(job.get("concerns", [])),  # J
                link,  # K
                "",  # L reviewed
                "",  # M applied
                "",  # N notes
            ])

    if pending_updates:
        sheet.batch_update(pending_updates)

    if rows_to_add:
        sheet.append_rows(rows_to_add)
        print(f"Added {len(rows_to_add)} new jobs to sheet")
    else:
        print("No new jobs to add")

    if updated_count:
        print(f"Updated {updated_count} existing jobs in sheet")

    # --- Export job summary for AI ops system ---
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    ranked_jobs = sorted(
        jobs,
        key=lambda j: j.get("score", 0),
        reverse=True
    )[:5]

    export_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
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