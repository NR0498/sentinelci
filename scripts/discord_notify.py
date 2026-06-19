import argparse
import json
import os
from pathlib import Path

import requests


def build_payload(result: dict) -> dict:
    run = result["run"]
    security = result["security"]
    counts = security["counts"]
    color = 0x2ECC71 if security["status"] == "passed" else 0xE74C3C
    top_findings = security["findings"][:5]
    findings_text = (
        "\n".join(
            f"{item['id']} | {item['package']} {item['installed_version']} "
            f"| fix: {item['fixed_version']}"
            for item in top_findings
        )
        or "No known vulnerabilities reported."
    )
    return {
        "username": "SentinelCI",
        "allowed_mentions": {"parse": []},
        "embeds": [
            {
                "title": (
                    f"Pipeline {security['status'].upper()}: "
                    f"{result['project']['name']}"
                ),
                "url": run["url"] or None,
                "color": color,
                "description": (
                    "Automated result generated from raw test, dependency, "
                    "and container scan evidence."
                ),
                "fields": [
                    {
                        "name": "Run",
                        "value": (
                            f"Branch: `{run['branch']}`\n"
                            f"Commit: `{run['commit']}`\n"
                            f"Actor: `{run['actor']}`"
                        ),
                        "inline": True,
                    },
                    {
                        "name": "Security",
                        "value": (
                            f"Score: **{security['score']}/100**\n"
                            f"Critical: **{counts['critical']}**\n"
                            f"High: **{counts['high']}**"
                        ),
                        "inline": True,
                    },
                    {
                        "name": "Quality",
                        "value": (
                            f"Coverage: **{result['quality']['coverage_percent']}%**\n"
                            f"Tests: **{result['quality']['tests_status']}**\n"
                            f"Lint: **{result['quality']['lint_status']}**"
                        ),
                        "inline": True,
                    },
                    {
                        "name": "Top findings",
                        "value": findings_text[:1024],
                        "inline": False,
                    },
                ],
                "footer": {
                    "text": "SentinelCI evidence-based DevSecOps pipeline"
                },
                "timestamp": result["generated_at"],
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", default="sentinelci-result.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = json.loads(Path(args.result).read_text(encoding="utf-8"))
    payload = build_payload(result)
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if args.dry_run or not webhook_url:
        print(json.dumps(payload, indent=2))
        if not webhook_url:
            print("DISCORD_WEBHOOK_URL is not set; notification skipped.")
        return 0
    response = requests.post(webhook_url, json=payload, timeout=20)
    response.raise_for_status()
    print("Discord notification delivered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
