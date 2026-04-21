# NOVA v2 Security Fix + Docs Update — Cursor Automaat

Automatische uitvoering van drie taken:
1. Root password roteren (genereer nieuwe, vervang oude, update secrets)
2. SSH key-only login activeren
3. MinIO poort afwijking documenteren in README + .env.template

Plus optioneel: UFW firewall activeren voor basis hardening.

## Gebruik

1. Open Cursor in `L:\!Nova V2\`
2. Open Composer (Ctrl+I)
3. Kopieer prompt hieronder
4. Plak + Enter

## De prompt

```
Voer NOVA v2 security fixes en documentatie updates uit.

CONTEXT:
- V2 draait op 178.104.207.194 (root@, password-based SSH)
- Root password is in chat gelekt, moet geroteerd
- MinIO gebruikt afwijkende poorten 19000/19001 (niet 9000/9001)
- SSH key van mij moet als enige login worden
- Werkmap: L:\!Nova V2\
- Secrets locatie: L:\!Nova V2\secrets\nova_v2_passwords.txt

TAKEN IN VOLGORDE:

== TAAK 1: SSH KEY SETUP (eerst!) ==

1.1 Check of SSH key bestaat:
    Test-Path "$env:USERPROFILE\.ssh\id_ed25519.pub"

    Als niet bestaat:
    ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\id_ed25519" -N ""
    (genereert zonder passphrase)

1.2 Kopieer public key naar Hetzner:
    Oude password wordt nog 1x gevraagd. Gebruik bestaand password.
    
    Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | ssh root@178.104.207.194 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"

1.3 Test key-based login:
    ssh -o PreferredAuthentications=publickey -o PasswordAuthentication=no root@178.104.207.194 "echo KEY_WORKS"
    
    Als "KEY_WORKS" terugkomt: gelukt
    Als mislukt: stop, rapporteer, NIET doorgaan met password wijziging

== TAAK 2: ROOT PASSWORD ROTEREN ==

2.1 Genereer nieuw sterk password (lokaal):
    $bytes = New-Object byte[] 24
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $new_root_password = [Convert]::ToBase64String($bytes)
    
    Spaties eruit indien aanwezig: $new_root_password = $new_root_password -replace '=','x'

2.2 Wijzig root password op Hetzner via SSH (key-based nu):
    echo "root:$new_root_password" | ssh root@178.104.207.194 "chpasswd"
    
    Verify: ssh root@178.104.207.194 "echo PASSWORD_CHANGED_OK"
    (moet werken met key, niet met password meer)

2.3 Update secrets file:
    Voeg toe aan L:\!Nova V2\secrets\nova_v2_passwords.txt:
    
    # Server root access (na rotatie 2026-04-19)
    SERVER_ROOT_PASSWORD=<new_root_password>
    SERVER_SSH_KEY=~/.ssh/id_ed25519
    SERVER_SSH_ACCESS_METHOD=key_only
    
    Markeer oude password als invalid.

== TAAK 3: SSH DAEMON HARDENEN (optioneel maar aanbevolen) ==

3.1 Backup SSH config:
    ssh root@178.104.207.194 "cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup_$(date +%Y%m%d)"

3.2 Schrijf nieuwe config settings:
    ssh root@178.104.207.194 "sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config"
    ssh root@178.104.207.194 "sed -i 's/^#*PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config"
    ssh root@178.104.207.194 "sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config"

3.3 Reload SSH:
    ssh root@178.104.207.194 "systemctl reload sshd"
    
    BELANGRIJK: NIET restart, alleen reload. Restart sluit huidige sessie.

3.4 Verify password login disabled:
    ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no root@178.104.207.194 "echo SHOULD_FAIL" 2>&1
    
    Verwacht: "Permission denied" (password auth weigeren)
    Als wel accepteer: SSH config niet goed toegepast, escaleer

== TAAK 4: MINIO POORT DOCS UPDATEN ==

