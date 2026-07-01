param(
    [ValidateSet("4090", "a40")]
    [string]$Target = "4090"
)

$ErrorActionPreference = "Stop"

$LocalRoot = "D:\AAAI_2"

if ($Target -eq "4090") {
    $RemoteHost = "ccj@10.10.217.244"
    $RemotePath = "/home/ccj/workspace_1/aaai_2"
    $ScpArgs = @()
    $SshArgs = @()
} else {
    $RemoteHost = "root@10.91.11.250"
    $RemotePath = "/workspace/thymic_project/paper/aaai_2"
    $ScpArgs = @("-P", "10008")
    $SshArgs = @("-p", "10008")
}

Write-Host "Syncing experiment code to $Target..."

ssh @SshArgs $RemoteHost "mkdir -p '$RemotePath/src' '$RemotePath/scripts' '$RemotePath/outputs' '$RemotePath/analysis/paper_assets'"

$Remote = "${RemoteHost}:${RemotePath}"

scp @ScpArgs -r "$LocalRoot\src" "$Remote/"
scp @ScpArgs -r "$LocalRoot\scripts" "$Remote/"

ssh @SshArgs $RemoteHost "rm -rf '$RemotePath/src/__pycache__'"

Write-Host "Done."
