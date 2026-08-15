# Job-search automation architecture

## Goal
One curated weekly digest matching Business Analysis/Product and Strategic Communications roles, enforcing active status and location eligibility.

## Weekly execution
```text
GitHub Actions schedule (Wednesday morning, Asia/Karachi)
  -> Discovery -> Intelligence -> Summary -> Email -> Mark run complete -> Terminate
```
The timer is the only recurring process: there are no agent loops, background workers, or repeated checks during the week.

## Pipeline outputs
| Stage | Responsibility | Output |
|---|---|---|
| Discovery | Search, normalize, verify open status, deduplicate | `data/discovered-jobs.json` |
| Intelligence | Enforce eligibility and score | `data/ranked-jobs.json` |
| Summary | Render Markdown and HTML | `data/weekly-summary.md`, `data/weekly-summary.html` |
| Email | Send and record provider confirmation | `data/run-state.json` |

## Eligibility
- Islamabad: onsite, hybrid, and remote are eligible.
- Elsewhere: only explicitly fully remote roles are eligible.
- All included roles must be verified open; expired, removed, closed, and unverified listings are excluded.
- Official pages are primary links; boards are secondary mirrors.

## Completion and failure
Provider-confirmed email delivery writes a completed run state, ends the GitHub Actions run, and keeps the pipeline dormant until next Wednesday. A failure records failed state and returns an error; it must not poll or run through the week. Future retry policies must be bounded to the same run.

## GitHub Actions boundary
Implement one scheduled workflow under `.github/workflows/`. Keep Resend keys and email addresses in GitHub Actions repository secrets; never commit them.
