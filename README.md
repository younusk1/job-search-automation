# Job-search automation

GitHub Actions runs the digest once each Wednesday at 08:00 Asia/Karachi (03:00 UTC) and can also be run manually from the Actions tab.

Add these repository secrets before enabling it: `BRAVE_SEARCH_API_KEY`, `RESEND_API_KEY`, `JOB_DIGEST_TO`, and `JOB_DIGEST_FROM`. The sender must be a verified Resend sender/domain. Secrets are only provided to their corresponding workflow step and are never written to workflow output or artifacts.

`collect_jobs.py` is the Pakistan-first lead collector. It searches the finalized Pakistan job boards and official employer sources first, then ReliefWeb/Devex, and finally remote-only ATS sources. It does not scrape job sites and never treats a search result as verified. It writes pending leads to `data/candidate-leads.json`.

A verification step must promote a lead into `data/input-jobs.json` before the digest runs. Every included listing must have `status: "open"`, `verified_open: true`, and a current deadline (when published). The digest excludes duplicates and listings outside the location policy, then sends exactly one email. Generated summaries and run state are retained only as that run's GitHub Actions artifact.
