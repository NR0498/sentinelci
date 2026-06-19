import json
from argparse import Namespace
from pathlib import Path

from scripts.build_pipeline_result import build_result
from scripts.discord_notify import build_payload


def test_trusted_result_combines_raw_scanner_evidence(
    tmp_path: Path,
    monkeypatch,
):
    trivy = tmp_path / "trivy.json"
    pip_audit = tmp_path / "pip-audit.json"
    coverage = tmp_path / "coverage.xml"
    trivy.write_text(
        json.dumps(
            {
                "Results": [
                    {
                        "Vulnerabilities": [
                            {
                                "VulnerabilityID": "CVE-TEST-1",
                                "PkgName": "library-a",
                                "InstalledVersion": "1.0",
                                "FixedVersion": "1.1",
                                "Severity": "HIGH",
                                "Title": "Test vulnerability",
                            }
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    pip_audit.write_text(
        json.dumps(
            {
                "dependencies": [
                    {
                        "name": "library-b",
                        "version": "2.0",
                        "vulns": [
                            {
                                "id": "PYSEC-TEST-2",
                                "fix_versions": ["2.1"],
                                "description": "Dependency advisory",
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    coverage.write_text(
        '<coverage line-rate="0.82"></coverage>',
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_SHA", "123456789")
    args = Namespace(
        trivy=str(trivy),
        pip_audit=str(pip_audit),
        coverage=str(coverage),
    )

    result = build_result(args)

    assert result["security"]["status"] == "failed"
    assert result["security"]["score"] == 80
    assert result["security"]["counts"]["high"] == 2
    assert result["quality"]["coverage_percent"] == 82.0
    assert result["run"]["commit"] == "1234567"


def test_discord_payload_uses_trusted_result():
    result = {
        "generated_at": "2026-06-19T00:00:00+00:00",
        "project": {"name": "SentinelCI"},
        "run": {
            "branch": "main",
            "commit": "abc1234",
            "actor": "developer",
            "url": "https://github.com/example/actions/runs/1",
        },
        "quality": {
            "coverage_percent": 82,
            "tests_status": "passed",
            "lint_status": "passed",
        },
        "security": {
            "status": "failed",
            "score": 90,
            "counts": {"critical": 0, "high": 1},
            "findings": [
                {
                    "id": "CVE-TEST",
                    "package": "library",
                    "installed_version": "1.0",
                    "fixed_version": "1.1",
                }
            ],
        },
    }

    payload = build_payload(result)

    assert payload["embeds"][0]["title"] == "Pipeline FAILED: SentinelCI"
    assert "CVE-TEST" in payload["embeds"][0]["fields"][3]["value"]
