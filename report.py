def generate_report():
    try:
        with open("trivy-report.txt", "r") as f:
            data = f.read()
    except FileNotFoundError:
        print("❌ trivy-report.txt not found")
        return

    # Count only HIGH and CRITICAL (same as pipeline)
    high = data.count("HIGH")
    critical = data.count("CRITICAL")

    # Ignore medium/low for scoring (pipeline logic alignment)
    medium = data.count("MEDIUM")
    low = data.count("LOW")

    # Security score based ONLY on high/critical
    score = 100 - (critical * 10 + high * 5)
    score = max(score, 0)

    # Determine status (same as pipeline)
    status = "PASS"
    if critical > 0 or high > 0:
        status = "FAIL"

    # Failure reason
    if critical > 0:
        reason = "Critical vulnerabilities detected in application dependencies."
    elif high > 0:
        reason = "High severity vulnerabilities detected in dependencies."
    else:
        reason = "No high or critical vulnerabilities detected."

    # Suggestions
    suggestions = []

    if critical > 0:
        suggestions.append("- Immediately update or remove critical vulnerabilities.")
        suggestions.append("- Do NOT deploy until resolved.")

    if high > 0:
        suggestions.append("- Upgrade dependencies to patched versions.")
        suggestions.append("- Review security advisories.")

    if not suggestions:
        suggestions.append("- System is secure. No action required.")

    suggestions_text = "\n".join(suggestions)

    # Final report
    report = f"""
================ SENTINELCI SECURITY REPORT ================

VULNERABILITY SUMMARY (Filtered):
CRITICAL : {critical}
HIGH     : {high}

(Info Only)
MEDIUM   : {medium}
LOW      : {low}

SECURITY SCORE: {score}/100

STATUS: {status}

REASON:
{reason}

RECOMMENDATIONS:
{suggestions_text}

============================================================
"""

    with open("final-report.txt", "w") as f:
        f.write(report)

    print(report)


generate_report()