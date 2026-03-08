import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


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