def generate_report():
    with open("trivy-report.txt", "r") as f:
        data = f.read()

    high = data.count("HIGH")
    critical = data.count("CRITICAL")

    score = 100 - (high * 5 + critical * 10)

    report = f"""
=== SENTINELCI SECURITY REPORT ===

CRITICAL: {critical}
HIGH: {high}

SECURITY SCORE: {score}/100

STATUS: {"FAIL" if (critical or high) else "PASS"}
"""

    with open("final-report.txt", "w") as f:
        f.write(report)

generate_report()