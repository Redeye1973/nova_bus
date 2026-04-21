<#
.SYNOPSIS
    Register the NovaHostBridge Scheduled Task.

.DESCRIPTION
    Creates a Task Scheduler entry that runs the bridge at system startup,
    under the SYSTEM account (no password required, runs whether user is
    logged on or not), with auto-restart on failure 3x at 1 minute intervals.

    Run this script ONCE from an elevated PowerShell prompt:
        powershell.exe -NoProfile -ExecutionPolicy Bypass -File register_scheduled_task.ps1

.NOTES
    Idempotent: re-running unregisters first, then registers fresh.
#>
[CmdletBinding()]
param(
    [string]$TaskName    = 'NovaHostBridge',
    [string]$TaskPath    = '\NOVA\',
    [string]$WrapperPs1  = 'L:\!Nova V2\nova_host_bridge\service\start_bridge_service.ps1',
    [string]$Description = 'NOVA Host Bridge: FastAPI on :8500 exposing FreeCAD + QGIS over Tailscale to Hetzner agents.'
)

$ErrorActionPreference = 'Stop'

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must run from an elevated (Administrator) PowerShell. Right-click PowerShell -> Run as administrator."
    exit 2
}

if (-not (Test-Path $WrapperPs1)) {
    Write-Error "Wrapper script not found: $WrapperPs1"
    exit 3
}

Write-Host "Registering Scheduled Task '$TaskPath$TaskName' ..." -ForegroundColor Cyan

$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$WrapperPs1`""

$trigger = New-ScheduledTaskTrigger -AtStartup
$trigger.Delay = 'PT30S'

$principal = New-ScheduledTaskPrincipal `
    -UserId 'SYSTEM' `
    -LogonType ServiceAccount `
    -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

if (Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction SilentlyContinue) {
    Write-Host "Existing task found - removing first." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Confirm:$false
}

Register-ScheduledTask `
    -TaskName    $TaskName `
    -TaskPath    $TaskPath `
    -Action      $action `
    -Trigger     $trigger `
    -Principal   $principal `
    -Settings    $settings `
    -Description $Description | Out-Null

Write-Host "Registered. Verifying..." -ForegroundColor Green
Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath |
    Select-Object TaskName, TaskPath, State,
        @{n='Principal';e={$_.Principal.UserId}},
        @{n='RunLevel'; e={$_.Principal.RunLevel}} |
    Format-List

Write-Host ""
Write-Host "To start it now:    Start-ScheduledTask -TaskName '$TaskName' -TaskPath '$TaskPath'" -ForegroundColor Cyan
Write-Host "To check status:    Get-ScheduledTaskInfo -TaskName '$TaskName' -TaskPath '$TaskPath'" -ForegroundColor Cyan
Write-Host "To remove:          Unregister-ScheduledTask -TaskName '$TaskName' -TaskPath '$TaskPath' -Confirm:`$false" -ForegroundColor Cyan
Write-Host "Log file:           L:\!Nova V2\nova_host_bridge.log" -ForegroundColor Cyan
