# Recruiter Guide

## Project summary

SentinelCI demonstrates how a delivery team can turn security tooling into a
clear release decision. It combines CI/CD automation, application testing,
container security, dependency auditing, infrastructure automation, artifact
storage, event notifications, and an operational dashboard.

The project is designed to show engineering judgment rather than a collection
of disconnected tools. Each component contributes evidence to one delivery
workflow.

## What the implementation demonstrates

### Software engineering

- FastAPI service design and automated API tests
- structured logging and health checks
- separation of report parsing, AWS integration, and HTTP routing
- defensive handling for unsupported or malformed reports

### DevSecOps

- GitHub Actions and Jenkins pipeline definitions
- pytest coverage, flake8, pip-audit, Trivy, and SARIF publishing
- policy-based deployment blocking
- normalized machine-readable and human-readable reports
- retained pipeline artifacts for auditability

### Cloud and infrastructure

- Docker and Nginx multi-container packaging
- LocalStack S3, SNS, and SQS integration without cloud credentials
- Terraform infrastructure modeling
- Ansible container deployment automation
- Vercel deployment for the public dashboard

### Operational communication

- dashboard views for runs, trends, findings, and remediation
- Discord webhook payloads containing actionable pipeline context
- GitHub job summaries and direct links to workflow runs

## What to review first

1. Open the production dashboard:
   https://dashboard-sooty-six-33.vercel.app
2. Review `.github/workflows/ci.yml` to see the control flow.
3. Review `scripts/build_pipeline_result.py` for evidence normalization.
4. Review `scripts/discord_notify.py` for notification design.
5. Review `app/aws_service.py` for LocalStack integration.
6. Review `docs/ARCHITECTURE.md` for system diagrams.
7. Review `proof/README.md` for captured working evidence.

## Design decisions

### Why normalize scanner output?

Different tools use different schemas. A dashboard should not contain separate
business logic for every scanner. SentinelCI converts raw outputs into one
stable contract before the UI, release gate, Discord notification, or artifact
summary consumes them.

### Why publish SARIF?

The dashboard is useful for overview and communication, while GitHub's Security
tab is the correct place for repository-level security triage. SARIF connects
container findings to GitHub's native security workflow.

### Why make Discord optional?

Webhook URLs are credentials. The workflow reads `DISCORD_WEBHOOK_URL` only
from GitHub repository secrets. If the secret is absent, the pipeline continues
and records that notification delivery was skipped.

### Why keep LocalStack local?

The project proves real boto3 calls, S3 object metadata, SNS publication, and
SQS delivery without asking a reviewer to provide AWS credentials. The same
service layer can later target AWS by changing endpoint and credential
configuration.

## Current limitations and production evolution

- Representative evidence is committed for the public portfolio dashboard.
  A production system would persist every trusted result in a database or
  object store and expose an authenticated API.
- The public GitHub API is rate limited. A production dashboard would use a
  server-side GitHub App installation token and caching.
- LocalStack provides service compatibility, not every operational property of
  AWS. Production adoption would add IAM least privilege, encryption, lifecycle
  policies, CloudTrail, and monitored dead-letter queues.
- Discord is one notification channel. The normalized result supports adding
  Slack, Microsoft Teams, email, or incident-management systems.
