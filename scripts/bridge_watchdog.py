"""NOVA Bridge watchdog — restarts NOVA_Bridge_Service if 3 consecutive
health checks fail. Designed to run as the NOVA_Bridge_Watchdog Windows
Service (NSSM)."""
from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

import requests

LOG_DIR = Path(r"L:\!Nova V2\logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "watchdog.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

BRIDGE_URL = "http://localhost:8500/health"
SERVICE_NAME = "NOVA_Bridge_Service"
CHECK_INTERVAL = 60
MAX_FAILURES = 3
POST_RESTART_GRACE = 30


def check_bridge() -> bool:
    try:
        r = requests.get(BRIDGE_URL, timeout=5)
        return r.status_code == 200
    except Exception as exc:
        logging.warning("health check failed: %s", exc)
        return False


def restart_service() -> None:
    logging.warning("Restarting %s ...", SERVICE_NAME)
    try:
        subprocess.run(["sc", "stop", SERVICE_NAME], check=False, timeout=30)
        time.sleep(3)
        subprocess.run(["sc", "start", SERVICE_NAME], check=False, timeout=30)
        time.sleep(5)
        logging.info("Service %s restart command issued", SERVICE_NAME)
    except Exception as exc:
        logging.error("restart failed: %s", exc)


def main() -> None:
    failures = 0
    logging.info("Watchdog started (interval=%ss, max_fail=%s)", CHECK_INTERVAL, MAX_FAILURES)
    while True:
        if check_bridge():
            if failures > 0:
                logging.info("Bridge recovered after %s failures", failures)
            failures = 0
        else:
            failures += 1
            logging.warning("Bridge down (%s/%s)", failures, MAX_FAILURES)
            if failures >= MAX_FAILURES:
                restart_service()
                failures = 0
                time.sleep(POST_RESTART_GRACE)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
