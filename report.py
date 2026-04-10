def generate_report():
    try:
        with open("trivy-report.txt", "r") as f:
            data = f.read()
    except FileNotFoundError:
        print("❌ trivy-report.txt not found")
        return

    # Count vulnerabilities
    high = data.count("HIGH")
    critical = data.count("CRITICAL")
    medium = data.count("MEDIUM")
    low = data.count("LOW")

    # Security score calculation
    score = 100 - (critical * 10 + high * 5 + medium * 2)
    score = max(score, 0)

    # Determine status
    status = "PASS"
    if critical > 0 or high > 0:
        status = "FAIL"

    # Failure reason
    if critical > 0:
        reason = "Critical vulnerabilities detected which pose severe security risks."
    elif high > 0:
        reason = "High severity vulnerabilities detected that must be resolved."
    elif medium > 0:
        reason = "Medium severity vulnerabilities present, recommended to fix."
    else:
        reason = "No significant vulnerabilities detected."

    # Suggestions
    suggestions = []

    if critical > 0:
        suggestions.append("- Immediately update or remove packages with critical vulnerabilities.")
        suggestions.append("- Avoid deploying this build until issues are resolved.")

    if high > 0:
        suggestions.append("- Upgrade affected dependencies to secure versions.")
        suggestions.append("- Review changelogs for patched releases.")

    if medium > 0:
        suggestions.append("- Consider updating dependencies to reduce risk.")

    if low > 0:
        suggestions.append("- Low severity issues can be monitored and fixed in future updates.")

    if not suggestions:
        suggestions.append("- No action needed. System is secure.")

    # Format suggestions nicely
    suggestions_text = "\n".join(suggestions)

    # Final report
    report = f"""
================ SENTINELCI SECURITY REPORT ================

VULNERABILITY SUMMARY:
CRITICAL : {critical}
HIGH     : {high}
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

    # Save report
    with open("final-report.txt", "w") as f:
        f.write(report)

    print(report)


# Run function
generate_report()