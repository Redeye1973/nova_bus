@echo off
REM Fallback start wanneer PowerShell pip/native stderr als fout ziet.
setlocal
set "BRIDGE_DIR=L:\!Nova V2\nova_host_bridge"
set "LOGDIR=L:\!Nova V2\logs"
set "PORT=%NOVA_BRIDGE_PORT%"
if "%PORT%"=="" set "PORT=8501"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
cd /d "%BRIDGE_DIR%"
REM Zelfde deps als start_bridge.ps1; stderr naar nul (cmd gedraagt zich neutraal).
py -3.13 -m pip install "pydantic>=2.5.0,<3" "fastapi>=0.109" --quiet 2>nul
py -3.13 -m uvicorn main:app --host 0.0.0.0 --port %PORT% >> "%LOGDIR%\bridge.log" 2>&1
