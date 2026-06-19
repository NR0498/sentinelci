import json
import re
from typing import Any


SEVERITIES = ("critical", "high", "medium", "low")


def _empty_counts() -> dict[str, int]:
    return {severity: 0 for severity in SEVERITIES}


def _calculate_score(counts: dict[str, int]) -> int:
    penalties = {"critical": 10, "high": 5, "medium": 2, "low": 1}
    return max(
        100 - sum(counts[name] * penalties[name] for name in SEVERITIES),
        0,
    )


def _result(
    counts: dict[str, int],
    score: int | None = None,
    status: str | None = None,
    analyzer: str = "unknown",
) -> dict[str, Any]:
    computed_status = (
        "FAIL"
        if counts["critical"] > 0 or counts["high"] > 0
        else "PASS"
    )
    normalized_status = (status or computed_status).upper()
    if normalized_status not in {"PASS", "FAIL", "REVIEW"}:
        normalized_status = computed_status
    if counts["critical"] > 0 or counts["high"] > 0:
        normalized_status = "FAIL"
    return {
        "status": normalized_status,
        "score": _calculate_score(counts) if score is None else score,
        "vulnerabilities": counts,
        "analyzer": analyzer,
    }


def _analyze_json(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    counts = _empty_counts()
    summary = payload.get("vulnerabilities")
    if isinstance(summary, dict):
        for severity in SEVERITIES:
            value = summary.get(severity, 0)
            counts[severity] = int(value) if str(value).isdigit() else 0
        score_value = payload.get("security_score")
        score = int(score_value) if str(score_value).isdigit() else None
        return _result(
            counts,
            score=score,
            status=payload.get("status"),
            analyzer="sentinelci-json",
        )

    found = False
    for scan_result in payload.get("Results", []):
        for vulnerability in scan_result.get("Vulnerabilities") or []:
            severity = str(vulnerability.get("Severity", "")).lower()
            if severity in counts:
                counts[severity] += 1
                found = True
    if found or "Results" in payload:
        return _result(counts, analyzer="trivy-json")
    return None


def _extract_text_count(text: str, severity: str) -> int:
    patterns = (
        rf"{severity}\s+vulnerabilit(?:y|ies)\s*[:=]\s*(\d+)",
        rf"{severity}\s*[:=]\s*(\d+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 0


def _analyze_text(text: str) -> dict[str, Any] | None:
    counts = {
        severity: _extract_text_count(text, severity)
        for severity in SEVERITIES
    }
    has_counts = any(
        re.search(severity, text, re.IGNORECASE) for severity in SEVERITIES
    )
    score_match = re.search(
        r"security\s+score\s*[:=]\s*(\d{1,3})(?:\s*/\s*100)?",
        text,
        re.IGNORECASE,
    )
    status_match = re.search(
        r"(?:^|\n)\s*status\s*[:=]\s*(PASS|FAIL|REVIEW)\b",
        text,
        re.IGNORECASE,
    )
    if not has_counts and not score_match and not status_match:
        return None
    score = min(int(score_match.group(1)), 100) if score_match else None
    status = status_match.group(1) if status_match else None
    return _result(counts, score=score, status=status, analyzer="text-report")


def analyze_artifact(
    content: bytes,
    filename: str,
    content_type: str,
) -> dict[str, Any]:
    is_text = content_type.startswith("text/") or filename.lower().endswith(
        (".txt", ".log", ".json")
    )
    if not is_text:
        return {
            "status": "REVIEW",
            "score": None,
            "vulnerabilities": _empty_counts(),
            "analyzer": "unsupported-file",
        }

    text = content.decode("utf-8", errors="replace")
    if filename.lower().endswith(".json") or "json" in content_type:
        try:
            json_result = _analyze_json(json.loads(text))
        except json.JSONDecodeError:
            json_result = None
        if json_result:
            return json_result

    text_result = _analyze_text(text)
    if text_result:
        return text_result
    return {
        "status": "REVIEW",
        "score": None,
        "vulnerabilities": _empty_counts(),
        "analyzer": "unrecognized-report",
    }
