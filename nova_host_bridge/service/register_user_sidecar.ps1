<#
.SYNOPSIS
    Register NovaHostBridgeSidecar scheduled task (user-context, at-logon).

.DESCRIPTION
    Creates a scheduled task that starts the user-context sidecar bridge
    (port 8501) whenever the current user logs on. No stored password
    needed - runs with the logon token of whoever triggered it.

    Trade-off vs main bridge (SYSTEM, at-startup):
      - only up when user is logged in (includes lock-screen state)
      - gets Steam DRM, Krita Qt profile, user AppData access

    Task name: NovaHostBridgeSidecar
    Task path: \NOVA\
    Action:    powershell.exe -File start_sidecar_service.ps1

.NOTES
    Requires no elevation to CREATE the task (it's a per-user task),
    but elevation is needed to put it in \NOVA\ folder to match main
    bridge convention. This script self-elevates if not admin.
#>
[CmdletBinding()]
param(
    [string]$TaskName   = 'NovaHostBridgeSidecar',
    [string]$TaskPath   = '\NOVA\',
    [string]$ScriptPath = 'L:\!Nova V2\nova_host_bridge\service\start_sidecar_service.ps1',
    [string]$RunAsUser  = $env:USERNAME
)

$currentId = New-Object System.Security.Principal.WindowsPrincipal([System.Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentId.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "elevating..."
    $argsList = @('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath,
                  '-TaskName',$TaskName,'-TaskPath',$TaskPath,'-ScriptPath',$ScriptPath,'-RunAsUser',$RunAsUser)
    Start-Process powershell -Verb RunAs -ArgumentList $argsList -Wait
    exit $LASTEXITCODE
}

if (-not (Test-Path $ScriptPath)) {
    Write-Error "start_sidecar_service.ps1 not found at $ScriptPath"
    exit 1
}

Write-Host "registering scheduled task '$TaskName' at '$TaskPath'"
Write-Host "run-as user: $RunAsUser"
Write-Host "script     : $ScriptPath"

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $RunAsUser

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([System.TimeSpan]::Zero)

$principal = New-ScheduledTaskPrincipal -UserId $RunAsUser -LogonType Interactive -RunLevel Limited

$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
    -Description 'NOVA Host Bridge - User-context sidecar (Aseprite, Krita) on port 8501. Triggered at user logon.'

Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -InputObject $task | Out-Null

Write-Host "registered:"
Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath | Select-Object TaskName, State, @{n='Trigger';e={$_.Triggers[0].CimClass.CimClassName}}, @{n='User';e={$_.Principal.UserId}}

Write-Host "`nstarting task now (sidecar will run as $RunAsUser)..."
Start-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath
Start-Sleep 5
$info = Get-ScheduledTaskInfo -TaskName $TaskName -TaskPath $TaskPath
Write-Host "LastRunTime : $($info.LastRunTime)"
Write-Host "LastResult  : 0x$('{0:X8}' -f $info.LastTaskResult)"
