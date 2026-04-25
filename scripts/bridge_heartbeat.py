"""NOVA Bridge Heartbeat Pusher.

Polls the local NOVA Host Bridge /health endpoint every INTERVAL seconds.
On each tick pushes a status to Uptime Kuma's Push URL (read from secrets
file). Sends ?status=up when bridge is healthy and ?status=down otherwise.

Runs as Windows Service via NSSM (NOVA_Heartbeat).
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

import requests

LOG_PATH = Path(r"L:\!Nova V2\logs\heartbeat.log")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

PUSH_URL_FILE = Path(r"L:\tools\nova\secrets\push_url.txt")
SECRETS = Path(r"L:\!Nova V2\secrets\nova_v2_passwords.txt")
BRIDGE_URL = "http://localhost:8500/health"
INTERVAL_SEC = 60
PING_TIMEOUT = 10
BRIDGE_TIMEOUT = 5


def read_push_url() -> str | None:
    if PUSH_URL_FILE.exists():
        try:
            value = PUSH_URL_FILE.read_text(encoding="utf-8-sig").strip()
            if value and not value.startswith("#"):
                return value
        except OSError:
            pass
    if not SECRETS.exists():
        return None
    try:
        text = SECRETS.read_text(encoding="utf-8-sig")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("UPTIME_KUMA_PUSH_URL="):
            value = line.split("=", 1)[1].strip()
            return value or None
    return None


def check_bridge() -> tuple[bool, int | None, str]:
    try:
        r = requests.get(BRIDGE_URL, timeout=BRIDGE_TIMEOUT)
        return r.status_code == 200, r.status_code, ""
    except requests.RequestException as exc:
        return False, None, str(exc)


def push(url: str, alive: bool, msg: str, latency_ms: int) -> None:
    status = "up" if alive else "down"
    params = {"status": status, "msg": msg, "ping": latency_ms}
    try:
        r = requests.get(url, params=params, timeout=PING_TIMEOUT)
        log_fn = logging.info if alive else logging.warning
        log_fn(f"push status={status} kuma_http={r.status_code} ping={latency_ms}ms")
    except requests.RequestException as exc:
        logging.error(f"push failed: {exc}")


def main() -> int:
    push_url = read_push_url()
    if not push_url:
        logging.error("UPTIME_KUMA_PUSH_URL is empty — fill in nova_v2_passwords.txt")
        print("FAIL: UPTIME_KUMA_PUSH_URL not set", file=sys.stderr)
        return 1
    logging.info(
        f"Heartbeat started (interval={INTERVAL_SEC}s, push={push_url[:50]}...)"
    )
    while True:
        t0 = time.monotonic()
        alive, code, err = check_bridge()
        latency_ms = int((time.monotonic() - t0) * 1000)
        msg = f"bridge http={code}" if alive else f"bridge DOWN: {err[:120]}"
        push(push_url, alive, msg, latency_ms)
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    sys.exit(main())
