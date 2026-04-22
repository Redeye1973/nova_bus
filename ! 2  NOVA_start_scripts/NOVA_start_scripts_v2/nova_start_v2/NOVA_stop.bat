@echo off
REM NOVA_stop.bat - stopt lokale services

where pwsh >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    pwsh.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0NOVA_stop.ps1"
) else (
    powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0NOVA_stop.ps1"
)

echo.
pause
