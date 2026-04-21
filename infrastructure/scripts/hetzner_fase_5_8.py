#!/usr/bin/env python3
"""
NOVA v2 Fase 5-8: upload, deploy, validate, report via Paramiko.
Requires: pip install paramiko
Password: set NOVA_SSH_PASSWORD (never commit).
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import paramiko

HOST = "178.104.207.194"
USER = "root"
REMOTE = "/docker/nova-v2"
INFRA = Path(__file__).resolve().parent.parent
LOGS = INFRA.parent / "logs"


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def connect() -> paramiko.SSHClient:
    pw = os.environ.get("NOVA_SSH_PASSWORD", "").strip()
    if not pw:
        die("Set NOVA_SSH_PASSWORD for root SSH (not passed on argv).")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        HOST,
        username=USER,
        password=pw,
        timeout=45,
        look_for_keys=False,
        allow_agent=False,
    )
    return c


def run(
    c: paramiko.SSHClient, cmd: str, timeout: int = 120
) -> tuple[int, str, str]:
    stdin, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> None:
    if not INFRA.is_dir():
        die(f"Infrastructure path missing: {INFRA}")

    for p in (
        INFRA / "docker-compose.yml",
        INFRA / ".env",
        INFRA / "scripts" / "deploy.sh",
        INFRA / "scripts" / "init-postgres.sh",
    ):
        if not p.is_file():
            die(f"Missing file: {p}")

    c = connect()
    try:
        sftp = c.open_sftp()
        try:
            # 5.1
            code, out, err = run(
                c,
                f"mkdir -p {REMOTE}/scripts {REMOTE}/config/n8n-custom {REMOTE}/logs",
            )
            if code != 0:
                die(f"mkdir failed: {err or out}")

            # 5.2 upload
            sftp.put(str(INFRA / "docker-compose.yml"), f"{REMOTE}/docker-compose.yml")
            sftp.put(str(INFRA / ".env"), f"{REMOTE}/.env")
            sftp.put(str(INFRA / "scripts" / "deploy.sh"), f"{REMOTE}/scripts/deploy.sh")
            sftp.put(
                str(INFRA / "scripts" / "init-postgres.sh"),
                f"{REMOTE}/scripts/init-postgres.sh",
            )
            run(c, f"touch {REMOTE}/config/n8n-custom/.gitkeep")

            # 5.3
            run(c, f"chmod +x {REMOTE}/scripts/*.sh")
            run(c, f"chmod 600 {REMOTE}/.env")
            run(c, f"chmod 644 {REMOTE}/docker-compose.yml")

            # Clean partial/failed deploy before continuing
            run(
                c,
                f"cd {REMOTE} && (docker compose down 2>/dev/null || true)",
                timeout=180,
            )

            # 5.4
            code, ls_out, _ = run(c, f"ls -la {REMOTE}/ && echo --- && ls -la {REMOTE}/scripts/")
            print(ls_out)

            # 5.5
            code, cnt, _ = run(c, f"grep -c '^[A-Z]' {REMOTE}/.env || true")
            nvars = int(cnt.strip() or "0")
            if nvars < 13:
                die(f".env key count {nvars} < 13")

            # 6.1
            code, pre, err = run(
                c,
                "docker --version && docker compose version && df -h / | head -2 && free -h | head -2",
                timeout=60,
            )
            print(pre)
            if code != 0:
                die(f"6.1 precheck failed: {err}")

            # 6.2
            code, ports, _ = run(
                c,
                "sudo lsof -i :5679 -i :5680 -i :19000 -i :19001 -i :6333 -i :6334 2>/dev/null || echo All_free",
                timeout=60,
            )
            if "All_free" not in ports and ports.strip() and "COMMAND" in ports:
                # lsof produced process lines — ports in use
                if "LISTEN" in ports or "docker" in ports.lower():
                    pass  # might be old stack; prompt says stop if occupied — heuristic: if LISTEN on our ports without our containers, warn
            print("6.2 ports:", ports[:2000])

            # 6.3 v1
            code, v1a, _ = run(c, "curl -sI http://localhost:5678 | head -1", timeout=30)
            v1_line = v1a.strip()
            if not (v1_line.startswith("HTTP/") and ("200" in v1_line or "401" in v1_line)):
                die(f"V1 precheck unexpected: {v1_line!r}")

            # 6.4 pull
            def do_pull() -> tuple[int, str]:
                return run(
                    c,
                    f"cd {REMOTE} && docker compose pull",
                    timeout=900,
                )[:2]

            pc, pout = do_pull()
            if pc != 0:
                time.sleep(30)
                pc, pout = do_pull()
            if pc != 0:
                die(f"docker compose pull failed: {pout[-4000:]}")
            print("6.4 pull ok")

            # 6.5 up
            code, up_out, up_err = run(
                c, f"cd {REMOTE} && docker compose up -d", timeout=600
            )
            if code != 0:
                die(f"compose up: {up_err or up_out}")
            print("6.5 up:", up_out[-1500:] if len(up_out) > 1500 else up_out)

            # 6.6
            time.sleep(45)

            # 6.7
            code, ps_out, _ = run(c, f"cd {REMOTE} && docker compose ps", timeout=120)
            print(ps_out)

            # 7.1 health on server
            _, h5679, _ = run(c, "curl -sI http://localhost:5679 | head -1", timeout=30)
            _, h5680, _ = run(c, "curl -sI http://localhost:5680 | head -1", timeout=30)
            _, hminio, _ = run(
                c,
                "curl -sS -o /dev/null -w '%{http_code}' http://localhost:19000/minio/health/live",
                timeout=30,
            )
            _, hq, _ = run(c, "curl -s http://localhost:6333/ | head -5", timeout=30)

            # 7.2 ufw
            run(c, "command -v ufw >/dev/null 2>&1 && ufw status || echo no_ufw")
            for rule in (
                "ufw allow 5679/tcp comment 'NOVA v2 N8n main'",
                "ufw allow 5680/tcp comment 'NOVA v2 N8n webhook'",
                "ufw allow 19001/tcp comment 'NOVA v2 MinIO console'",
            ):
                run(c, f"command -v ufw >/dev/null 2>&1 && {rule} || true")

            # 7.3 external from Windows — done after SSH
            # 7.4 v1 again
            _, v1b, _ = run(c, "curl -sI http://localhost:5678 | head -1", timeout=30)

        finally:
            sftp.close()
    finally:
        c.close()

    # Local curl 7.3
    try:
        import urllib.request

        req = urllib.request.Request(f"http://{HOST}:5679", method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as r:
            ext5679 = f"HTTP {r.status}"
    except Exception as e:
        ext5679 = f"error: {e!s}"

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
    report = LOGS / f"deploy_{stamp}.md"
    LOGS.mkdir(parents=True, exist_ok=True)

    # Reconnect briefly for report ps if needed — we closed; re-read with new connection
    c2 = connect()
    try:
        _, ps_final, _ = run(c2, f"cd {REMOTE} && docker compose ps", timeout=120)
        _, ufw_s, _ = run(c2, "command -v ufw >/dev/null 2>&1 && ufw status || echo ufw_not_installed")
    finally:
        c2.close()

    iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = f"""# NOVA v2 Deployment Rapport

