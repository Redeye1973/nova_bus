<#
.SYNOPSIS
  Kopieert AI Assistant Hub naar een Godot-project en schakelt het in via project.godot.

.PARAMETER ProjectRoot
  Map met project.godot.

.PARAMETER TemplateRoot
  Standaard: L:\!Nova V2\templates\godot\ai_assistant_hub
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot,

    [Parameter(Mandatory = $false)]
    [string] $TemplateRoot = "L:\!Nova V2\templates\godot\ai_assistant_hub"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$pluginCfgMarker = "res://addons/ai_assistant_hub/plugin.cfg"

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "project.godot"))) {
    throw "Geen project.godot in: $ProjectRoot"
}
if (-not (Test-Path -LiteralPath (Join-Path $TemplateRoot "plugin.cfg"))) {
    throw "Template ontbreekt of incompleet: $TemplateRoot"
}

$dest = Join-Path $ProjectRoot "addons\ai_assistant_hub"
New-Item -ItemType Directory -Path (Split-Path $dest) -Force | Out-Null
Copy-Item -Path $TemplateRoot -Destination $dest -Recurse -Force

$pg = Join-Path $ProjectRoot "project.godot"
$lines = @(Get-Content -LiteralPath $pg)

foreach ($ln in $lines) {
    if ($ln -like "*$pluginCfgMarker*") {
        Write-Host "project.godot already references plugin; addon files refreshed."
        exit 0
    }
}

function Merge-PackedStringArrayLine {
    param([string] $Line)
    if ($Line -notmatch '^\s*enabled\s*=\s*PackedStringArray\((.*)\)\s*$') {
        return $Line
    }
    $inner = $Matches[1].Trim()
    if ([string]::IsNullOrWhiteSpace($inner)) {
        return 'enabled=PackedStringArray("' + $pluginCfgMarker + '")'
    }
    return 'enabled=PackedStringArray(' + $inner + ', "' + $pluginCfgMarker + '")'
}

$editorIdx = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i].Trim() -eq "[editor_plugins]") {
        $editorIdx = $i
        break
    }
}

$out = [System.Collections.Generic.List[string]]::new()

if ($editorIdx -lt 0) {
    foreach ($ln in $lines) { $out.Add($ln) }
    $out.Add("")
    $out.Add("[editor_plugins]")
    $out.Add("")
    $out.Add('enabled=PackedStringArray("' + $pluginCfgMarker + '")')
}
else {
    $enabledIdx = -1
    for ($j = $editorIdx + 1; $j -lt $lines.Count; $j++) {
        if ($lines[$j] -match '^\s*\[') { break }
        if ($lines[$j] -match '^\s*enabled\s*=\s*PackedStringArray') {
            $enabledIdx = $j
            break
        }
    }
    for ($k = 0; $k -lt $lines.Count; $k++) {
        if ($k -eq $editorIdx) {
            $out.Add($lines[$k])
            if ($enabledIdx -lt 0) {
                $out.Add('enabled=PackedStringArray("' + $pluginCfgMarker + '")')
            }
            continue
        }
        if ($k -eq $enabledIdx) {
            $out.Add((Merge-PackedStringArrayLine -Line $lines[$k]))
            continue
        }
        $out.Add($lines[$k])
    }
}

$text = (($out | ForEach-Object { $_ }) -join "`n") + "`n"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($pg, $text, $utf8NoBom)
Write-Host "AI Assistant Hub installed and enabled: $ProjectRoot"
