# NOVA host bridge — TB-001 auto-start (working dir = real bridge tree)
$ErrorActionPreference = "Stop"
$bridgeDir = "L:\!Nova V2\nova_host_bridge"
$logDir = "L:\!Nova V2\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Set-Location $bridgeDir
# Ensure pydantic stack works on this machine (Python 3.14 user install)
python -m pip install "pydantic>=2.5.0,<3" "fastapi>=0.109" --quiet 2>$null
python -m uvicorn main:app --host 0.0.0.0 --port 8500 `
  2>&1 | Tee-Object -FilePath (Join-Path $logDir "bridge.log") -Append
