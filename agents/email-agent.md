# Email Agent

## Purpose
Deliver the completed digest after all earlier stages succeed.

## Inputs
- `data/weekly-summary.html`
- `data/weekly-summary.md`
- Secure email settings (future Resend configuration)

## Responsibilities
Send one digest; log provider message ID without secrets. On provider-confirmed success, write `data/run-state.json` with `status: completed`, run ID, timestamp, and delivery ID. On failure, mark failed and return an error.

## Completion contract
A successful email marks this Wednesday run complete. All agents terminate and nothing runs again until the next Wednesday Timer trigger. Any future retry must be bounded to this invocation, never an all-week loop.

## Security
Use Azure Key Vault or Function App settings for API keys and addresses. Never commit secrets.
