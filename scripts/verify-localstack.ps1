$ErrorActionPreference = "Stop"

$baseUrl = if ($env:SENTINELCI_URL) {
    $env:SENTINELCI_URL.TrimEnd("/")
} else {
    "http://127.0.0.1:8080"
}
$proofFile = if ($args.Count -gt 0) {
    $args[0]
} else {
    "final-report-pass.txt"
}

if (-not (Test-Path -LiteralPath $proofFile)) {
    throw "Proof file not found: $proofFile"
}

Write-Host "Checking API health..."
$health = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 15
if ($health.status -ne "healthy") {
    throw "Unexpected health response: $($health | ConvertTo-Json -Compress)"
}

Write-Host "Checking LocalStack S3 and SNS..."
$status = Invoke-RestMethod -Uri "$baseUrl/api/aws/status" -TimeoutSec 15
if (-not $status.connected) {
    throw "LocalStack is not connected: $($status.error)"
}

Write-Host "Uploading $proofFile..."
$uploadJson = curl.exe -sS -X POST `
    -F "file=@$proofFile;type=text/plain" `
    "$baseUrl/api/artifacts/upload"
if ($LASTEXITCODE -ne 0) {
    throw "Artifact upload failed."
}
$upload = $uploadJson | ConvertFrom-Json

Start-Sleep -Seconds 1
$artifacts = Invoke-RestMethod -Uri "$baseUrl/api/artifacts" -TimeoutSec 15
$notifications = Invoke-RestMethod `
    -Uri "$baseUrl/api/notifications" `
    -TimeoutSec 15

$artifact = $artifacts.artifacts |
    Where-Object { $_.key -eq $upload.key } |
    Select-Object -First 1
$notification = $notifications.notifications |
    Where-Object { $_.message_id -eq $upload.message_id } |
    Select-Object -First 1

if (-not $artifact) {
    throw "Uploaded S3 object was not returned by the artifact API."
}
if (-not $notification) {
    throw "SNS notification was not delivered to the verification queue."
}

Write-Host ""
Write-Host "SentinelCI LocalStack proof passed."
Write-Host "S3 URI: $($upload.s3_uri)"
Write-Host "SNS message ID: $($upload.message_id)"
Write-Host "Event: $($notification.payload.event)"
