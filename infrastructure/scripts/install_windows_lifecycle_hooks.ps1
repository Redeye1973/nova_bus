# Run as Administrator.
param(
    [string]$WebhookStatusUrl = "http://127.0.0.1:8088/lifecycle/status"
)

$ErrorActionPreference = "Stop"
$targetDir = "C:\nova\scripts"
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null

Copy-Item "L:\!Nova V2\infrastructure\scripts\windows\nova_shutdown_notify.ps1" (Join-Path $targetDir "nova_shutdown_notify.ps1") -Force
Copy-Item "L:\!Nova V2\infrastructure\scripts\windows\nova_startup_notify.ps1" (Join-Path $targetDir "nova_startup_notify.ps1") -Force

try {
    Invoke-RestMethod -Uri $WebhookStatusUrl -Method Get -TimeoutSec 5 | Out-Null
} catch {
    Write-Warning "Lifecycle webhook status check failed: $($_.Exception.Message). Installation continues."
}

# Startup scheduled task
$startupAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\nova\scripts\nova_startup_notify.ps1"
$startupTrigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "NovaLifecycleStartup" -Action $startupAction -Trigger $startupTrigger -RunLevel Highest -Force | Out-Null

# Shutdown via Local Group Policy script registration helper (fallback: task on event log)
$shutdownAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\nova\scripts\nova_shutdown_notify.ps1"
$shutdownTrigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "NovaLifecycleShutdownFallback" -Action $shutdownAction -Trigger $shutdownTrigger -RunLevel Highest -Force | Out-Null

Write-Output "Installed lifecycle scripts to C:\nova\scripts and registered scheduled tasks."
Write-Output "For strict GPO startup/shutdown hooks, see scripts/README_WINDOWS_HOOKS.md"
