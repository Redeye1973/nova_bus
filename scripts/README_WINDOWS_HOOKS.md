# Windows Lifecycle Hooks (Nova)

## Best effort installer
1. Open PowerShell as Administrator.
2. Run:
   `powershell -NoProfile -ExecutionPolicy Bypass -File "L:\!Nova V2\infrastructure\scripts\install_windows_lifecycle_hooks.ps1"`
3. Verify tasks:
   - `NovaLifecycleStartup`
   - `NovaLifecycleShutdownFallback`

## Manual GPO startup/shutdown script method
1. Run `gpedit.msc`
2. Go to `Computer Configuration -> Windows Settings -> Scripts (Startup/Shutdown)`
3. Startup -> Add -> `C:\nova\scripts\nova_startup_notify.ps1`
4. Shutdown -> Add -> `C:\nova\scripts\nova_shutdown_notify.ps1`
5. Reboot and verify `C:\nova\logs\lifecycle.log`

## Notes
- Webhook calls use 5s timeout and never block shutdown.
- Failures are logged only.
