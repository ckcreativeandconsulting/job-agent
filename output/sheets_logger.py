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


HEADER_ROW = [
    "date_found", "title", "company", "location", "source",
    "rank_score", "ai_score", "action", "why_match", "concerns",
    "link", "reviewed", "applied", "notes", "employment_type", "ollama_score",
]


def _ensure_header(sheet, all_values: list) -> None:
    """Write the header row if O or P is missing or the sheet is empty."""
    if not all_values:
        sheet.insert_row(HEADER_ROW, 1)
        return
    header = all_values[0]
    if len(header) < 15 or header[14].strip().lower() not in ("employment_type", "employment type"):
        sheet.update("O1", [["employment_type"]])
    if len(header) < 16 or header[15].strip().lower() != "ollama_score":
        sheet.update("P1", [["ollama_score"]])


def append_jobs(jobs):
    sheet = get_sheet()

    all_values = sheet.get_all_values()
    _ensure_header(sheet, all_values)
    today = datetime.now().strftime("%Y-%m-%d")

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

        # Derive Ollama pre-score for column P:
        #   hybrid mode + OpenAI ran: pre_score holds Ollama's initial score
        #   hybrid mode + only Ollama ran: backend=="ollama", score is the Ollama score
        #   openai-only or error: leave blank
        if job.get("pre_score") is not None:
            ollama_score = job["pre_score"]
        elif job.get("backend") == "ollama":
            ollama_score = job.get("score", "")
        else:
            ollama_score = ""

        if link in existing_link_to_row:
            row_num = existing_link_to_row[link]

            # Update rank_score, ai_score, action, why_match, concerns (F:J),
            # employment_type_label (O), and ollama_score (P)
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
            pending_updates.append({
                "range": f"O{row_num}",
                "values": [[job.get("employment_type_label", "unknown").lower()]],
            })
            pending_updates.append({
                "range": f"P{row_num}",
                "values": [[ollama_score]],
            })
            updated_count += 1

        else:
            rows_to_add.append([
                today,                                          # A: first-seen date
                job.get("title"),                              # B
                job.get("company"),                            # C
                job.get("location"),                           # D
                job.get("source"),                             # E
                job.get("rank_score"),                         # F
                job.get("score"),                              # G ai_score (final)
                job.get("action"),                             # H
                ", ".join(job.get("why_match", [])),           # I
                ", ".join(job.get("concerns", [])),            # J
                link,                                          # K
                "",                                            # L reviewed
                "",                                            # M applied
                "",                                            # N notes
                job.get("employment_type_label", "unknown").lower(),  # O employment_type
                ollama_score,                                  # P ollama_score
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


def get_applied_data() -> tuple[set, set, set]:
    """
    Read the sheet and return (applied_links, applied_companies, rejected_links).
    applied_links:    col K where col M is "yes" (case-insensitive) — already applied.
    applied_companies: col C (lowercased) where col M is "yes" — used for rank boost.
    rejected_links:   col K where col M is "no"  — reviewed and decided not to apply.
    Returns (set(), set(), set()) on any error so the pipeline degrades gracefully.
    """
    try:
        sheet = get_sheet()
        all_values = sheet.get_all_values()
    except Exception as e:
        print(f"[sheets] WARNING: Could not read applied data: {e}")
        print("[sheets] Continuing without applied boost.")
        return set(), set(), set()

    applied_links: set = set()
    applied_companies: set = set()
    rejected_links: set = set()

    for row in all_values[1:]:  # skip header row
        if len(row) < 13:
            continue
        link    = row[10].strip()   # col K
        company = row[2].strip()    # col C
        applied = row[12].strip()   # col M

        is_applied  = applied.lower() == "yes"
        is_rejected = applied.lower() == "no"

        if is_applied and link:
            applied_links.add(link)
        if is_applied and company:
            applied_companies.add(company.lower())
        if is_rejected and link:
            rejected_links.add(link)

    return applied_links, applied_companies, rejected_links