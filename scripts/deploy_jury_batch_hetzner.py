"""SCP jury service folders to Hetzner and rebuild compose services.

On Windows, paths like ``L:\\!Nova V2\\...`` break bare ``scp`` invocations when
shells interpret ``!``. We run ``scp`` via ``cmd /d /c`` with the *source* path
in double quotes (no ``bash -c`` wrapper for remote targets).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HOST = "root@178.104.207.194"
REMOTE_SERVICES = "/docker/nova-v2/services"
LOCAL = Path(r"L:\!Nova V2\v2_services")
AGENTS = [
    "agent_03_audio_jury",
    "agent_04_3d_model_jury",
    "agent_05_gis_jury",
    "agent_06_cad_jury",
    "agent_07_narrative_jury",
    "agent_08_character_art_jury",
    "agent_09_illustration_jury",
]
SERVICES = [
    "agent-03-audio-jury",
    "agent-04-3d-model-jury",
    "agent-05-gis-jury",
    "agent-06-cad-jury",
    "agent-07-narrative-jury",
    "agent-08-character-art-jury",
    "agent-09-illustration-jury",
]

SSH_SCP_OPTS = [
    "-o",
    "BatchMode=yes",
    "-o",
    "StrictHostKeyChecking=no",
    "-o",
    "ConnectTimeout=10",
]


def _scp_upload_dir(src: Path, dest_host: str, remote_parent: str) -> None:
    """Upload ``src`` (directory) to ``dest_host:remote_parent/`` (sequential, one agent at a time)."""
    src_abs = src.resolve()
    if not src_abs.is_dir():
        raise FileNotFoundError(src_abs)

    remote_target = f"{dest_host}:{remote_parent.rstrip('/')}/"

    if sys.platform == "win32":
        # Double-quote source for cmd.exe / PowerShell safety when path contains '!'.
        inner = str(src_abs).replace('"', r"\"")
        cmdline = (
            "scp "
            + " ".join(SSH_SCP_OPTS)
            + f' -r "{inner}" {remote_target}'
        )
        subprocess.run(["cmd.exe", "/d", "/c", cmdline], check=True)
    else:
        cmd = ["scp", *SSH_SCP_OPTS, "-r", str(src_abs), remote_target]
        subprocess.run(cmd, check=True)


def _ssh_compose_build_up() -> None:
    svc = " ".join(SERVICES)
    remote_cmd = f"cd /docker/nova-v2 && docker compose build {svc} && docker compose up -d {svc}"
    cmd = ["ssh", *SSH_SCP_OPTS, HOST, remote_cmd]
    print("+", " ".join(cmd[: len(SSH_SCP_OPTS) + 2]), "<remote compose build/up>", flush=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    n = len(AGENTS)
    for i, a in enumerate(AGENTS, start=1):
        src = LOCAL / a
        print(f"[{i}/{n}] scp start: {src} -> {HOST}:{REMOTE_SERVICES}/", flush=True)
        _scp_upload_dir(src, HOST, REMOTE_SERVICES)
        print(f"[{i}/{n}] scp done:  {a}", flush=True)

    print(f"[compose] docker compose build + up ({n} services) …", flush=True)
    _ssh_compose_build_up()
    print("[compose] done.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print("deploy_failed", e, file=sys.stderr)
        sys.exit(1)
