from __future__ import annotations

import os


def log_suppressed_alert(channel: str, alert_text: str, reason: str, quiet_mode_ttl: int) -> None:
    dsn = os.getenv("NOVA_BRIDGE_DATABASE_URL", "")
    if not dsn:
        return
    try:
        import psycopg  # type: ignore
    except Exception:
        return

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO suppressed_alerts (channel, alert_text, reason, quiet_mode_ttl)
            VALUES (%s, %s, %s, %s)
            """,
            (channel, alert_text, reason, quiet_mode_ttl),
        )
        conn.commit()
