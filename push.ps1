param(
    [ValidateSet("4090", "a40")]
    [string]$Target = "4090"
)

$ErrorActionPreference = "Stop"

$LocalRoot = "D:\AAAI_2"

if ($Target -eq "4090") {
    $Remote = "ccj@10.10.217.244:/home/ccj/workspace_1/aaai_2"
    $ScpArgs = @()
} else {
    $Remote = "root@10.91.11.250:/workspace/thymic_project/paper/aaai_2"
    $ScpArgs = @("-P", "10008")
}

Write-Host "Syncing src and workflow docs to $Target..."

scp @ScpArgs -r "$LocalRoot\src" "$Remote/"
scp @ScpArgs "$LocalRoot\idea_blueprint.md" "$Remote/"
scp @ScpArgs "$LocalRoot\EXPERIMENT_MANUAL.md" "$Remote/"
scp @ScpArgs "$LocalRoot\EXPERIMENT_FIX_PLAN.md" "$Remote/"
scp @ScpArgs "$LocalRoot\NEXT_STEPS.md" "$Remote/"
scp @ScpArgs "$LocalRoot\experiment_report.md" "$Remote/"
scp @ScpArgs "$LocalRoot\theory_proofs.md" "$Remote/"

Write-Host "Done."

