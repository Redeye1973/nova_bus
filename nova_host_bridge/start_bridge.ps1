param(
    [string]$BindHost = "0.0.0.0",
    [int]$Port = 8500,
    [string]$ConfigPath = "L:\!Nova V2\nova_config.yaml",
    [string]$Token = $null
)

Set-Location -Path $PSScriptRoot

if ($Token) {
    $env:BRIDGE_TOKEN = $Token
}
$env:NOVA_CONFIG_PATH = $ConfigPath

Write-Host "Starting nova_host_bridge on http://${BindHost}:${Port}"
Write-Host "Config: $ConfigPath"
Write-Host "Auth required: $([bool]$env:BRIDGE_TOKEN)"
Write-Host "Tailscale exposure: bind 0.0.0.0 means agents can reach via tailnet IP."

python -m uvicorn main:app --host $BindHost --port $Port
