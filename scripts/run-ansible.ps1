param(
    [string]$Inventory = "ansible/inventory.ini.example",
    [string]$Playbook = "ansible/deploy.yml",
    [string[]]$ExtraArgs
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$imageName = "sentinelci-ansible:local"
$inventoryPath = Join-Path $repoRoot $Inventory
$playbookPath = Join-Path $repoRoot $Playbook

if (-not (Test-Path $inventoryPath)) {
    throw "Inventory file not found at $inventoryPath"
}

if (-not (Test-Path $playbookPath)) {
    throw "Playbook file not found at $playbookPath"
}

Write-Host "Running Ansible from repo-local Docker image $imageName"

$dockerArgs = @(
    "run",
    "--rm",
    "-v", "${repoRoot}:/workspace",
    "-w", "/workspace",
    $imageName,
    "ansible-playbook",
    "-i", $Inventory,
    $Playbook
)

if ($ExtraArgs) {
    $dockerArgs += $ExtraArgs
}

& docker @dockerArgs
