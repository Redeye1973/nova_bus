# NOVA Bridge Software Inventory Scan
# Check welke tools aanwezig zijn op PC, output naar CSV + markdown

param(
    [string]$OutputDir = "L:\!Nova V2\bridge\nova_bridge\handoff\shared_state"
)

Write-Host ""
Write-Host "=== NOVA Bridge Software Inventory ===" -ForegroundColor Cyan
Write-Host ""

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}

# Tool definitions: name, command, version_flag, description, required_for
$tools = @(
    @{ Name="FreeCAD"; Command="freecad"; VersionFlag="--version"; Category="Baseline"; Fase="1"; Description="Parametric 3D CAD"; },
    @{ Name="QGIS"; Command="qgis_process"; VersionFlag="--version"; Category="Baseline"; Fase="2"; Description="Geographic Information System"; },
    @{ Name="Blender"; Command="blender"; VersionFlag="--version"; Category="Fase1"; Fase="1"; Description="3D creation suite"; },
    @{ Name="Aseprite"; Command="aseprite"; VersionFlag="--version"; Category="Fase1"; Fase="1"; Description="Pixel art editor (paid)"; },
    @{ Name="Godot"; Command="godot"; VersionFlag="--version"; Category="Fase1"; Fase="1"; Description="Game engine"; },
    @{ Name="GRASS"; Command="grass"; VersionFlag="--version"; Category="Fase4"; Fase="4"; Description="GRASS GIS (geospatial)"; },
    @{ Name="GIMP"; Command="gimp"; VersionFlag="--version"; Category="Fase4"; Fase="4"; Description="Raster image editor"; },
    @{ Name="Krita"; Command="krita"; VersionFlag="--version"; Category="Fase4"; Fase="4"; Description="Digital painting"; },
    @{ Name="Inkscape"; Command="inkscape"; VersionFlag="--version"; Category="Fase4"; Fase="4"; Description="Vector graphics"; },
    @{ Name="Ollama"; Command="ollama"; VersionFlag="--version"; Category="LLM"; Fase="All"; Description="Local LLM inference"; },
    @{ Name="Python"; Command="python"; VersionFlag="--version"; Category="Runtime"; Fase="All"; Description="Python 3.x"; },
    @{ Name="Node"; Command="node"; VersionFlag="--version"; Category="Runtime"; Fase="MCP"; Description="Node.js for MCP"; },
    @{ Name="Git"; Command="git"; VersionFlag="--version"; Category="Runtime"; Fase="All"; Description="Version control"; },
    @{ Name="Docker"; Command="docker"; VersionFlag="--version"; Category="Runtime"; Fase="Infra"; Description="Container runtime"; }
)

# Scan
$results = @()
foreach ($tool in $tools) {
    Write-Host "Checking $($tool.Name)..." -NoNewline
    
    $cmd = Get-Command $tool.Command -ErrorAction SilentlyContinue
    
    if ($cmd) {
        $path = $cmd.Source
        try {
            $versionOutput = & $tool.Command $tool.VersionFlag 2>&1 | Select-Object -First 1
            $version = ($versionOutput -split "`n")[0].Trim()
        } catch {
            $version = "unknown"
        }
        
        Write-Host " OK ($version)" -ForegroundColor Green
        
        $results += [PSCustomObject]@{
            Tool = $tool.Name
            Status = "Installed"
            Version = $version
            Path = $path
            InPath = "Yes"
            Category = $tool.Category
            Fase = $tool.Fase
            Description = $tool.Description
        }
    } else {
        # Check common install locations even if not in PATH
        $commonPaths = @()
        switch ($tool.Name) {
            "FreeCAD" { $commonPaths = @("C:\Program Files\FreeCAD *\bin\FreeCAD.exe") }
            "QGIS" { $commonPaths = @("C:\Program Files\QGIS *\bin\qgis_process-qgis.bat") }
            "Blender" { $commonPaths = @("C:\Program Files\Blender Foundation\Blender *\blender.exe") }
            "Aseprite" { $commonPaths = @("C:\Program Files\Aseprite\aseprite.exe", "${env:LOCALAPPDATA}\Aseprite\aseprite.exe") }
            "Godot" { $commonPaths = @("C:\Godot\godot.exe", "C:\Program Files\Godot\godot.exe") }
            "GRASS" { $commonPaths = @("C:\Program Files\GRASS GIS *\grass*.bat") }
            "GIMP" { $commonPaths = @("C:\Program Files\GIMP 2\bin\gimp-*.exe", "C:\Program Files\GIMP 3\bin\gimp-*.exe") }
            "Krita" { $commonPaths = @("C:\Program Files\Krita (x64)\bin\krita.exe") }
            "Inkscape" { $commonPaths = @("C:\Program Files\Inkscape\bin\inkscape.exe") }
            "Ollama" { $commonPaths = @("${env:LOCALAPPDATA}\Programs\Ollama\ollama.exe") }
        }
        
        $foundPath = $null
        foreach ($p in $commonPaths) {
            $resolved = Resolve-Path $p -ErrorAction SilentlyContinue
            if ($resolved) {
                $foundPath = $resolved[0].Path
                break
            }
        }
        
        if ($foundPath) {
            Write-Host " installed but NOT IN PATH" -ForegroundColor Yellow
            $results += [PSCustomObject]@{
                Tool = $tool.Name
                Status = "Installed"
                Version = "check manually"
                Path = $foundPath
                InPath = "No"
                Category = $tool.Category
                Fase = $tool.Fase
                Description = $tool.Description
            }
        } else {
            Write-Host " MISSING" -ForegroundColor Red
            $results += [PSCustomObject]@{
                Tool = $tool.Name
                Status = "Missing"
                Version = ""
                Path = ""
                InPath = "N/A"
                Category = $tool.Category
                Fase = $tool.Fase
                Description = $tool.Description
            }
        }
    }
}

