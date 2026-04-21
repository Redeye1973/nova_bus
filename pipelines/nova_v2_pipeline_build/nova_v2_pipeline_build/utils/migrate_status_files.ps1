<#
.SYNOPSIS
  Migreert oude agent_*_status.json naar het verplichte veldenset van status_schema.json.

.DESCRIPTION
  Zet ontbrekende required velden waar mogelijk af uit legacy keys (n8n_v2, deployed_at).
  Bestaande extra keys (service, n8n_v2, endpoints, ...) blijven behouden.

.PARAMETER StatusDir
  Map met agent_*_status.json (default: L:\!Nova V2\status)

.PARAMETER WebhookBase
  Basis-URL voor webhook_url als alleen webhook_path bekend is (zonder trailing slash).

.PARAMETER WhatIf
  Toon welke bestanden gewijzigd zouden worden zonder te schrijven.
#>
[CmdletBinding()]
param(
    [Parameter()]
    [string]$StatusDir = 'L:\!Nova V2\status',

    [Parameter()]
    [string]$WebhookBase = 'http://178.104.207.194:5680/webhook',

    [Parameter()]
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-HasProp {
    param([object]$Obj, [string]$Name)
    return ($null -ne $Obj) -and ($Obj.PSObject.Properties.Name -contains $Name)
}

function Get-WebhookUrl {
    param(
        [object]$Doc,
        [string]$Base
    )
    if (Test-HasProp $Doc 'webhook_url') {
        $u = $Doc.webhook_url
        if ($u -and $u.ToString().Trim().Length -gt 0) {
            return $u.ToString().Trim()
        }
    }
    if (Test-HasProp $Doc 'n8n_v2') {
        $n = $Doc.n8n_v2
        if ($n -and (Test-HasProp $n 'webhook_path')) {
            $p = $n.webhook_path.ToString().Trim().TrimStart('/')
            return ('{0}/{1}' -f $Base.TrimEnd('/'), $p)
        }
    }
    return $null
}

function Normalize-AgentNumber {
    param($n)
    if ($null -eq $n) { return $null }
    if ($n -is [int] -or $n -is [long]) { return [int]$n }
    $s = $n.ToString().Trim()
    if ($s -match '^\d+$') { return [int]$s }
    return $n
}

$files = Get-ChildItem -LiteralPath $StatusDir -Filter 'agent_*_status.json' -File -ErrorAction Stop
if (-not $files -or $files.Count -eq 0) {
    Write-Warning "Geen agent_*_status.json gevonden in $StatusDir"
    exit 0
}

$migrated = 0
$whatIfCount = 0
foreach ($f in $files) {
    $raw = [System.IO.File]::ReadAllText($f.FullName)
    $j = $raw | ConvertFrom-Json

    $changed = $false

    $rawNum = if (Test-HasProp $j 'agent_number') { $j.agent_number } else { $null }
    $num = Normalize-AgentNumber $rawNum
    if ($null -ne $num -and $rawNum -ne $num) {
        $j | Add-Member -NotePropertyName agent_number -NotePropertyValue $num -Force
        $changed = $true
    }

    $wh = Get-WebhookUrl -Doc $j -Base $WebhookBase
    $curWh = if (Test-HasProp $j 'webhook_url') { $j.webhook_url } else { $null }
    if ($null -ne $wh -and [string]$curWh -ne $wh) {
        $j | Add-Member -NotePropertyName webhook_url -NotePropertyValue $wh -Force
        $changed = $true
    }

    if (-not (Test-HasProp $j 'fallback_mode') -or ($null -eq $j.fallback_mode)) {
        $j | Add-Member -NotePropertyName fallback_mode -NotePropertyValue $false -Force
        $changed = $true
    }

    if (-not (Test-HasProp $j 'tests_passed') -or ($null -eq $j.tests_passed)) {
        $j | Add-Member -NotePropertyName tests_passed -NotePropertyValue $false -Force
        $changed = $true
    }

    if (-not (Test-HasProp $j 'built_at') -or [string]::IsNullOrWhiteSpace([string]$j.built_at)) {
        $alt = $null
        if (Test-HasProp $j 'deployed_at') { $alt = $j.deployed_at }
        if ([string]::IsNullOrWhiteSpace([string]$alt)) {
            $alt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')
        }
        $j | Add-Member -NotePropertyName built_at -NotePropertyValue ([string]$alt) -Force
        $changed = $true
    }

    if (-not (Test-HasProp $j 'status') -or [string]::IsNullOrWhiteSpace([string]$j.status)) {
        $j | Add-Member -NotePropertyName status -NotePropertyValue 'active' -Force
        $changed = $true
    }

    if (-not (Test-HasProp $j 'name') -or [string]::IsNullOrWhiteSpace([string]$j.name)) {
        $suffix = if ($null -ne $num) { [string]$num } else { 'unknown' }
        $j | Add-Member -NotePropertyName name -NotePropertyValue ('agent_' + $suffix) -Force
        $changed = $true
    }

    $wf = if (Test-HasProp $j 'workflow_id') { $j.workflow_id } else { $null }
    $n8nWf = $null
    if ((Test-HasProp $j 'n8n_v2') -and $j.n8n_v2 -and (Test-HasProp $j.n8n_v2 'workflow_id')) {
        $n8nWf = $j.n8n_v2.workflow_id
    }
    if ([string]::IsNullOrWhiteSpace([string]$wf) -and -not [string]::IsNullOrWhiteSpace([string]$n8nWf)) {
        $j | Add-Member -NotePropertyName workflow_id -NotePropertyValue $n8nWf.ToString() -Force
        $changed = $true
    }

    if (-not $changed) {
        Write-Host "[skip] $($f.Name) — geen wijzigingen nodig."
        continue
    }

    $required = @('agent_number', 'name', 'status', 'fallback_mode', 'webhook_url', 'built_at', 'tests_passed')
    $missing = @()
    foreach ($k in $required) {
        if (-not ($j.PSObject.Properties.Name -contains $k)) {
            $missing += $k
            continue
        }
        if ($k -eq 'tests_passed' -or $k -eq 'fallback_mode') { continue }
        if ([string]::IsNullOrWhiteSpace([string]$j.$k)) { $missing += $k }
    }
    if ($missing.Count -gt 0) {
        Write-Warning "[fail] $($f.Name) — kan niet afronden; ontbrekend of leeg: $($missing -join ', ')"
        continue
    }

    $json = $j | ConvertTo-Json -Depth 20
    if ($WhatIf) {
        Write-Host "[whatif] $($f.Name) — zou schrijven ($($json.Length) chars)."
        $whatIfCount++
        continue
    }

    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($f.FullName, $json, $utf8)
    Write-Host "[ok]   $($f.Name) — gemigreerd."
    $migrated++
}

if ($WhatIf) {
    Write-Host "Klaar (WhatIf). Zou wijzigen: $whatIfCount / $($files.Count); niets geschreven."
} else {
    Write-Host "Klaar. Gemigreerde bestanden: $migrated / $($files.Count)."
}
