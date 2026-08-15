"""Promote verifiable official job leads into digest-ready normalized jobs.

Only pages that expose a schema.org JobPosting on an approved official-employer
domain can pass this stage. Board results, inconclusive pages, and expired jobs
remain leads; they are never treated as verified vacancies.
"""
from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OFFICIAL_DOMAINS = (
    "careers.un.org", "undp.org", "unicef.org", "who.int", "unwomen.org",
    "wfp.org", "iom.int", "unops.org", "jazz.com.pk", "zong.com.pk",
    "telenor.com.pk", "ptcl.com.pk", "nayatel.com", "akdn.org",
)
JOB_POSTING_PATTERN = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL)


def is_official_url(url: str) -> bool:
    host = urllib.parse.urlparse(url).hostname or ""
    return any(host == domain or host.endswith("." + domain) for domain in OFFICIAL_DOMAINS)


def json_ld_objects(page: str) -> list[dict]:
    """Extract JSON-LD objects without relying on fragile page-specific markup."""
    objects: list[dict] = []
    for raw in JOB_POSTING_PATTERN.findall(page):
        try:
            value = json.loads(html.unescape(raw).strip())
        except json.JSONDecodeError:
            continue
        values = value if isinstance(value, list) else value.get("@graph", []) if isinstance(value, dict) and "@graph" in value else [value]
        objects.extend(item for item in values if isinstance(item, dict))
    return objects


def job_posting_from_page(page: str) -> dict | None:
    for item in json_ld_objects(page):
        kind = item.get("@type", "")
        if kind == "JobPosting" or (isinstance(kind, list) and "JobPosting" in kind):
            return item
    return None


def text_location(value: object) -> str:
    locations = value if isinstance(value, list) else [value]
    output = []
    for location in locations:
        address = location.get("address", {}) if isinstance(location, dict) else {}
        if isinstance(address, dict):
            output.append(", ".join(str(address.get(key)) for key in ("addressLocality", "addressRegion", "addressCountry") if address.get(key)))
    return " / ".join(output)


def normalize(posting: dict, url: str) -> dict | None:
    deadline = posting.get("validThrough")
    if deadline:
        try:
            if datetime.fromisoformat(str(deadline).replace("Z", "+00:00")).date() < date.today():
                return None
        except ValueError:
            return None  # An unreadable expiry is not sufficient evidence that it is open.
    location = text_location(posting.get("jobLocation"))
    remote = str(posting.get("jobLocationType", "")).upper() == "TELECOMMUTE"
    work_mode = "fully remote" if remote else "onsite"
    if "islamabad" not in location.lower() and not remote:
        return None
    employer = posting.get("hiringOrganization", {})
    return {
        "title": posting.get("title"),
        "employer": employer.get("name") if isinstance(employer, dict) else "Unknown employer",
        "location": location or "Remote",
        "work_mode": work_mode,
        "employment_type": posting.get("employmentType"),
        "posted_date": posting.get("datePosted"),
        "deadline": deadline,
        "description": re.sub(r"<[^>]+>", " ", str(posting.get("description", ""))),
        "official_url": url,
        "status": "open",
        "verified_open": True,
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "JobSearchDigestBot/1.0 (+https://github.com/)"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")


def main() -> None:
    leads_path = DATA / "candidate-leads.json"
    leads = json.loads(leads_path.read_text(encoding="utf-8")) if leads_path.exists() else []
    jobs, checked = [], []
    for lead in leads:
        url = str(lead.get("url", ""))
        if not is_official_url(url):
            checked.append({**lead, "verification_status": "unverified_non_official_source"})
            continue
        try:
            posting = job_posting_from_page(fetch(url))
            job = normalize(posting, url) if posting else None
        except Exception as error:
            checked.append({**lead, "verification_status": "verification_failed", "verification_note": str(error)})
            continue
        if job:
            jobs.append(job)
            checked.append({**lead, "verification_status": "verified_open", "included_in_digest": True})
        else:
            checked.append({**lead, "verification_status": "not_eligible_or_not_verifiable"})
    (DATA / "candidate-leads.json").write_text(json.dumps(checked, indent=2), encoding="utf-8")
    (DATA / "input-jobs.json").write_text(json.dumps(jobs, indent=2), encoding="utf-8")
    print(f"Verified {len(jobs)} of {len(leads)} candidate leads.")


if __name__ == "__main__":
    main()
