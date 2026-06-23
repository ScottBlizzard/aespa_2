param(
    [ValidateSet("4090", "a40")]
    [string]$Target = "4090"
)

$ErrorActionPreference = "Stop"

$LocalRoot = "D:\AAAI_2"
New-Item -ItemType Directory -Force -Path "$LocalRoot\outputs" | Out-Null

if ($Target -eq "4090") {
    $Remote = "ccj@10.10.217.244:/home/ccj/workspace_1/aaai_2/outputs/*"
    $ScpArgs = @()
} else {
    $Remote = "root@10.91.11.250:/workspace/thymic_project/paper/aaai_2/outputs/*"
    $ScpArgs = @("-P", "10008")
}

Write-Host "Pulling outputs from $Target..."
scp @ScpArgs $Remote "$LocalRoot\outputs\"
Write-Host "Done."

