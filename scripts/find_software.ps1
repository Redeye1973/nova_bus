#Requires -Version 5.1
<#
.SYNOPSIS
  NOVA — software discovery via expliciete wortels (geen volledige C:\ recursie).

  Output: docs/software_discovery_full.json
#>

$ErrorActionPreference = 'SilentlyContinue'
$RepoRoot = if ($PSScriptRoot) { (Resolve-Path (Join-Path $PSScriptRoot '..')).Path } else { 'L:\!Nova V2' }
$outFile = Join-Path $RepoRoot 'docs\software_discovery_full.json'

# Per tool: lijst van mappen om onder te zoeken (max diepte per map) + bestandsnamen
$plan = @(
    @{ Tool = 'Aseprite';      Depth = 6;  Patterns = @('Aseprite.exe'); Roots = @('L:\SteamLibrary\steamapps\common\Aseprite') }
    @{ Tool = 'Blender';       Depth = 5;  Patterns = @('blender.exe'); Roots = @('C:\Program Files\Blender Foundation') }
    @{ Tool = 'Krita';         Depth = 4;  Patterns = @('krita.exe'); Roots = @('C:\Program Files\Krita (x64)') }
    @{ Tool = 'GIMP';          Depth = 5;  Patterns = @('gimp-console-3.2.exe','gimp-3.2.exe','gimp-console-3.0.exe','gimp-3.0.exe'); Roots = @('L:\ZZZ Software\GIMP 3','C:\Program Files\GIMP 3','C:\Program Files\GIMP 2') }
    @{ Tool = 'Inkscape';      Depth = 5;  Patterns = @('inkscape.exe'); Roots = @('L:\ZZZ Software\InkScape','C:\Program Files\Inkscape') }
    @{ Tool = 'DAZ_Studio';    Depth = 4;  Patterns = @('DAZStudio.exe'); Roots = @('C:\Program Files\DAZ 3D\DAZStudio4') }
    @{ Tool = 'FreeCAD';       Depth = 5;  Patterns = @('FreeCAD.exe','FreeCADCmd.exe'); Roots = @('L:\ZZZ Software\FreeCad') }
    @{ Tool = 'Godot';         Depth = 3;  Patterns = @('Godot*.exe'); Roots = @('L:\ZZZ Software\Godot') }
    @{ Tool = 'QGIS';          Depth = 8;  Patterns = @('qgis_process.exe','qgis-ltr-bin.exe'); Roots = @('C:\Program Files\QGIS 3.40.13') }
    @{ Tool = 'GRASS_bundled'; Depth = 6;  Patterns = @('qgis.g.browser8.exe'); Roots = @('C:\Program Files\QGIS 3.40.13\apps\qgis-ltr\grass') }
    @{ Tool = 'SuperCollider'; Depth = 4;  Patterns = @('sclang.exe','scsynth.exe'); Roots = @('L:\ZZZ Software\Super Collider') }
    @{ Tool = 'SoX';           Depth = 4;  Patterns = @('sox.exe'); Roots = @('L:\ZZZ Software\SoX') }
    @{ Tool = 'LDtk';          Depth = 3;  Patterns = @('LDtk.exe'); Roots = @('L:\ZZZ Software\ldtk') }
    @{ Tool = 'Audacity';      Depth = 4;  Patterns = @('Audacity.exe'); Roots = @('C:\Program Files\Audacity') }
    @{ Tool = 'OBS_Studio';    Depth = 4;  Patterns = @('obs64.exe'); Roots = @('C:\Program Files\obs-studio','C:\Program Files\OBS Studio') }
    @{ Tool = 'MakeHuman';     Depth = 4;  Patterns = @('makehuman.exe'); Roots = @('C:\Program Files\MakeHuman') }
    @{ Tool = 'Unreal_Engine'; Depth = 6;  Patterns = @('UnrealEditor.exe'); Roots = @('L:\UE_5.7') }
    @{ Tool = 'Poser';         Depth = 4;  Patterns = @('Poser.exe'); Roots = @('C:\Program Files\Poser*') }
    @{ Tool = 'Tiled';         Depth = 4;  Patterns = @('tiled.exe'); Roots = @('C:\Program Files\Tiled','L:\ZZZ Software\Tiled') }
    @{ Tool = 'PyxelEdit';     Depth = 3;  Patterns = @('PyxelEdit.exe'); Roots = @('L:\ZZZ Software\PyxelEdit') }
    @{ Tool = 'Audiocraft';    Depth = 3;  Patterns = @('python.exe'); Roots = @('L:\ZZZ Software\Audiocraft\venv\Scripts') }
)

