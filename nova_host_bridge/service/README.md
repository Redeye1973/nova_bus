# nova_host_bridge — service installation

Two ways to make the bridge survive reboots without manual start.

## Files

| File | Purpose |
|------|---------|
| `start_bridge_service.ps1` | Wrapper script: sets cwd, env, exec's uvicorn via `Start-Process`, then loops with retry (default 3x @ 60 s) on non-zero exit. Healthy runs (>5 min) reset the attempt counter. Produces three logs: `nova_host_bridge.log` (wrapper meta, append + 10 MB rotation), `nova_host_bridge.log.uvicorn` and `nova_host_bridge.log.uvicorn.err` (uvicorn streams, truncated each restart). |
| `register_scheduled_task.ps1` | Option A: Task Scheduler entry under SYSTEM account, restart 3x at 1 min intervals. |
| `register_nssm_service.ps1` | Option B: Real Windows service via NSSM with auto-restart + log rotation. |

## Defaults assumed

- Bridge code root: `L:\!Nova V2\nova_host_bridge`
- Config file: `L:\!Nova V2\nova_config.yaml`
- Python: `C:\Python314\python.exe` with deps **installed system-wide** in `C:\Python314\Lib\site-packages`
- Bind: `0.0.0.0:8500`
- Log: `L:\!Nova V2\nova_host_bridge.log` (+ `.uvicorn` / `.uvicorn.err`)

Override with named parameters if your layout differs.

### System-wide dep install (required for SYSTEM account)

SYSTEM cannot see per-user packages at `%APPDATA%\Roaming\Python\...`. Install
deps into the system site-packages from an **elevated** PowerShell:

```powershell
C:\Python314\python.exe -m pip install `
  --target=C:\Python314\Lib\site-packages `
  --upgrade fastapi 'uvicorn[standard]' pydantic pyyaml httpx
```

The wrapper sets `$env:PYTHONNOUSERSITE='1'` so behavior is identical whether
it runs as SYSTEM or as your interactive user.

## Option A — Task Scheduler

```powershell
# From elevated PowerShell:
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File "L:\!Nova V2\nova_host_bridge\service\register_scheduled_task.ps1"
```

Creates task `\NOVA\NovaHostBridge`. SYSTEM account, no password storage,
runs whether or not user is logged in.

**Restart model (two layers of resilience):**

1. **Wrapper-level retry** (deterministic, in-process): when uvicorn exits
   non-zero, the wrapper waits 60 s and retries, up to 3 times. A run
   lasting >5 min resets the attempt counter. This is the reliable path for
   mid-run crashes.
2. **Task Scheduler RestartCount=3/RestartInterval=1min** (outer fallback):
   if the wrapper itself dies, Task Scheduler re-launches it.

Together these give "3× @ 1 min" behaviour that actually works on Windows
(Task Scheduler's own `restart on failure` is unreliable for child-process
exits).

```powershell
# Start it now (without rebooting)
Start-ScheduledTask -TaskName 'NovaHostBridge' -TaskPath '\NOVA\'

# Status
Get-ScheduledTaskInfo -TaskName 'NovaHostBridge' -TaskPath '\NOVA\'

# Tail logs (wrapper supervises, uvicorn streams to .uvicorn / .uvicorn.err)
Get-Content 'L:\!Nova V2\nova_host_bridge.log'         -Wait   # wrapper meta
Get-Content 'L:\!Nova V2\nova_host_bridge.log.uvicorn.err' -Wait   # uvicorn INFO/ERR

# Remove
Unregister-ScheduledTask -TaskName 'NovaHostBridge' -TaskPath '\NOVA\' -Confirm:$false
```

## Option B — NSSM (recommended for production)

NSSM gives a real Windows service: `services.msc` shows it, `Get-Service` works,
graceful stop signals propagate cleanly, log rotation is built-in.

1. Download NSSM 2.24 from <https://nssm.cc/release/nssm-2.24.zip>
2. Extract `win64\nssm.exe` to `C:\Tools\nssm.exe`
3. Add `C:\Tools` to PATH **or** pass `-NssmExe 'C:\Tools\nssm.exe'`
4. From elevated PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File "L:\!Nova V2\nova_host_bridge\service\register_nssm_service.ps1"
```

Creates service `NovaHostBridge` (auto-start, LocalSystem, restart on exit
after 60 s, log rotation at 10 MB).

```powershell
Get-Service NovaHostBridge
nssm edit   NovaHostBridge      # GUI for tweaks
nssm restart NovaHostBridge
nssm remove NovaHostBridge confirm
```

## Verification (both options)

After the service/task is running:

```powershell
# Local
Invoke-RestMethod http://127.0.0.1:8500/health

# From Hetzner (over Tailscale)
ssh root@178.104.207.194 "curl -sS http://100.64.0.2:8500/health"
```

You should see `"engine":"freecad_via_bridge"` reflected in `agent-21`'s health
response too.

## Trade-offs

| Aspect | Task Scheduler | NSSM |
|--------|---------------|------|
| Built into Windows | yes | external download |
| Visible in `services.msc` | no | yes |
| Graceful stop | basic kill | proper SCM stop signal |
| Log rotation | manual (wrapper script) | built-in |
| Failure restart granularity | 3 attempts × 1 min | continuous with backoff |
| Setup complexity | one PS1 | one PS1 + nssm.exe |

For NOVA's current single-PC bridge, **Task Scheduler is enough**. Move to
NSSM if you ever want to: monitor it via the Service control panel, integrate
with monitoring tools that watch services, or run multiple bridge instances.

## Python deps must live in system site-packages

When the wrapper runs as SYSTEM (Task Scheduler default), it cannot see
per-user packages at `C:\Users\<u>\AppData\Roaming\Python\Python314\site-packages`.
Install the bridge's deps **system-wide** (one-time, elevated):

```powershell
# Elevated PowerShell, one shot:
& 'C:\Python314\python.exe' -m pip install --upgrade `
    --target='C:\Python314\Lib\site-packages' `
    fastapi 'uvicorn[standard]' pydantic pyyaml httpx
```

The wrapper sets `PYTHONNOUSERSITE=1` so this layout is honoured the same
way whether the bridge runs as SYSTEM or as the desktop user.

Symptom if you skip this step: `python.exe: No module named uvicorn` in
`nova_host_bridge.log.uvicorn.err`, wrapper exits with code -1, task
result `0xFFFFFFFF`.

## SYSTEM account caveats

Both options run the bridge under `LocalSystem` (NT AUTHORITY\SYSTEM). Things
to know:

- SYSTEM has full access to local NTFS drives by default. `L:\` should work.
- SYSTEM cannot see network drives (UNC paths) without explicit setup.
- SYSTEM **does see Tailscale** because Tailscale itself runs as a Windows
  service — the `100.64.0.2` interface is up at boot.
- FreeCAD subprocess runs under SYSTEM too; if FreeCAD needs user-profile
  config (it usually doesn't for `freecadcmd` headless), switch
  `ObjectName`/`UserId` to your user account and store the password.
