# Discord Notification Setup

## Purpose

Discord receives concise pipeline outcomes after SentinelCI has generated its
trusted result. Discord does not calculate the score and does not replace the
GitHub artifact or Security tab.

## Configuration

1. In Discord, open the target channel settings.
2. Open **Integrations**, then **Webhooks**.
3. Create a webhook and copy its URL.
4. In GitHub, open the repository.
5. Open **Settings**, **Secrets and variables**, **Actions**.
6. Create a repository secret named `DISCORD_WEBHOOK_URL`.
7. Paste the webhook URL as the secret value.
8. Run the `SentinelCI Demo Pipeline` workflow.

The workflow never prints the secret. If the secret is not configured,
`scripts/discord_notify.py` reports that delivery was skipped and exits
successfully.

## Notification content

The message contains:

- pipeline PASS or FAIL state
- branch, commit and triggering actor
- direct GitHub Actions run link
- calculated security score
- coverage and quality status
- critical and high finding counts
- up to five top vulnerabilities
- installed and fixed package versions

## Local payload preview

Generate a result and preview the exact Discord JSON without sending it:

```powershell
.\.venv\Scripts\python scripts\build_pipeline_result.py `
  --trivy demo\trivy-vulnerable.json `
  --pip-audit demo\pip-audit-empty.json `
  --coverage coverage.xml

.\.venv\Scripts\python scripts\discord_notify.py `
  --result sentinelci-result.json `
  --dry-run
```
