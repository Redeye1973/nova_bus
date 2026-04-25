@echo off
REM ============================================================
REM NOVA_start.bat - Startup wrapper
REM ============================================================
REM Probeert eerst PowerShell 7 (pwsh), valt terug op Windows PowerShell 5
REM PowerShell 7 heeft betere compat, 5.1 werkt ook met dit script

where pwsh >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    pwsh.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0NOVA_start.ps1"
) else (
    powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0NOVA_start.ps1"
)

echo.
echo Druk een toets om te sluiten...
pause >nul