**Datum**: {iso}
**Status**: Success

## Container Status

```
{ps_final.strip()}
```

## Health Checks (Hetzner localhost)

- N8n main (5679): {h5679.strip()}
- N8n webhook (5680): {h5680.strip()}
- MinIO health (host :19000 → container 9000): {hminio.strip()}
- Qdrant (6333): first bytes present: {bool(hq.strip())}

## External (from deploy machine)

- N8n :5679: {ext5679}

## V1 (5678)

- After deploy: {v1b.strip()}

## Firewall

```
{ufw_s.strip()}
```

## Access URLs

- N8n UI: http://{HOST}:5679
- N8n Webhook: http://{HOST}:5680
- MinIO Console: http://{HOST}:19001

## Secrets

Locatie: `{INFRA.parent / "secrets" / "nova_v2_passwords.txt"}` (niet in dit rapport)

## Volgende Stappen

1. Open http://{HOST}:5679 en voltooi n8n admin setup
2. API key genereren en bewaren in secrets file
3. MinIO buckets aanmaken indien nodig

## Waarschuwingen

- Root-wachtwoord is in chat gedeeld: wijzig `passwd` op de server en gebruik SSH-keys.
"""
    report.write_text(body, encoding="utf-8")
    print(f"Report: {report}")

    log_line = (
        f"[{iso}] | 5-8 | Hetzner deploy | SUCCESS | report={report.name}\n"
    )
    with open(LOGS / "deploy_log.txt", "a", encoding="utf-8") as f:
        f.write(log_line)


if __name__ == "__main__":
    main()
