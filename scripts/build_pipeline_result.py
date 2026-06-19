import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


WEIGHTS = {"critical": 20, "high": 10, "medium": 3, "low": 1}
ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_finding(
    source: str,
    vulnerability_id: str,
    package: str,
    installed: str,
    fixed: str,
    severity: str,
    title: str,
    url: str = "",
) -> dict[str, str]:
    severity_name = severity.lower()
    if severity_name not in ORDER:
        severity_name = "unknown"
    return {
        "source": source,
        "id": vulnerability_id,
        "package": package,
        "installed_version": installed,
        "fixed_version": fixed or "Not available",
        "severity": severity_name,
        "title": title or "No advisory summary provided",
        "url": url,
        "action": (
            f"Upgrade {package} to {fixed} or later."
            if fixed
            else f"Review or replace {package}; no fixed version was reported."
        ),
    }


def parse_trivy(path: Path) -> list[dict[str, str]]:
    payload = read_json(path)
    findings = []
    for result in payload.get("Results", []):
        for item in result.get("Vulnerabilities") or []:
            findings.append(
                normalize_finding(
                    "Trivy",
                    item.get("VulnerabilityID", "Unknown"),
                    item.get("PkgName", "Unknown"),
                    item.get("InstalledVersion", "Unknown"),
                    item.get("FixedVersion", ""),
                    item.get("Severity", "UNKNOWN"),
                    item.get("Title", ""),
                    item.get("PrimaryURL", ""),
                )
            )
    return findings


def parse_pip_audit(path: Path) -> list[dict[str, str]]:
    payload = read_json(path)
    findings = []
    for dependency in payload.get("dependencies", []):
        for vulnerability in dependency.get("vulns", []):
            fixes = vulnerability.get("fix_versions") or []
            aliases = vulnerability.get("aliases") or []
            findings.append(
                normalize_finding(
                    "pip-audit",
                    vulnerability.get("id", "Unknown"),
                    dependency.get("name", "Unknown"),
                    dependency.get("version", "Unknown"),
                    fixes[0] if fixes else "",
                    vulnerability.get("severity", "HIGH"),
                    vulnerability.get("description", ""),
                    (
                        f"https://osv.dev/vulnerability/{vulnerability.get('id')}"
                        if vulnerability.get("id")
                        else ""
                    ),
                )
            )
            if aliases:
                findings[-1]["aliases"] = ", ".join(aliases)
    return findings


def parse_coverage(path: Path) -> float:
    if not path.exists():
        return 0.0
    root = ElementTree.parse(path).getroot()
    return round(float(root.attrib.get("line-rate", 0)) * 100, 1)


def deduplicate(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    unique = {}
    for finding in findings:
        key = (finding["id"], finding["package"])
        existing = unique.get(key)
        if not existing or ORDER[finding["severity"]] < ORDER[existing["severity"]]:
            unique[key] = finding
    return sorted(
        unique.values(),
        key=lambda item: (ORDER[item["severity"]], item["package"], item["id"]),
    )


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    findings = deduplicate(
        parse_trivy(Path(args.trivy)) + parse_pip_audit(Path(args.pip_audit))
    )
    counts = {severity: 0 for severity in ("critical", "high", "medium", "low")}
    for finding in findings:
        if finding["severity"] in counts:
            counts[finding["severity"]] += 1

    score = max(
        100 - sum(counts[name] * WEIGHTS[name] for name in counts),
        0,
    )
    status = "failed" if counts["critical"] or counts["high"] else "passed"
    repository = os.getenv("GITHUB_REPOSITORY", "NR0498/sentinelci")
    run_id = os.getenv("GITHUB_RUN_ID", "local")
    server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "name": "SentinelCI",
            "repository": repository,
            "description": (
                "DevSecOps evidence platform for automated security, "
                "quality, artifact, and notification workflows."
            ),
        },
        "run": {
            "id": run_id,
            "number": os.getenv("GITHUB_RUN_NUMBER", "local"),
            "attempt": os.getenv("GITHUB_RUN_ATTEMPT", "1"),
            "event": os.getenv("GITHUB_EVENT_NAME", "local"),
            "branch": os.getenv("GITHUB_REF_NAME", "local"),
            "commit": os.getenv("GITHUB_SHA", "local")[:7],
            "actor": os.getenv("GITHUB_ACTOR", "local-user"),
            "url": (
                f"{server_url}/{repository}/actions/runs/{run_id}"
                if run_id != "local"
                else ""
            ),
            "status": status,
        },
        "quality": {
            "coverage_percent": parse_coverage(Path(args.coverage)),
            "tests_status": os.getenv("TEST_STATUS", "passed"),
            "lint_status": os.getenv("LINT_STATUS", "passed"),
        },
        "security": {
            "status": status,
            "score": score,
            "counts": counts,
            "total_findings": len(findings),
            "findings": findings,
            "gate": {
                "passed": status == "passed",
                "policy": "Block on any critical or high vulnerability.",
            },
        },
        "delivery": {
            "image_tag": os.getenv("IMAGE_TAG", "local"),
            "artifact_name": os.getenv(
                "ARTIFACT_NAME",
                "sentinelci-pipeline-evidence",
            ),
            "discord_configured": bool(os.getenv("DISCORD_WEBHOOK_URL")),
        },
    }


def write_summary(result: dict[str, Any], path: Path) -> None:
    security = result["security"]
    run = result["run"]
    lines = [
        "# SentinelCI pipeline result",
        "",
        f"- Status: **{security['status'].upper()}**",
        f"- Security score: **{security['score']}/100**",
        f"- Coverage: **{result['quality']['coverage_percent']}%**",
        f"- Branch: `{run['branch']}`",
        f"- Commit: `{run['commit']}`",
        (
            "- Findings: "
            f"{security['counts']['critical']} critical, "
            f"{security['counts']['high']} high, "
            f"{security['counts']['medium']} medium, "
            f"{security['counts']['low']} low"
        ),
        "",
        "## Actionable findings",
        "",
    ]
    for finding in security["findings"][:10]:
        lines.append(
            f"- **{finding['id']}** in `{finding['package']} "
            f"{finding['installed_version']}`: {finding['action']}"
        )
    if not security["findings"]:
        lines.append("- No known vulnerabilities were reported.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trivy", default="trivy-report.json")
    parser.add_argument("--pip-audit", default="pip-audit-report.json")
    parser.add_argument("--coverage", default="coverage.xml")
    parser.add_argument("--output", default="sentinelci-result.json")
    parser.add_argument("--summary", default="sentinelci-summary.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_result(args)
    Path(args.output).write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    write_summary(result, Path(args.summary))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
