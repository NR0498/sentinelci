import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


class AwsServiceError(RuntimeError):
    """Raised when the local AWS-compatible services cannot complete a request."""


class AwsArtifactService:
    def __init__(self) -> None:
        self.endpoint_url = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
        self.region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.bucket = os.getenv("S3_BUCKET", "sentinelci-artifacts")
        self.topic_arn = os.getenv(
            "SNS_TOPIC_ARN",
            "arn:aws:sns:us-east-1:000000000000:sentinelci-notifications",
        )
        self.queue_url = os.getenv(
            "SQS_QUEUE_URL",
            "http://localhost:4566/000000000000/sentinelci-events",
        )
        self._client_config = Config(
            connect_timeout=2,
            read_timeout=5,
            retries={"max_attempts": 1},
            s3={"addressing_style": "path"},
        )

    def _client(self, service_name: str):
        return boto3.client(
            service_name,
            endpoint_url=self.endpoint_url,
            region_name=self.region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
            config=self._client_config,
        )

    def status(self) -> dict:
        try:
            self._client("s3").head_bucket(Bucket=self.bucket)
            topic = self._client("sns").get_topic_attributes(
                TopicArn=self.topic_arn
            )
        except (BotoCoreError, ClientError, OSError) as exc:
            return {
                "connected": False,
                "endpoint": self.endpoint_url,
                "bucket": self.bucket,
                "topic_arn": self.topic_arn,
                "error": str(exc),
            }

        return {
            "connected": True,
            "endpoint": self.endpoint_url,
            "bucket": self.bucket,
            "topic_arn": topic["Attributes"]["TopicArn"],
        }

    def upload(
        self,
        file_object: BinaryIO,
        filename: str,
        content_type: str,
    ) -> dict:
        safe_name = Path(filename or "artifact.bin").name
        object_key = f"uploads/{uuid4().hex[:12]}-{safe_name}"
        uploaded_at = datetime.now(timezone.utc).isoformat()

        try:
            self._client("s3").upload_fileobj(
                file_object,
                self.bucket,
                object_key,
                ExtraArgs={
                    "ContentType": content_type or "application/octet-stream",
                    "Metadata": {"uploaded-at": uploaded_at},
                },
            )
            message = {
                "event": "artifact.uploaded",
                "bucket": self.bucket,
                "key": object_key,
                "filename": safe_name,
                "content_type": content_type or "application/octet-stream",
                "uploaded_at": uploaded_at,
            }
            publish = self._client("sns").publish(
                TopicArn=self.topic_arn,
                Subject="SentinelCI artifact uploaded",
                Message=json.dumps(message),
            )
        except (BotoCoreError, ClientError, OSError) as exc:
            raise AwsServiceError(str(exc)) from exc

        return {
            **message,
            "message_id": publish["MessageId"],
            "s3_uri": f"s3://{self.bucket}/{object_key}",
        }

    def list_artifacts(self, limit: int = 20) -> list[dict]:
        try:
            response = self._client("s3").list_objects_v2(
                Bucket=self.bucket,
                Prefix="uploads/",
                MaxKeys=limit,
            )
        except (BotoCoreError, ClientError, OSError) as exc:
            raise AwsServiceError(str(exc)) from exc

        objects = response.get("Contents", [])
        objects.sort(key=lambda item: item["LastModified"], reverse=True)
        return [
            {
                "key": item["Key"],
                "size": item["Size"],
                "last_modified": item["LastModified"].isoformat(),
                "s3_uri": f"s3://{self.bucket}/{item['Key']}",
            }
            for item in objects
        ]

    def receive_notifications(self, limit: int = 10) -> list[dict]:
        try:
            response = self._client("sqs").receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=min(limit, 10),
                WaitTimeSeconds=1,
                VisibilityTimeout=1,
            )
        except (BotoCoreError, ClientError, OSError) as exc:
            raise AwsServiceError(str(exc)) from exc

        notifications = []
        for message in response.get("Messages", []):
            body = json.loads(message["Body"])
            payload = json.loads(body.get("Message", "{}"))
            notifications.append(
                {
                    "message_id": body.get("MessageId"),
                    "subject": body.get("Subject"),
                    "published_at": body.get("Timestamp"),
                    "payload": payload,
                }
            )
        return notifications
