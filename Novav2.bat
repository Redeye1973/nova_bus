@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title NOVA v2 — pipeline

set "H=178.104.207.194"
set "LOG_DIR=%~dp0logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" 2>nul

echo.
echo ========================================
echo  NOVA v2 — server + AI + console
echo  Root: %~dp0
echo ========================================
echo.

REM --- 1) Lokale AI: Ollama (indien geinstalleerd) ---
set "OLLAMA_STARTED="
where ollama >nul 2>&1
if %ERRORLEVEL%==0 (
  echo [AI] Starting Ollama serve in new window...
  start "Ollama" cmd /k "ollama serve"
  set "OLLAMA_STARTED=1"
) else if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
  echo [AI] Starting Ollama ^(user install^)...
  start "Ollama" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
  set "OLLAMA_STARTED=1"
) else if exist "%ProgramFiles%\Ollama\ollama.exe" (
  echo [AI] Starting Ollama ^(Program Files^)...
  start "Ollama" "%ProgramFiles%\Ollama\ollama.exe" serve
  set "OLLAMA_STARTED=1"
)

if not defined OLLAMA_STARTED (
  echo [AI] Ollama niet gevonden — overslaan. ^(Installeer van https://ollama.com indien je lokale LLM wilt.^)
)
echo.

REM --- 2) Hetzner: NOVA v2 Docker stack ---
echo [Server] SSH: docker compose up -d op %H% ...
ssh -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=accept-new root@%H% "cd /docker/nova-v2 && docker compose up -d" 2>"%LOG_DIR%\novav2_ssh_last.err"
if errorlevel 1 (
  echo [WARN] SSH of compose mislukt — zie logs\novav2_ssh_last.err  ^(key/password/host^)
) else (
  echo [Server] Docker stack is up-to-date ^(of gestart^).
)
echo.

REM --- 3) Browser: n8n v2 ^(pipeline^), v1 ^(productie^), tools ---
echo [UI] Opening browser tabs...
start "" "http://%H%:5679"
timeout /t 1 /nobreak >nul
start "" "http://%H%:5678"
timeout /t 1 /nobreak >nul
start "" "http://%H%:19001"
timeout /t 1 /nobreak >nul
start "" "http://%H%:6333"

echo.
echo Klaar. n8n v2 = pipeline UI  ^(5679^)  ^|  v1 productie  ^(5678^)  ^|  MinIO  ^(19001^)  ^|  Qdrant  ^(6333^)
echo Venster sluit over 5 sec... ^(dubbelklik opnieuw om te herhalen^)
timeout /t 5 /nobreak >nul
endlocal
exit /b 0
