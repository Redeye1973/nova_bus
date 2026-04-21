# Tailscale Setup voor NOVA v2

Tailscale is cruciaal voor secure PC ↔ Hetzner communicatie. Hetzner agents bellen jouw PC voor Ollama inferenties via private tailnet.

## Waarom Tailscale

Alternatieven beoordeeld:
- **Cloudflare tunnel**: WAS optie, maar strategisch niet gekozen (pull model)
- **Port forwarding + dyndns**: security risico, thuis-router exposure
- **VPN (WireGuard/OpenVPN)**: werkt, maar complexer setup
- **Tailscale**: gekozen - mesh netwerk, zero-config, gratis voor personal

Voordelen Tailscale:
- End-to-end encrypted
- Geen port forwarding nodig
- Private IPs automatisch
- Works through NAT/firewall
- Free tier voldoende (tot 100 devices)

## Setup PC (jouw workstation)

### Stap 1: Tailscale installeren

Download van https://tailscale.com/download/windows

Installer:
- Run `.exe`
- Inloggen met email account
- Auto-start bij boot inschakelen

Verificatie:
```powershell
# Check tailscale draait
Get-Service | Where-Object { $_.Name -like "*tailscale*" }

# Check IP
tailscale ip -4
# Verwacht: 100.x.x.x IP address
```

### Stap 2: Ollama bereikbaar maken

Default Ollama luistert alleen op 127.0.0.1. Moet op alle interfaces:

```powershell
# Set environment variable
[System.Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'User')

# Restart Ollama
Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
ollama serve

# In nieuwe terminal: verify
curl http://localhost:11434/api/tags
curl http://$(tailscale ip -4):11434/api/tags
```

### Stap 3: Firewall rule (als nodig)

Windows Defender Firewall kan blokkeren:

```powershell
# Allow Ollama op tailscale interface
New-NetFirewallRule -DisplayName "Ollama Tailscale" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 11434 `
    -Action Allow `
    -Profile Private

# Verify
Get-NetFirewallRule -DisplayName "Ollama Tailscale"
```

## Setup Hetzner server

### Stap 1: Tailscale installeren

```bash
# SSH in
ssh root@178.104.207.194

# Install
curl -fsSL https://tailscale.com/install.sh | sh

# Enable as service
systemctl enable --now tailscaled

# Auth
tailscale up
# Volg URL die verschijnt, authenticeer in browser met zelfde account
```

### Stap 2: Verify connectie

```bash
# Op Hetzner
tailscale status
# Verwacht: jouw PC in lijst

# Check of je PC kunt bereiken
ping -c 3 <jouw-pc-tailnet-ip>

# Test Ollama vanaf Hetzner
curl http://<jouw-pc-tailnet-ip>:11434/api/tags
```

## Configuratie in NOVA v2

### Agent containers Ollama calls

Agent containers moeten Ollama URL kennen. Via environment variable:

```yaml
# docker-compose.yml op Hetzner
services:
  agent-02-code-jury:
    environment:
      - OLLAMA_URL=http://<jouw-pc-tailnet-ip>:11434
    # extra_hosts niet meer nodig als tailscale werkt
```

### Update .env op Hetzner

```bash
# SSH in
ssh root@178.104.207.194

# Edit .env
nano /docker/nova-v2/.env

# Voeg toe:
PC_TAILSCALE_IP=100.x.x.x  # Jouw echte tailnet IP
OLLAMA_URL=http://${PC_TAILSCALE_IP}:11434
```

### Test chain

```bash
# Vanaf Hetzner: curl Ollama via tailscale
docker compose exec agent-02-code-jury curl -s http://${PC_TAILSCALE_IP}:11434/api/tags
```

Verwacht: JSON met jouw Ollama modellen lijst.

## Ollama modellen setup

Voor NOVA v2 agents hebben we specifieke modellen nodig:

```powershell
# Op jouw PC, na RTX 5060 Ti installed
ollama pull qwen2.5-coder:9b       # Code generation + review (Code Jury)
ollama pull nemotron-mini:4b        # Quick decisions (veel agents)
ollama pull llama3.2-vision:11b     # Image analysis (Sprite Jury, Storyboard)
ollama pull nomic-embed-text        # Embeddings voor Qdrant

# Verify
ollama list
```

Voor zwakkere hardware (voor RTX 5060 Ti):
```powershell
ollama pull llama3.2:3b              # Lightweight
ollama pull codestral:22b-q4         # Quantized
```

## Troubleshooting

### PC niet zichtbaar vanaf Hetzner

```bash
# Check Tailscale status
tailscale status

# Als PC offline:
# Op PC: open Tailscale, check verbinding
# Op PC: Log-in opnieuw als nodig

# Als PC wel online maar niet reachable:
# Check firewall op PC
# Check OLLAMA_HOST env var
```

### Slow Ollama responses

```bash
# Check tailscale ping times
tailscale ping <jouw-pc-tailnet-ip>
# Verwacht: <100ms

# Als hoog: check direct vs relay
# Direct: PC en Hetzner verbonden via DERP relay (langzamer)
# Kan gebeuren als NAT issues
```

### PC-Hetzner direct vs relay

Tailscale probeert direct P2P connection. Als NAT blokkeert: valt terug op DERP relay (extra hop, latency).

Check:
```bash
tailscale status
# Zoek "direct" of "relay" in output
```

Voor P2P direct: mogelijk port forwarding UDP 41641 op thuis-router.

### Security

Tailscale ACL configureren (optioneel):

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["<hetzner-tailnet-ip>"],
      "dst": ["<pc-tailnet-ip>:11434"]
    }
  ]
}
```

Op https://login.tailscale.com/admin/acls

## Alternatief zonder Tailscale

Als Tailscale niet werkt:

**Optie 1**: Ollama op Hetzner zelf (alleen als Hetzner GPU heeft)
- Kost extra: GPU server €184/maand
- Voordeel: geen PC dependency

**Optie 2**: Pull model (originele NOVA v2 design)
- PC poll Hetzner queue
- PC doet Ollama work lokaal
- Returnt resultaten naar Hetzner
- Zie nova_poller.py design in V1 referentie

**Optie 3**: Cloudflare Tunnel (niet aanbevolen)
- Expliciet tegen NOVA v2 regel
- Alleen als laatste redmiddel

## Monitoring

Check periodiek of Tailscale gezond is:

```powershell
# PowerShell script voor daily check
$pcIp = tailscale ip -4
$hetznerReachable = Test-NetConnection -ComputerName "<hetzner-tailnet-ip>" -Port 22 -InformationLevel Quiet
$ollamaAccessible = (Invoke-WebRequest -Uri "http://$pcIp:11434/api/tags" -UseBasicParsing).StatusCode -eq 200

if ($hetznerReachable -and $ollamaAccessible) {
    Write-Host "Tailscale OK"
} else {
    Write-Host "Tailscale ISSUE - check connections"
}
```

Zet in scheduled task voor daily check.

## Kosten

Tailscale Personal plan: **gratis** voor:
- Tot 100 devices
- Unlimited nodes  
- Basic ACLs
- Derp relay service

Geen upgrade nodig voor NOVA v2 gebruik.
