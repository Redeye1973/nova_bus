@echo off
setlocal DisableDelayedExpansion
rem OpenGL3 avoids many Vulkan loader / overlay crashes (ReShade, RTSS, etc.).
set "GODOT=L:\ZZZ Software\Godot\Godot_v4.6.2-stable_win64.exe"
set "PROJ=%~dp0"
if not exist "%GODOT%" (
  echo Godot not found at: %GODOT%
  pause
  exit /b 1
)
start "" "%GODOT%" --path "%PROJ%" --display-driver windows --rendering-driver opengl3
