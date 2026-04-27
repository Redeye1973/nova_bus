# Uptime Kuma Maintenance + Push Setup

## 1) Recurring maintenance window (23:00-07:00)
1. Open Uptime Kuma UI.
2. Go to `Maintenance` -> `Add`.
3. Name: `Nova nightly quiet window`.
4. Type: `Recurring`.
5. Set daily window: start `23:00`, end `07:00`.
6. Apply to Nova infra monitors.
7. Save.

## 2) Route infra alerts through bridge (/notify)
1. In Uptime Kuma: `Notifications` -> `Setup Notification`.
2. Choose `Webhook` (or HTTP Notification type).
3. URL: `http://localhost:8088/notify`
4. Method: `POST`
5. JSON body example:
```json
{
  "kind": "infrastructure",
  "severity": "warning",
  "title": "Kuma monitor alert",
  "detail": "{{heartbeat.msg}}",
  "channels": ["telegram", "discord"],
  "source": "uptime-kuma"
}
```
6. Attach this notification to infra monitors only.

## 3) Push monitor setup (recommended)
1. `Add New Monitor` -> choose `Push`.
2. Name per service (nova-ref, nova-learn, bridge).
3. Copy generated Push URL.
4. Configure each service/heartbeat to call URL every 60s.
5. Grace period: 180s.
6. Save.

This avoids false down alerts when host is intentionally offline.
