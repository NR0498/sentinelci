import sys
import time
from pathlib import Path

import requests


def main() -> int:
    base_url = "http://127.0.0.1:8080"
    proof_path = Path(sys.argv[1] if len(sys.argv) > 1 else "final-report-pass.txt")
    if not proof_path.exists():
        print(f"Proof file not found: {proof_path}")
        return 1

    health = requests.get(f"{base_url}/health", timeout=15)
    health.raise_for_status()
    if health.json().get("status") != "healthy":
        raise RuntimeError(f"Unexpected health response: {health.text}")

    status = requests.get(f"{base_url}/api/aws/status", timeout=15)
    status.raise_for_status()
    if not status.json().get("connected"):
        raise RuntimeError(f"LocalStack is not connected: {status.text}")

    with proof_path.open("rb") as proof_file:
        upload = requests.post(
            f"{base_url}/api/artifacts/upload",
            files={"file": (proof_path.name, proof_file, "text/plain")},
            timeout=30,
        )
    upload.raise_for_status()
    upload_data = upload.json()

    time.sleep(1)
    artifacts = requests.get(f"{base_url}/api/artifacts", timeout=15)
    artifacts.raise_for_status()
    notifications = requests.get(
        f"{base_url}/api/notifications",
        timeout=15,
    )
    notifications.raise_for_status()

    artifact_found = any(
        item["key"] == upload_data["key"]
        for item in artifacts.json()["artifacts"]
    )
    notification_found = any(
        item["message_id"] == upload_data["message_id"]
        for item in notifications.json()["notifications"]
    )
    if not artifact_found:
        raise RuntimeError("Uploaded object was not returned by the S3 API.")
    if not notification_found:
        raise RuntimeError("SNS event did not reach the SQS verification queue.")

    print("SentinelCI LocalStack proof passed.")
    print(f"S3 URI: {upload_data['s3_uri']}")
    print(f"SNS message ID: {upload_data['message_id']}")
    print("Event: artifact.uploaded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
