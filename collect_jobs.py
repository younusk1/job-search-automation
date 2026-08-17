"""Collect leads from source-approved RSS/Atom feeds only.

Feed URLs are supplied through the ``JOB_SOURCE_FEEDS`` GitHub Actions variable
as a JSON list: [{"name": "BrightSpyre", "url": "https://..."}]. This avoids
general web search and does not scrape job boards. Add a feed only after the
source has made it available to the account or approved its use.
"""
from __future__ import annotations

import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ATOM = "{http://www.w3.org/2005/Atom}"


def configured_feeds() -> list[dict[str, str]]:
    raw = os.environ.get("JOB_SOURCE_FEEDS", "").strip()
    if not raw:
        return []
    try:
        feeds = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("JOB_SOURCE_FEEDS must be valid JSON for a list of objects with name and url") from exc
    if not isinstance(feeds, list) or not all(isinstance(feed, dict) and feed.get("name") and feed.get("url") for feed in feeds):
        raise ValueError("JOB_SOURCE_FEEDS must be a JSON list of objects with name and url")
    return feeds


def text(element: ET.Element | None, tag: str) -> str:
    value = element.findtext(tag) if element is not None else None
    return value.strip() if value else ""


def parse_feed(name: str, payload: bytes) -> list[dict]:
    root = ET.fromstring(payload)
    items = root.findall("./channel/item") or root.findall(f"{ATOM}entry")
    output = []
    for item in items:
        link = text(item, "link") or next((candidate.get("href", "") for candidate in item.findall(f"{ATOM}link") if candidate.get("href")), "")
        output.append({
            "title": text(item, "title") or text(item, f"{ATOM}title"),
            "url": link,
            "description": text(item, "description") or text(item, f"{ATOM}summary") or text(item, f"{ATOM}content"),
            "source": name,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "verification_status": "pending",
            "included_in_digest": False,
        })
    return output


def fetch_feed(feed: dict[str, str]) -> list[dict]:
    request = urllib.request.Request(feed["url"], headers={"User-Agent": "JobSearchDigestBot/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_feed(feed["name"], response.read())


def main() -> None:
    DATA.mkdir(exist_ok=True)
    feeds = configured_feeds()
    leads, errors = [], []
    for feed in feeds:
        try:
            leads.extend(fetch_feed(feed))
        except Exception as error:
            errors.append({"source": feed["name"], "error": str(error)})
    unique = {lead["url"]: lead for lead in leads if lead["url"]}
    (DATA / "candidate-leads.json").write_text(json.dumps(list(unique.values()), indent=2), encoding="utf-8")
    (DATA / "collection-state.json").write_text(json.dumps({"feeds": len(feeds), "leads": len(unique), "errors": errors}, indent=2), encoding="utf-8")
    if errors:
        raise RuntimeError(f"One or more source integrations failed: {[error['source'] for error in errors]}")
    print(f"Collected {len(unique)} candidate leads from {len(feeds)} approved feeds.")


if __name__ == "__main__":
    main()
