# Job-search automation

GitHub Actions runs the digest once each Wednesday at 08:00 Asia/Karachi (03:00 UTC) and can also be run manually from the Actions tab.

Add these repository secrets before enabling it: `RESEND_API_KEY`, `JOB_DIGEST_TO`, and `JOB_DIGEST_FROM`. The sender must be a verified Resend sender/domain. Secrets are only provided to their corresponding workflow step and are never written to workflow output or artifacts.

`collect_jobs.py` is the direct source-integration collector. It consumes only source-approved RSS or Atom feeds, does not scrape job sites, and never treats a feed item as verified. Configure the non-secret `JOB_SOURCE_FEEDS` GitHub Actions variable as a JSON list, for example `[{"name":"BrightSpyre","url":"https://your-approved-feed-url"}]`. BrightSpyre publicly offers job-alert RSS feeds; add other sources only when they provide a feed or grant API access. It writes pending leads to `data/candidate-leads.json`.

`verify_jobs.py` promotes only structured schema.org `JobPosting` data from approved official-employer domains. It rejects non-official board links, expired postings, listings outside Islamabad unless they are explicitly remote, and pages without enough structured evidence. It writes verified, normalized jobs to `data/input-jobs.json` for the digest. Generated summaries and run state are retained only as that run's GitHub Actions artifact.
