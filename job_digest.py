"""One-shot job-digest workflow invoked by GitHub Actions."""
from __future__ import annotations

import html
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def write_json(name: str, value: object) -> None:
    DATA.mkdir(exist_ok=True)
    (DATA / name).write_text(json.dumps(value, indent=2), encoding="utf-8")


def load_verified_jobs() -> list[dict]:
    """Read normalized collector output and enforce the first hard gate."""
    source = DATA / "input-jobs.json"
    jobs = json.loads(source.read_text(encoding="utf-8")) if source.exists() else []
    if not isinstance(jobs, list):
        raise ValueError("data/input-jobs.json must contain a JSON list")
    unique: dict[tuple[str, str, str, str], dict] = {}
    for job in jobs:
        if job.get("status") != "open" or job.get("verified_open") is not True:
            continue
        key = tuple(str(job.get(k, "")).lower() for k in ("employer", "title", "location", "requisition_id"))
        if key not in unique or (job.get("official_url") and not unique[key].get("official_url")):
            unique[key] = job
    result = list(unique.values())
    write_json("discovered-jobs.json", result)
    return result


def rank(jobs: list[dict]) -> tuple[list[dict], int]:
    today, results, rejected = date.today(), [], 0
    ba = ("business analyst", "product", "digital transformation", "process improvement", "requirements")
    comms = ("communication", "knowledge management", "stakeholder engagement", "change management")
    for job in jobs:
        location, mode = str(job.get("location", "")).lower(), str(job.get("work_mode", "")).lower()
        deadline = job.get("deadline")
        if ("islamabad" not in location and mode not in {"remote", "fully remote"}) or (deadline and date.fromisoformat(str(deadline)) < today):
            rejected += 1
            continue
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        terms, track = (ba, "Business Analysis / Product") if any(x in text for x in ba) else (comms, "Strategic Communications")
        if not any(x in text for x in terms):
            rejected += 1
            continue
        score = min(100, int(job.get("score") or (50 + 25 * sum(x in text for x in terms))))
        results.append({**job, "track": track, "score": score, "priority_label": "High priority" if score >= 80 else "Recommended" if score >= 60 else "Worth reviewing", "match_reasons": job.get("match_reasons") or f"Matches the {track} track and location policy."})
    return sorted(results, key=lambda item: item["score"], reverse=True), rejected


def render(jobs: list[dict], discovered: int, rejected: int) -> tuple[str, str]:
    metric = f"Discovered: {discovered} | Rejected: {rejected} | Included: {len(jobs)}"
    lines, cards = [], []
    for j in jobs:
        deadline = j.get("deadline") or "Deadline not published"
        lines.append(f"### {j['priority_label']} — {j.get('title')} at {j.get('employer')}\n\n- Score: {j['score']}/100 · Track: {j['track']}\n- Location: {j.get('location')} · Work mode: {j.get('work_mode')}\n- Deadline: {deadline}\n- Why it matches: {j['match_reasons']}\n- Apply: {j.get('official_url')}\n")
        cards.append(f"<section><h2>{html.escape(str(j.get('title')))} at {html.escape(str(j.get('employer')))}</h2><p><strong>{j['score']}/100 · {html.escape(j['track'])}</strong><br>{html.escape(str(j.get('location')))} · {html.escape(str(j.get('work_mode')))}<br>Deadline: {html.escape(str(deadline))}<br>{html.escape(str(j['match_reasons']))}<br><a href=\"{html.escape(str(j.get('official_url', '')), quote=True)}\">Apply</a></p></section>")
    markdown = "# Weekly curated job search — " + str(date.today()) + "\n\n" + metric + "\n\n## Recommended roles\n\n" + ("\n".join(lines) or "No eligible verified roles were found this week.\n")
    template = (ROOT / "templates" / "weekly-email.html").read_text(encoding="utf-8")
    email_html = template.replace("{{run_date}}", str(date.today())).replace("{{summary_metrics}}", html.escape(metric)).replace("{{jobs_html}}", "".join(cards) or "<p>No eligible verified roles were found this week.</p>")
    return markdown, email_html


def send_email(email_html: str, markdown: str) -> str:
    required = {name: os.environ.get(name) for name in ("RESEND_API_KEY", "JOB_DIGEST_TO", "JOB_DIGEST_FROM")}
    if not all(required.values()):
        raise RuntimeError("Set RESEND_API_KEY, JOB_DIGEST_TO, and JOB_DIGEST_FROM as GitHub Actions secrets")
    body = json.dumps({"from": required["JOB_DIGEST_FROM"], "to": [required["JOB_DIGEST_TO"]], "subject": "Weekly curated job search", "html": email_html, "text": markdown}).encode()
    request = urllib.request.Request("https://api.resend.com/emails", body, {"Authorization": f"Bearer {required['RESEND_API_KEY']}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Resend delivery failed with HTTP {error.code}") from error
    if not result.get("id"):
        raise RuntimeError("Resend did not return a delivery ID")
    return str(result["id"])


def main() -> None:
    run_id, timestamp = str(uuid.uuid4()), datetime.now(timezone.utc).isoformat()
    try:
        discovered = load_verified_jobs()
        jobs, rejected = rank(discovered)
        write_json("ranked-jobs.json", jobs)
        markdown, email_html = render(jobs, len(discovered), rejected)
        (DATA / "weekly-summary.md").write_text(markdown, encoding="utf-8")
        (DATA / "weekly-summary.html").write_text(email_html, encoding="utf-8")
        delivery_id = send_email(email_html, markdown)
        write_json("run-state.json", {"status": "completed", "run_id": run_id, "timestamp": timestamp, "delivery_id": delivery_id})
    except Exception as error:
        write_json("run-state.json", {"status": "failed", "run_id": run_id, "timestamp": timestamp, "error": str(error)})
        raise


if __name__ == "__main__":
    main()