$drives = @('C','D','E','G','H','L') | ForEach-Object { "$_`:\" } | Where-Object { Test-Path $_ }

$results = [ordered]@{
    scan_timestamp = (Get-Date).ToString('o')
    drives_present = @($drives)
    note           = 'Bounded roots only; geen volledige drive-recursie.'
    tools          = [ordered]@{}
}

function Add-Hits {
    param($ToolName, $Hits)
    if (-not $results.tools[$ToolName]) { $results.tools[$ToolName] = @() }
    foreach ($h in $Hits) {
        $entry = @{ Path = $h.FullName; Size = $h.Length; Modified = $h.LastWriteTime.ToString('o') }
        $dup = $false
        foreach ($e in $results.tools[$ToolName]) { if ($e.Path -eq $entry.Path) { $dup = $true; break } }
        if (-not $dup) { $results.tools[$ToolName] += $entry }
    }
}

foreach ($item in $plan) {
    foreach ($root in $item.Roots) {
        $resolved = $null
        if ($root -match '\*') {
            $parent = Split-Path $root -Parent
            $leaf = Split-Path $root -Leaf
            if (Test-Path $parent) {
                Get-ChildItem -Path $parent -Directory -Filter $leaf.Replace('*','*') -ErrorAction SilentlyContinue | ForEach-Object {
                    $hits = @()
                    foreach ($pat in $item.Patterns) {
                        if ($pat -match '\*') {
                            $star = Join-Path $_.FullName '*'
                            Get-ChildItem -Path $star -Recurse -Depth $item.Depth -File -Include $pat -ErrorAction SilentlyContinue |
                                Select-Object -First 5 FullName, Length, LastWriteTime | ForEach-Object { $hits += $_ }
                        } else {
                            Get-ChildItem -LiteralPath $_.FullName -Filter $pat -Recurse -Depth $item.Depth -File -ErrorAction SilentlyContinue |
                                Select-Object -First 5 FullName, Length, LastWriteTime | ForEach-Object { $hits += $_ }
                        }
                    }
                    Add-Hits -ToolName $item.Tool -Hits $hits
                }
            }
        } elseif (Test-Path $root) {
            $hits = @()
            foreach ($pat in $item.Patterns) {
                if ($pat -match '\*') {
                    $star = Join-Path $root '*'
                    Get-ChildItem -Path $star -Recurse -Depth $item.Depth -File -Include $pat -ErrorAction SilentlyContinue |
                        Select-Object -First 5 FullName, Length, LastWriteTime | ForEach-Object { $hits += $_ }
                } else {
                    Get-ChildItem -LiteralPath $root -Filter $pat -Recurse -Depth $item.Depth -File -ErrorAction SilentlyContinue |
                        Select-Object -First 5 FullName, Length, LastWriteTime | ForEach-Object { $hits += $_ }
                }
            }
            Add-Hits -ToolName $item.Tool -Hits $hits
        }
    }
}

$json = $results | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($outFile, $json, [System.Text.UTF8Encoding]::new($false))
Write-Host "Discovery complete: $outFile"
$with = ($results.tools.Keys | Where-Object { $results.tools[$_].Count -gt 0 })
Write-Host ("Tools with hits ({0}): {1}" -f $with.Count, ($with -join ', '))