4.1 Update infrastructure/README.md:
    
    Voeg na "Poorten overzicht" tabel toe:
    
    ## MinIO Poort Afwijking (belangrijk)
    
    Standaard MinIO gebruikt poorten 9000 (S3 API) en 9001 (console).
    Op deze Hetzner server zijn die poorten al bezet door een andere 
    Docker service. Daarom zijn de hostpoorten aangepast naar:
    
    - 19000 (S3 API, extern) → 9000 (container intern)
    - 19001 (console, extern) → 9001 (container intern)
    
    Container-interne communicatie blijft op 9000/9001. Alleen de
    host-mapping is anders.
    
    URLs om te gebruiken:
    - MinIO S3 API: http://178.104.207.194:19000
    - MinIO Console: http://178.104.207.194:19001
    
    Aangepaste bestanden met deze poorten:
    - docker-compose.yml (port mappings)
    - scripts/deploy.sh (health checks)
    - scripts/hetzner_fase_5_8.py (UFW regels, curl checks)

4.2 Update infrastructure/.env.template:
    
    Voeg bij MinIO sectie commentaar toe:
    
    # ============================================
    # MINIO (S3-compatible storage)
    # ============================================
    # LET OP: Op deze host zijn poorten 9000/9001 bezet door andere
    # Docker service. Host ports zijn daarom 19000/19001.
    # Container interne poorten blijven 9000/9001 (niet wijzigen).
    # Zie docker-compose.yml voor exacte port mapping.
    MINIO_ROOT_USER=nova_admin
    MINIO_ROOT_PASSWORD=CHANGE_ME_STRONG_PASSWORD_32_CHARS

4.3 Update bovenste README.md in L:\!Nova V2\:
    
    Als sectie "Access URLs" bestaat: update MinIO console naar :19001
    Als niet: voeg toe

== TAAK 5: UFW FIREWALL ACTIVEREN (optioneel) ==

5.1 Check huidige UFW status:
    ssh root@178.104.207.194 "ufw status"

5.2 Vraag gebruiker:
    "UFW staat nu inactive. Activeren met deze regels?
    
    - SSH (22/tcp) - jouw toegang behouden
    - N8n v1 (5678/tcp) - productie niet breken
    - N8n v2 (5679/tcp) - main UI
    - N8n v2 webhook (5680/tcp)
    - MinIO console (19001/tcp)
    
    NIET publiek: 19000 (S3), 6333 (Qdrant), 5432 (Postgres), etc.
    
    Activeer firewall? (ja/nee)"
    
    Wacht op antwoord.

5.3 Als ja:
    ssh root@178.104.207.194 "ufw default deny incoming && ufw default allow outgoing"
    ssh root@178.104.207.194 "ufw allow 22/tcp comment 'SSH'"
    ssh root@178.104.207.194 "ufw allow 5678/tcp comment 'NOVA v1'"
    ssh root@178.104.207.194 "ufw allow 5679/tcp comment 'NOVA v2 main'"
    ssh root@178.104.207.194 "ufw allow 5680/tcp comment 'NOVA v2 webhook'"
    ssh root@178.104.207.194 "ufw allow 19001/tcp comment 'MinIO console'"
    ssh root@178.104.207.194 "ufw --force enable"
    ssh root@178.104.207.194 "ufw status numbered"
    
    Verify SSH nog werkt: ssh root@178.104.207.194 "echo SSH_STILL_WORKS"
    
    Als faalt: ssh root@178.104.207.194 via rescue mode noodzakelijk.
    BELANGRIJK: Als SSH breekt, is server niet meer bereikbaar!
    Daarom eerst UFW rules configureren, DAN pas enable.

5.4 Test alle services nog bereikbaar:
    - curl -I http://178.104.207.194:5678 (v1)
    - curl -I http://178.104.207.194:5679 (v2)
    - curl -I http://178.104.207.194:5680 (webhook)
    - curl -I http://178.104.207.194:19001 (MinIO)

== TAAK 6: RAPPORTAGE ==

