from fastapi.testclient import TestClient

from app.artifact_analysis import analyze_artifact
from app.main import app, aws_service

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SentinelCI is running"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_get_user():
    response = client.get("/users/7")
    assert response.status_code == 200
    assert response.json() == {"user_id": 7, "name": "test_user"}


def test_aws_status(monkeypatch):
    monkeypatch.setattr(
        aws_service,
        "status",
        lambda: {"connected": True, "bucket": "sentinelci-artifacts"},
    )
    response = client.get("/api/aws/status")
    assert response.status_code == 200
    assert response.json()["connected"] is True


def test_upload_artifact_publishes_notification(monkeypatch):
    expected = {
        "event": "artifact.uploaded",
        "s3_uri": "s3://sentinelci-artifacts/uploads/proof.txt",
        "message_id": "message-123",
    }
    monkeypatch.setattr(aws_service, "upload", lambda *_args: expected)

    response = client.post(
        "/api/artifacts/upload",
        files={"file": ("proof.txt", b"working proof", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_list_artifacts(monkeypatch):
    monkeypatch.setattr(
        aws_service,
        "list_artifacts",
        lambda: [{"key": "uploads/proof.txt", "size": 13}],
    )
    response = client.get("/api/artifacts")
    assert response.status_code == 200
    assert response.json()["artifacts"][0]["key"] == "uploads/proof.txt"


def test_list_notifications(monkeypatch):
    monkeypatch.setattr(
        aws_service,
        "receive_notifications",
        lambda: [{"payload": {"event": "artifact.uploaded"}}],
    )
    response = client.get("/api/notifications")
    assert response.status_code == 200
    assert response.json()["notifications"][0]["payload"]["event"] == (
        "artifact.uploaded"
    )


def test_analyze_trivy_failure():
    analysis = analyze_artifact(
        b'{"Results":[{"Vulnerabilities":['
        b'{"Severity":"CRITICAL"},{"Severity":"HIGH"}]}]}',
        "trivy.json",
        "application/json",
    )
    assert analysis["status"] == "FAIL"
    assert analysis["score"] == 70
    assert analysis["vulnerabilities"]["critical"] == 1
    assert analysis["vulnerabilities"]["high"] == 1


def test_analyze_text_report():
    analysis = analyze_artifact(
        b"Status: FAIL\nSecurity score: 72/100\n"
        b"Critical: 1\nHigh: 3\nMedium: 4\nLow: 2\n",
        "report.txt",
        "text/plain",
    )
    assert analysis["status"] == "FAIL"
    assert analysis["score"] == 36
    assert analysis["vulnerabilities"] == {
        "critical": 1,
        "high": 3,
        "medium": 4,
        "low": 2,
    }


def test_unrecognized_file_requires_review():
    analysis = analyze_artifact(
        b"\x89PNG",
        "screenshot.png",
        "image/png",
    )
    assert analysis["status"] == "REVIEW"
    assert analysis["score"] is None
