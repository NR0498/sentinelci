import argparse
import json
from pathlib import Path
from typing import Any


SEVERITY_ORDER = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a SentinelCI security report.")
    parser.add_argument(
        "--input",
        default="trivy-report.json",
        help="Path to the Trivy JSON report.",
    )
    parser.add_argument(
        "--output",
        default="final-report.txt",
        help="Path to write the generated text report.",
    )
    parser.add_argument(
        "--label",
        default="PIPELINE REPORT",
        help="Optional label to display at the top of the report.",
    )
    parser.add_argument(
        "--fail-on-vulns",
        action="store_true",
        help="Exit with a non-zero code when high or critical findings exist.",
    )
    return parser.parse_args()


def load_report(report_path: Path) -> dict[str, Any]:
    if not report_path.exists():
        raise FileNotFoundError(f"{report_path} not found")
    return json.loads(report_path.read_text(encoding="utf-8"))


def summarize_vulnerabilities(
    payload: dict[str, Any],
) -> tuple[dict[str, int], list[dict[str, str]]]:
    counts = {severity: 0 for severity in SEVERITY_ORDER}
    findings: list[dict[str, str]] = []

    for result in payload.get("Results", []):
        target = result.get("Target", "unknown-target")
        for vulnerability in result.get("Vulnerabilities") or []:
            severity = vulnerability.get("Severity", "UNKNOWN").upper()
            counts[severity] = counts.get(severity, 0) + 1
            findings.append(
                {
                    "target": target,
                    "package": vulnerability.get("PkgName", "unknown-package"),
                    "installed": vulnerability.get("InstalledVersion", "unknown"),
                    "fixed": vulnerability.get("FixedVersion", "not-available"),
                    "severity": severity,
                    "id": vulnerability.get("VulnerabilityID", "unknown-id"),
                    "title": (
                        vulnerability.get("Title")
                        or vulnerability.get("PrimaryURL", "")
                    ),
                }
            )

    findings.sort(
        key=lambda item: (SEVERITY_ORDER.index(item["severity"]), item["package"])
    )
    return counts, findings


def build_reason(critical: int, high: int) -> str:
    if critical > 0:
        return "Critical vulnerabilities detected in the container image."
    if high > 0:
        return "High severity vulnerabilities detected in the container image."
    return (
        "No high or critical vulnerabilities detected in the image scan."
    )


def build_suggestions(critical: int, high: int) -> list[str]:
    suggestions = []

    if critical > 0:
        suggestions.append("- Immediately update or remove critical vulnerabilities.")
        suggestions.append("- Block deployment until critical issues are resolved.")
    if high > 0:
        suggestions.append("- Upgrade affected dependencies to a fixed version.")
        suggestions.append("- Rebuild the Docker image and rerun the Trivy scan.")
    if not suggestions:
        suggestions.append("- Security baseline passed. Continue with deployment checks.")
        suggestions.append("- Preserve the report artifact as evidence for the demo.")

    return suggestions


def format_findings(findings: list[dict[str, str]], limit: int = 5) -> str:
    if not findings:
        return "None"

    lines = []
    for item in findings[:limit]:
        lines.append(
            "- [{severity}] {package} {installed} | fix: {fixed} | id: {id}".format(**item)
        )
    return "\n".join(lines)


def generate_report(payload: dict[str, Any], label: str) -> tuple[str, bool]:
    counts, findings = summarize_vulnerabilities(payload)
    critical = counts.get("CRITICAL", 0)
    high = counts.get("HIGH", 0)
    medium = counts.get("MEDIUM", 0)
    low = counts.get("LOW", 0)

    score = max(100 - (critical * 10 + high * 5), 0)
    passed = critical == 0 and high == 0
    status = "PASS" if passed else "FAIL"
    reason = build_reason(critical, high)
    suggestions_text = "\n".join(build_suggestions(critical, high))
    findings_text = format_findings(findings)

    report = f"""
============================================================
                SENTINELCI SECURITY REPORT
============================================================
REPORT LABEL    : {label}
STATUS          : {status}
SECURITY SCORE  : {score}/100

VULNERABILITY SUMMARY
- Critical: {critical}
- High    : {high}
- Medium  : {medium}
- Low     : {low}

REASON
{reason}

TOP FINDINGS
{findings_text}

RECOMMENDATIONS
{suggestions_text}
============================================================
""".strip()

    return report, passed


def main() -> int:
    args = parse_args()

    try:
        payload = load_report(Path(args.input))
    except FileNotFoundError as exc:
        print(exc)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {args.input}: {exc}")
        return 1

    report, passed = generate_report(payload, args.label)
    Path(args.output).write_text(f"{report}\n", encoding="utf-8")
    print(report)

    if args.fail_on_vulns and not passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