6.1 Schrijf rapport naar L:\!Nova V2\logs\security_fix_YYYY-MM-DD_HH-MM.md:
    
    # NOVA v2 Security Fix Rapport
    
    **Datum**: [timestamp]
    **Duur**: [minuten]
    
    ## SSH Key Setup
    - [x] Key gegenereerd/aanwezig
    - [x] Public key op Hetzner geplaatst
    - [x] Key-based login getest
    
    ## Root Password Rotatie
    - [x] Nieuw password gegenereerd
    - [x] Oud password vervangen op server
    - [x] Nieuw password opgeslagen in secrets file
    - [x] Oud password markered als invalid
    
    ## SSH Daemon Hardening
    - [x] Backup gemaakt van sshd_config
    - [x] PasswordAuthentication no
    - [x] PermitRootLogin prohibit-password
    - [x] SSH reload succesvol
    - [x] Password login geverifieerd disabled
    
    ## Documentatie Update
    - [x] README.md MinIO sectie toegevoegd
    - [x] .env.template comments toegevoegd
    
    ## UFW Firewall
    - [x/n] Status: [enabled/disabled]
    - [indien enabled] Rules applied
    
    ## Status van services na fix
    - V1 (5678): [status]
    - V2 main (5679): [status]
    - V2 webhook (5680): [status]
    - MinIO console (19001): [status]
    
    ## Action items voor jou
    - Lees nieuwe root password uit secrets file (indien nodig voor emergency)
    - SSH key backup maken (id_ed25519 + id_ed25519.pub naar veilige plek)
    - Password authentication is nu uit op server

6.2 Log naar L:\!Nova V2\logs\deploy_log.txt:
    [timestamp] | security | SSH key setup | SUCCESS
    [timestamp] | security | Root password rotated | SUCCESS
    [timestamp] | security | SSH hardened | SUCCESS
    [timestamp] | security | Docs updated | SUCCESS
    [timestamp] | security | UFW | [SUCCESS/SKIPPED]

6.3 Chat rapport aan mij:
    Compact summary:
    - ✓/✗ per taak
    - Eventuele warnings
    - URLs nog werkend
    - Rapport locatie
    - NIET het nieuwe password tonen in chat (alleen locatie secrets file)

REGELS:
- Secrets nooit in chat
- SSH key werkt voordat password wordt gewijzigd (anders lockout)
- SSH daemon reload (niet restart) om huidige sessie intact te houden
- UFW: eerst regels, DAN enable (anders lockout)
- Bij elke risico stap: valideer voordat doorgaan
- Elke fout > 2 retries: stop, escaleer

Ga nu autonoom aan de slag. Vraag alleen bij Taak 5 (UFW) om ja/nee.
```

## Waarschuwingen

**CRITICAL: SSH lockout risico**

Als SSH key setup faalt of config fout is, kan je uitgesloten raken van server. De prompt heeft safeguards maar:

Als het misgaat:
- Hetzner heeft web-based "Rescue System" (boot in recovery mode)
- Zie Hetzner Cloud dashboard → jouw server → "Rescue"
- Login via web terminal, fix SSH config, reboot normaal

## Wat Cursor autonoom doet

- SSH key genereren als nog niet bestaat
- Key uploaden naar Hetzner
- Key-login testen
- Root password roteren
- Secrets file updaten
- SSH daemon hardening
- Docs bijwerken

## Waar Cursor pauzeert voor jou

- Taak 5 UFW activeren: ja/nee vraag

## Geschatte tijd

10-15 minuten totaal.

## Alternatief: stapsgewijs

Als je niet wilt dat alles autonoom gaat, splits in 3 aparte prompts:

**Prompt A: Alleen SSH key + password rotate**
(Taken 1-2)

**Prompt B: Alleen SSH hardening**  
(Taak 3)

**Prompt C: Alleen docs + UFW**
(Taken 4-5)

Geef elk apart aan Cursor, met pauze ertussen om te verifiëren.

## Rollback scenario

Als iets fout gaat:

```bash
# Via Hetzner Rescue Console
# Restore SSH config
cp /etc/ssh/sshd_config.backup_YYYYMMDD /etc/ssh/sshd_config
systemctl reload sshd

# Of reset root password
passwd
# Type nieuw password 2x
```

Secrets file lokaal heeft nog oude en nieuwe credentials voor emergency.
