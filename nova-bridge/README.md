# nova-bridge

Lifecycle-aware alert suppressor and notifier for Nova infra.

## Endpoints
- `POST /lifecycle` (`shutdown|startup|snooze`)
- `GET /lifecycle/status`
- `POST /notify`
- `GET /health`

## Routing policy
- **All infrastructure alerts route through bridge** (`kind=infrastructure`) and are filtered by quiet mode (`nova:quiet_mode`).
- **User messages bypass middleware** (`kind=user_message`) and are always delivered.
- **Critical infra alerts bypass quiet mode** (`kind=critical_alert`).

## Quiet mode TTL
- shutdown event: 7200s
- startup event: 300s
- snooze event: `duration_minutes * 60`

## Storage
Suppressed infra alerts are logged to `suppressed_alerts` (when DB is configured via `NOVA_BRIDGE_DATABASE_URL`).
