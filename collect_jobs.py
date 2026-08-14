"""Pakistan-first job lead collector for the weekly GitHub Actions run.

This collector deliberately produces *leads*, not verified jobs. A lead must be
checked against its official vacancy page before it can be copied into
``data/input-jobs.json`` and become eligible for the email digest.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

# Pakistan and Islamabad sources are searched before global remote-only sources.
# Domain-less official-employer groups are intentionally queried broadly, then
# verified against their official career page by the verification stage.
SOURCE_GROUPS = (
    ("Pakistan job boards", ("linkedin.com/jobs", "pk.indeed.com", "bebee.com/pk", "jobs.taraki.co", "brightspyre.com", "rozee.pk", "mustakbil.com", "nstp.pk")),
    ("Pakistan official employers", ("careers.un.org", "undp.org", "unicef.org", "who.int", "unwomen.org", "wfp.org", "iom.int", "unops.org", "jazz.com.pk", "zong.com.pk", "telenor.com.pk", "ptcl.com.pk", "nayatel.com", "akdn.org")),
    ("Development jobs", ("reliefweb.int", "devex.com")),
    ("Remote-only ATS supplement", ("greenhouse.io", "lever.co", "ashbyhq.com")),
)

ROLE_QUERIES = (
    '"Business Analyst"',
    '"Product Analyst" OR "Product Owner"',
    '"Digital Transformation" OR "Process Improvement"',
    '"Strategic Communications" OR "Communications Manager" OR "Knowledge Management"',
)


def brave_search(query: str, api_key: str) -> list[dict]:
    """Return web results from Brave Search without scraping the target websites."""
    endpoint = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode({"q": query, "count": 10, "freshness": "pm"})
    request = urllib.request.Request(endpoint, headers={"Accept": "application/json", "X-Subscription-Token": api_key})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("web", {}).get("results", [])


def source_query(domain: str, role_query: str, group: str) -> str:
    location = "Pakistan OR Islamabad" if group != "Remote-only ATS supplement" else '"remote"'
    return f"site:{domain} ({role_query}) ({location}) (job OR careers OR vacancy)"


def collect(api_key: str) -> list[dict]:
    seen, leads = set(), []
    for group, domains in SOURCE_GROUPS:
        for domain in domains:
            for role in ROLE_QUERIES:
                for result in brave_search(source_query(domain, role, group), api_key):
                    url = result.get("url")
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    leads.append({
                        "title": result.get("title", "Untitled listing"),
                        "url": url,
                        "description": result.get("description", ""),
                        "source_domain": domain,
                        "source_group": group,
                        "discovered_at": datetime.now(timezone.utc).isoformat(),
                        "verification_status": "pending",
                        "included_in_digest": False,
                    })
    return leads


def main() -> None:
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY")
    if not api_key:
        raise RuntimeError("Set BRAVE_SEARCH_API_KEY as a GitHub Actions secret")
    DATA.mkdir(exist_ok=True)
    leads = collect(api_key)
    (DATA / "candidate-leads.json").write_text(json.dumps(leads, indent=2), encoding="utf-8")
    print(f"Collected {len(leads)} candidate leads for verification.")


if __name__ == "__main__":
    main()
