# Job-search automation

This project uses a single scheduled timer trigger that runs once each Wednesday at 08:00 Asia/Karachi (03:00 UTC), executes discovery → ranking → summary → email sequentially, and then terminates. The workflow is intentionally one-shot: no poller, no week-long loop, no repeated checks during the week. A provider-confirmed successful email marks the run complete until the next scheduled Wednesday. Manual runs from the Actions tab are allowed, but they still follow the same one-run flow.

Add these repository secrets before enabling it: `RESEND_API_KEY`, `JOB_DIGEST_TO`, and `JOB_DIGEST_FROM`. The sender must be a verified Resend sender/domain. Secrets are only provided to their corresponding workflow step and are never written to workflow output or artifacts.

`collect_jobs.py` is the direct source-integration collector. It consumes only source-approved RSS or Atom feeds, does not scrape job sites, and never treats a feed item as verified. Configure the non-secret `JOB_SOURCE_FEEDS` GitHub Actions variable as a JSON list, for example `[{"name":"BrightSpyre","url":"https://your-approved-feed-url"}]`. BrightSpyre publicly offers job-alert RSS feeds; add other sources only when they provide a feed or grant API access. It writes pending leads to `data/candidate-leads.json`.

Current search sources include: LinkedIn, BeBee, Taraki, BrightSpyre, Mustakbil, NSTP, ReliefWeb, Devex, UN agencies, embassies/high commissions in Pakistan, Pakistani telecoms, AKDN organizations, major NGOs/INGOs, Greenhouse, Lever, and Ashby.

User preferences and eligibility rules:

- Islamabad may include onsite, hybrid, or remote roles; all other locations must be remote only.
- Only active jobs are included; expired, closed, or unverifiable listings are rejected.
- Prefer official employer career pages; board and mirror links are secondary.
- Deduplicate by canonical employer/title/location/requisition so only the strongest official link remains.
- Score Business Analysis/Product and Communications roles using the project scoring rules from the prior discussion.

`verify_jobs.py` promotes only structured schema.org `JobPosting` data from approved official-employer domains. It rejects non-official board links, expired postings, listings outside Islamabad unless they are explicitly remote, and pages without enough structured evidence. It writes verified, normalized jobs to `data/input-jobs.json` for the digest. Generated summaries and run state are retained only as that run's GitHub Actions artifact.
