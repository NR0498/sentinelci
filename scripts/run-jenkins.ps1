param(
    [int]$Port = 8080
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$jenkinsWar = Join-Path $repoRoot "tools\jenkins\jenkins.war"
$jenkinsHome = Join-Path $repoRoot "tools\jenkins\home"

if (-not (Test-Path $jenkinsWar)) {
    throw "Jenkins WAR not found at $jenkinsWar. Run scripts\install-tools.ps1 first."
}

if (-not (Test-Path $jenkinsHome)) {
    New-Item -ItemType Directory -Path $jenkinsHome | Out-Null
}

$env:JENKINS_HOME = $jenkinsHome

Write-Host "Starting Jenkins from $jenkinsWar"
Write-Host "JENKINS_HOME=$jenkinsHome"
Write-Host "Open http://localhost:$Port after startup completes."

& java -jar $jenkinsWar "--enable-future-java" "--httpPort=$Port"
