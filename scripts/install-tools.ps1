param(
    [string]$JenkinsUrl = "https://get.jenkins.io/war-stable/latest/jenkins.war"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$jenkinsDir = Join-Path $repoRoot "tools\jenkins"
$ansibleDir = Join-Path $repoRoot "tools\ansible"
$jenkinsWar = Join-Path $jenkinsDir "jenkins.war"

New-Item -ItemType Directory -Force -Path $jenkinsDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $jenkinsDir "home") | Out-Null
New-Item -ItemType Directory -Force -Path $ansibleDir | Out-Null

Write-Host "Downloading Jenkins WAR from $JenkinsUrl"
Invoke-WebRequest -Uri $JenkinsUrl -OutFile $jenkinsWar

Write-Host "Building repo-local Ansible Docker runner"
docker build -t sentinelci-ansible:local $ansibleDir

Write-Host "Tool installation complete."
Write-Host "Start Jenkins with: powershell -ExecutionPolicy Bypass -File scripts\run-jenkins.ps1"
Write-Host "Run Ansible with: powershell -ExecutionPolicy Bypass -File scripts\run-ansible.ps1"
