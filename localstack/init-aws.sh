#!/bin/bash
set -euo pipefail

BUCKET_NAME="${S3_BUCKET:-sentinelci-artifacts}"
TOPIC_NAME="${SNS_TOPIC_NAME:-sentinelci-notifications}"
QUEUE_NAME="${SQS_QUEUE_NAME:-sentinelci-events}"

awslocal s3api create-bucket --bucket "${BUCKET_NAME}" >/dev/null 2>&1 || true
TOPIC_ARN="$(awslocal sns create-topic --name "${TOPIC_NAME}" --query TopicArn --output text)"
QUEUE_URL="$(awslocal sqs create-queue --queue-name "${QUEUE_NAME}" --query QueueUrl --output text)"
QUEUE_ARN="$(awslocal sqs get-queue-attributes --queue-url "${QUEUE_URL}" --attribute-names QueueArn --query Attributes.QueueArn --output text)"

awslocal sns subscribe \
  --topic-arn "${TOPIC_ARN}" \
  --protocol sqs \
  --notification-endpoint "${QUEUE_ARN}" >/dev/null

echo "SentinelCI LocalStack resources ready"
echo "Bucket: ${BUCKET_NAME}"
echo "Topic: ${TOPIC_ARN}"
echo "Queue: ${QUEUE_URL}"