# Save CSV
$csvPath = Join-Path $OutputDir "software_inventory.csv"
$results | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
Write-Host ""
Write-Host "CSV saved: $csvPath" -ForegroundColor Cyan

# Save markdown
$mdPath = Join-Path $OutputDir "software_inventory.md"
$installed = ($results | Where-Object { $_.Status -eq "Installed" -and $_.InPath -eq "Yes" }).Count
$installedNotInPath = ($results | Where-Object { $_.Status -eq "Installed" -and $_.InPath -eq "No" }).Count
$missing = ($results | Where-Object { $_.Status -eq "Missing" }).Count

$mdContent = @"
# NOVA Bridge Software Inventory

**Scan date**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  
**Host**: $env:COMPUTERNAME

## Summary

- Installed + in PATH: $installed
- Installed but not in PATH: $installedNotInPath
- Missing: $missing
- Total: $($results.Count)

## Per tool

| Tool | Status | In PATH | Version | Fase | Path |
|------|--------|---------|---------|------|------|
"@

foreach ($r in $results) {
    $pathDisplay = if ($r.Path) { $r.Path } else { "-" }
    $versionDisplay = if ($r.Version) { $r.Version } else { "-" }
    $statusIcon = switch ($r.Status) {
        "Installed" { if ($r.InPath -eq "Yes") { "✓" } else { "⚠️" } }
        "Missing" { "✗" }
        default { "?" }
    }
    $mdContent += "`n| $($r.Tool) | $statusIcon $($r.Status) | $($r.InPath) | $versionDisplay | $($r.Fase) | $pathDisplay |"
}

$mdContent += @"


## Volgende stappen

### Als missing tools

Handoff 002 (install_missing) kan de meeste tools autonoom installeren:
- Blender, Godot, GRASS, GIMP, Inkscape: autonoom via installer
- Python, Node, Git, Docker: meestal al aanwezig

### Als tools aanwezig maar niet in PATH

Toevoegen aan system PATH via handoff 002 of handmatig:
``````powershell
# Example voor Blender
`$blenderPath = "C:\Program Files\Blender Foundation\Blender 4.5"
`[System.Environment]::SetEnvironmentVariable("Path", `$env:Path + ";`$blenderPath", "Machine")
``````

### Aseprite (paid tool)

Niet autonoom te installeren. Aanschaf via:
- Steam
- itch.io  
- Aseprite.org direct

### Node.js

Als missing: `winget install OpenJS.NodeJS.LTS`

### Python 3.11+

Als missing of oude versie: `winget install Python.Python.3.11`

## Bridge adapter prioriteit

Op basis van wat aanwezig is, in volgorde:

1. **Wat al werkt**: FreeCAD, QGIS bridge adapters draaien
2. **Na basis installs**: Blender, Aseprite, PyQt, Godot adapters (handoffs 003, 004)
3. **Uitbreiding**: GRASS, GIMP, Krita, Inkscape adapters (handoff 005)

"@

$mdContent | Set-Content -Path $mdPath -Encoding UTF8
Write-Host "Markdown saved: $mdPath" -ForegroundColor Cyan

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Installed + in PATH: $installed" -ForegroundColor Green
Write-Host "Installed but not in PATH: $installedNotInPath" -ForegroundColor Yellow
Write-Host "Missing: $missing" -ForegroundColor Red
Write-Host ""

# Display table
$results | Format-Table Tool, Status, InPath, Version, Fase -AutoSize
