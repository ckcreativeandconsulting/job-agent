def build_digest(scored_jobs: list[dict], ignored_jobs: list[dict]) -> str:
    apply_jobs = [job for job in scored_jobs if job.get("action") == "Apply"]
    maybe_jobs = [job for job in scored_jobs if job.get("action") == "Maybe"]
    ignore_scored_jobs = [job for job in scored_jobs if job.get("action") == "Ignore"]

    lines = []
    lines.append("DAILY JOB DIGEST")
    lines.append("=" * 50)
    lines.append("")

    if apply_jobs:
        lines.append("APPLY NOW")
        lines.append("-" * 50)
        for job in apply_jobs:
            lines.append(f"{job.get('score')} — {job.get('title')} — {job.get('company')}")
            lines.append(f"Type: {job.get('employment_type_label')}")
            lines.append(f"Why: {', '.join(job.get('why_match', []))}")
            concerns = job.get("concerns", [])
            if concerns:
                lines.append(f"Concerns: {', '.join(concerns)}")
            lines.append(f"Link: {job.get('link')}")
            lines.append("")
            lines.append(f"Rank Score: {job.get('rank_score')}")

    if maybe_jobs:
        lines.append("MAYBE")
        lines.append("-" * 50)
        for job in maybe_jobs:
            lines.append(f"{job.get('score')} — {job.get('title')} — {job.get('company')}")
            lines.append(f"Type: {job.get('employment_type_label')}")
            lines.append(f"Why: {', '.join(job.get('why_match', []))}")
            concerns = job.get("concerns", [])
            if concerns:
                lines.append(f"Concerns: {', '.join(concerns)}")
            lines.append(f"Link: {job.get('link')}")
            lines.append("")
            lines.append(f"Rank Score: {job.get('rank_score')}")

    lines.append("IGNORED SUMMARY")
    lines.append("-" * 50)
    lines.append(f"Ignored before scoring: {len(ignored_jobs)}")
    if ignored_jobs:
        lines.append("Examples:")
        for job in ignored_jobs[:3]:
            lines.append(f"- {job.get('title')} — {job.get('company')}")
        lines.append("")

    lines.append(f"Ignored after scoring: {len(ignore_scored_jobs)}")
    if ignore_scored_jobs:
        lines.append("Examples:")
        for job in ignore_scored_jobs[:3]:
            lines.append(f"- {job.get('title')} — {job.get('company')} ({job.get('score')})")
        lines.append("")

    lines.append("SUMMARY")
    lines.append("-" * 50)
    lines.append(f"Apply: {len(apply_jobs)}")
    lines.append(f"Maybe: {len(maybe_jobs)}")
    lines.append(f"Ignore: {len(ignore_scored_jobs) + len(ignored_jobs)}")

    return "\n".join(lines)