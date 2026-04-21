# Show NOVA Bridge status

$bridgeRoot = Split-Path -Parent $PSScriptRoot
$script = Join-Path $bridgeRoot "scripts\bridge_watcher.py"

python $script --status
