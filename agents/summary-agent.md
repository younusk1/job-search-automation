# Summary Agent

## Purpose
Render eligible, verified jobs into the weekly Markdown and HTML digest.

## Inputs
- `data/ranked-jobs.json`
- `templates/weekly-email.md`
- `templates/weekly-email.html`

## Responsibilities
Order by priority and score. For each role show employer, title, location/work mode, deadline or “deadline not published”, official link, score, track, and match reasons. Include discovered/rejected/deduplicated/included metrics. Write `data/weekly-summary.md` and `data/weekly-summary.html`.

## Completion
Return the digest to Email and terminate. Do not send email or schedule further work.
