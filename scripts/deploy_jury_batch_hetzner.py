"""SCP jury service folders to Hetzner and rebuild compose services."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HOST = "root@178.104.207.194"
REMOTE = "/docker/nova-v2/services"
LOCAL = Path(r"L:/!Nova V2/v2_services")
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


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    for a in AGENTS:
        src = LOCAL / a
        run(
            [
                "scp",
                "-o",
                "BatchMode=yes",
                "-r",
                str(src),
                f"{HOST}:{REMOTE}/",
            ]
        )
    svc = " ".join(SERVICES)
    run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            HOST,
            f"cd /docker/nova-v2 && docker compose build {svc} && docker compose up -d {svc}",
        ]
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print("deploy_failed", e, file=sys.stderr)
        sys.exit(1)
