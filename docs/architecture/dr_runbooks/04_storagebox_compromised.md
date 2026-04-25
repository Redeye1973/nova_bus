---
title: DR Runbook — Storage Box Compromised
severity: critical
expected_time: 30-60 min
---

# Hetzner Storage Box — Wachtwoord Rotation

## Detectie
- Onverwachte backup deletes
- Onbekende SSH sessies
- Hetzner security alert

## Stappen

1. **Revoke huidige SSH key**
   ```bash
   # Op Hetzner server
   ssh -p 23 u583230@u583230.your-storagebox.de
   # In storagebox shell:
   rm .ssh/authorized_keys
   ```

2. **Genereer nieuwe SSH key**
   ```bash
   ssh-keygen -t ed25519 -C "nova-backup-rotated" -f ~/.ssh/id_storagebox_new
   ```

3. **Upload nieuwe key naar Storage Box**
   - Via Hetzner Cloud Console > Storage Boxes > Settings
   - Of via wachtwoord auth: `ssh-copy-id -p 23 -i ~/.ssh/id_storagebox_new u583230@u583230.your-storagebox.de`

4. **Wijzig Storage Box wachtwoord**
   - Hetzner Cloud Console > Storage Boxes > Change Password

5. **Update backup script**
   ```bash
   # Update ~/.ssh/config of BORG_RSH in nova-backup.sh
   export BORG_RSH="ssh -p 23 -i ~/.ssh/id_storagebox_new"
   ```

6. **Test backup**
   ```bash
   borg list
   borg create --stats ::rotation-test /docker/nova-v2/.env
   ```

## Verificatie
- `borg list` werkt met nieuwe key
- Oude key geeft "Permission denied"
- Handmatige backup run succesvol
