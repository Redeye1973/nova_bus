# Intern: start Host Bridge (uvicorn). Wordt door nova_dagstart gestart.
param(
    [Parameter(Mandatory = $false)]
    [string]$Port = '8501',
    # Niet $Host: conflicteert met automatische variabele $Host (read-only).
    [string]$BindHost = '0.0.0.0'
)
$ErrorActionPreference = 'Stop'
$bridgeDir = 'L:\!Nova V2\nova_host_bridge'
$logDir = 'L:\!Nova V2\logs'
$logFile = Join-Path $logDir 'bridge.log'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Set-Location -LiteralPath $bridgeDir
# Pip + uvicorn schrijven naar stderr; onder Stop geeft native stderr NativeCommandError.
# Zelfde patroon als start_bridge.ps1: cmd bundelt streams naar log.
cmd /c "python -m pip install ""pydantic>=2.5.0,<3"" ""fastapi>=0.109"" --quiet 2>nul"
cmd /c "cd /d ""$bridgeDir"" && python -m uvicorn main:app --host $BindHost --port $Port >> ""$logFile"" 2>&1"
