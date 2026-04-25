<#
.SYNOPSIS
  DAZ Studio starten in officiële headless-modus en een DazScript (.dsa) uitvoeren.

.DESCRIPTION
  DAZ ondersteunt dit zelf via CLI (zie DAZ Studio Command Line Options):
    -headless          Geen GUI
    -noPrompt          Geen dialogs (automation; bij dialog sluit DAZ vaak af)
    -noDefaultScene    Geen startup-scene

  Gebruik een .dsa op een pad zonder "!" — PowerShell/cmd knipt anders af op L:\! ...

.PARAMETER DazExe
  Pad naar DAZStudio.exe. Default: env DAZ_STUDIO_EXE, anders Program Files-pad uit inventory.

.PARAMETER DsaPath
  Volledig pad naar het uit te voeren DazScript.

.PARAMETER CopyOutputs
  Na afloop: kopieer alles uit C:\Users\Public\nova_dazz_out\ naar deze map (optioneel).

.EXAMPLE
  .\scripts\daz_headless_run.ps1
  .\scripts\daz_headless_run.ps1 -DsaPath "C:\Users\Public\nova_dazz_batch\batch_female_redhair.dsa" -CopyTo "L:\! 2 Nova v2  OUTPUT !\Dazz"
#>
[CmdletBinding()]
param(
    [string]$DazExe = $env:DAZ_STUDIO_EXE,
    [string]$DsaPath = "C:\Users\Public\nova_dazz_batch\batch_female_redhair.dsa",
    [string]$CopyTo = ""
)

$ErrorActionPreference = "Stop"

if (-not $DazExe) {
    $DazExe = "C:\Program Files\DAZ 3D\DAZStudio4\DAZStudio.exe"
}

if (-not (Test-Path -LiteralPath $DazExe)) {
    throw "DAZ niet gevonden: $DazExe — zet `$env:DAZ_STUDIO_EXE of pas -DazExe aan (zie config\tool_paths.yaml daz_studio.executable)."
}

if (-not (Test-Path -LiteralPath $DsaPath)) {
    throw ".dsa niet gevonden: $DsaPath"
}

Write-Host "DAZ headless: $DazExe"
Write-Host "Script:       $DsaPath"

$proc = Start-Process -FilePath $DazExe -ArgumentList @(
    "-noPrompt",
    "-headless",
    "-noDefaultScene",
    $DsaPath
) -Wait -PassThru

$code = $proc.ExitCode
Write-Host "Exit code: $code"

if ($CopyTo) {
    $src = "C:\Users\Public\nova_dazz_out"
    if (Test-Path -LiteralPath $src) {
        New-Item -ItemType Directory -Force -Path $CopyTo | Out-Null
        Copy-Item -Path (Join-Path $src "*") -Destination $CopyTo -Force
        Write-Host "Output gekopieerd naar: $CopyTo"
    } else {
        Write-Warning "Geen bronmap $src — niets gekopieerd."
    }
}

exit $code
