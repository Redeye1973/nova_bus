---
title: DR Runbook — Secret Leaked in Git
severity: critical
expected_time: 30-60 min
---

# Secret Leaked in Git History

## Detectie
- Pre-commit hook false negative
- GitHub secret scanning alert
- Handmatige ontdekking in git log

## Stappen

1. **Identificeer het secret**
   ```bash
   git log --all -p | grep -i "password\|token\|secret\|api_key" | head -20
   ```

2. **Roteer het secret EERST**
   - Genereer nieuw wachtwoord/token
   - Update in Vault (Agent 44)
   - Update in .env op server
   - Restart betrokken services

3. **Verwijder uit git history**
   ```bash
   # BFG Repo-Cleaner (sneller dan filter-branch)
   # Download: https://rtyley.github.io/bfg-repo-cleaner/
   
   # Maak secrets file
   echo "OLD_SECRET_VALUE" > secrets.txt
   
   # Clean
   java -jar bfg.jar --replace-text secrets.txt nova_bus.git
   cd nova_bus.git
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   git push --force
   ```

4. **Als GitHub token gelekt**
   - Revoke op github.com/settings/tokens
   - Genereer nieuw token
   - Update in Vault + server

## Preventie
- Pre-commit hook scant op patterns (al actief)
- Nooit secrets in code, altijd via Vault
- .env in .gitignore
