# NOVA host bridge — auto-start (working dir = real bridge tree)
# Poort: NOVA_BRIDGE_PORT > canonical_endpoints.yaml (host_bridge.default_port) > 8501
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$bridgeDir = "L:\!Nova V2\nova_host_bridge"
$logDir = "L:\!Nova V2\logs"
$reader = Join-Path $here "nova_runtime_config.py"
$port = (& python $reader "bridge-port" 2>$null | Out-String).Trim()
if (-not $port -or ($port -notmatch '^\d+$')) { $port = "8501" }
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Set-Location $bridgeDir
# Pip schrijft naar stderr; onder $ErrorActionPreference Stop geeft dat NativeCommandError.
# Via cmd /c blijft pip buiten de strikte native-error pipeline (packages zijn meestal al OK).
cmd /c "python -m pip install ""pydantic>=2.5.0,<3"" ""fastapi>=0.109"" --quiet 2>nul"
$logFile = Join-Path $logDir "bridge.log"
# Uvicorn INFO naar stderr: onder PS7+ Tee/native → NativeCommandError. cmd bundelt stderr naar log.
cmd /c "cd /d ""$bridgeDir"" && python -m uvicorn main:app --host 0.0.0.0 --port $port >> ""$logFile"" 2>&1"
