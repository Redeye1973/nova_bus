# Disaster Recovery Procedure — NOVA v2

**Laatste test:** 2026-04-25 (PASS)
**RTO (Recovery Time Objective):** 4 uur
**RPO (Recovery Point Objective):** 24 uur (daily backup)

---

## Scenario A: Hetzner prod crash, data intact

1. Escalate via Hetzner support
2. Wacht op server recovery
3. Verify: `docker compose -f /docker/nova-v2/docker-compose.yml ps`
4. Check backup: `borg list --rsh "ssh -i /root/.ssh/id_ed25519 -p 23" u583230@u583230.your-storagebox.de:nova-v2-backup`

Geen data loss verwacht. RTO: ~1u (Hetzner response).

---

## Scenario B: Hetzner prod lost — volledige restore op nieuwe server

### Vereisten
- Nieuwe Hetzner server (CX31+ recommended, Ubuntu 22.04/24.04)
- Toegang tot Hetzner Storage Box (u583230.your-storagebox.de, poort 23)
- Borg passphrase (in `L:\!Nova V2\secrets\nova_v2_passwords.txt`)
- SSH key voor Storage Box (`L:\!Nova V2\secrets\prod-to-hetzner-storage-box.pub`)
- GitHub repo: https://github.com/Redeye1973/nova_bus.git

### Stap 1: Nieuwe server provisioning (~10 min)

```bash
# Op nieuwe server als root
apt update && apt install -y docker.io docker-compose-plugin borgbackup git
systemctl enable docker && systemctl start docker
```

### Stap 2: SSH key voor Storage Box (~5 min)

```bash
# Kopieer bestaande prod key of genereer nieuwe
ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N '' -C 'prod-to-hetzner-storage-box'
# Upload pubkey naar Storage Box (via Hetzner console of install-ssh-key)
cat /root/.ssh/id_ed25519.pub | ssh -p 23 u583230@u583230.your-storagebox.de install-ssh-key
```

### Stap 3: Borg restore (~15 min)

```bash
export BORG_PASSPHRASE='<passphrase uit nova_v2_passwords.txt>'
RSH='ssh -i /root/.ssh/id_ed25519 -p 23 -o StrictHostKeyChecking=accept-new'
REPO='u583230@u583230.your-storagebox.de:nova-v2-backup'

# Lijst archives
borg list --rsh "$RSH" "$REPO"

# Extract laatst beschikbare
LATEST=$(borg list --short --rsh "$RSH" "$REPO" | tail -1)
mkdir -p /tmp/dr-restore && cd /tmp/dr-restore
borg extract --rsh "$RSH" "$REPO::$LATEST"

# Verify extractie
find /tmp/dr-restore -name '*.sql' -exec ls -lh {} \;
```

### Stap 4: Clone repo + restore configs (~5 min)

```bash
cd /docker
git clone https://github.com/Redeye1973/nova_bus.git nova-v2

# Restore .env en service configs uit borg extract
cp /tmp/dr-restore/tmp/nova-backup-staging/docker-nova-v2-*/.env /docker/nova-v2/.env
```

### Stap 5: Start infrastructure (~5 min)

```bash
cd /docker/nova-v2
docker compose up -d postgres redis minio
sleep 10
docker exec nova-v2-postgres pg_isready -h localhost -U postgres
```

### Stap 6: Postgres restore (~5 min)

```bash
PG_V2=$(find /tmp/dr-restore -name 'postgres-v2-*.sql' | head -1)
docker exec -i -e PGPASSWORD=<wachtwoord> nova-v2-postgres \
  psql -h localhost -U postgres -v ON_ERROR_STOP=0 < "$PG_V2"

# Verify
docker exec nova-v2-postgres psql -U postgres -d n8n_v2 -c \
  "SELECT count(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema')"
# Verwacht: ~79 tabellen
```

### Stap 7: Start alle services (~5 min)

```bash
cd /docker/nova-v2
docker compose up -d
sleep 30
docker compose ps
```

### Stap 8: Verify (~5 min)

```bash
# N8n V2 bereikbaar
curl -s http://localhost:5679 | head -1

# Alle containers healthy
docker compose ps --format 'table {{.Name}}\t{{.Status}}'
```

### Stap 9: DNS / Bridge update

- Update `SERVER_IP` in bridge config op Alex's PC
- Update UptimeRobot / Uptime Kuma monitors met nieuw IP
- Test bridge: `curl http://<nieuw-ip>:5679`

### Stap 10: Cron herstellen

```bash
# Backup cron
echo "16 23 * * * /root/nova-backup.sh >> /var/log/nova-backup.log 2>&1" | crontab -
# DR test cron (maandelijks)
(crontab -l; echo "0 4 1 * * /root/nova-dr-test.sh >> /var/log/nova-dr-test.log 2>&1") | crontab -
```

---

## Scenario C: Volledige DR test op apart systeem

Bewezen werkend op 2026-04-25. Procedure:

```bash
# Op willekeurige Linux machine met Docker + borg
export BORG_PASSPHRASE='<passphrase>'
LATEST=$(borg list --short --rsh "ssh -p 23" u583230@u583230.your-storagebox.de:nova-v2-backup | tail -1)
mkdir /tmp/dr-drill && cd /tmp/dr-drill
borg extract --rsh "ssh -p 23" "u583230@u583230.your-storagebox.de:nova-v2-backup::$LATEST"

docker run -d --name dr-sandbox -e POSTGRES_PASSWORD=test postgres:16-alpine
sleep 10
PG_V2=$(find /tmp/dr-drill -name 'postgres-v2-*.sql' | head -1)
docker exec -i -e PGPASSWORD=test dr-sandbox psql -h localhost -U postgres < "$PG_V2"

# Verify: 79 tables in n8n_v2, 110 in gitea, 4 in nova
docker stop dr-sandbox && docker rm dr-sandbox
rm -rf /tmp/dr-drill
```

---

## Contact & Keys

| Item | Locatie |
|------|---------|
| Borg passphrase | `L:\!Nova V2\secrets\nova_v2_passwords.txt` |
| Borg key export | `L:\!Nova V2\secrets\borg-key-nova-v2-backup.txt` |
| Prod SSH key | `L:\!Nova V2\secrets\prod-to-hetzner-storage-box.pub` |
| PC SSH key | `C:\Users\awsme\.ssh\id_ed25519` |
| GitHub repo | https://github.com/Redeye1973/nova_bus.git |
| Storage Box | u583230.your-storagebox.de:23 |

## Tabel referentie (na restore)

| Database | Tabellen | Bron |
|----------|----------|------|
| n8n_v2 | 79 | V2 dump |
| gitea | 110 | V1 dump |
| nova | 4 | V1 dump |
