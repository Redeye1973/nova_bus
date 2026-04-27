param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 5440,
    [string]$DbName = "nova_ref_db",
    [string]$User = "nova_ref"
)

$ErrorActionPreference = "Continue"
$pwd = $env:NOVA_REF_DB_PASS
if (-not $pwd) {
    Write-Output "NOVA_REF_DB_PASS not set; showing query only"
}

$query = "SELECT pid, application_name, state, query_start, query FROM pg_stat_activity WHERE state <> 'idle' ORDER BY query_start;"
Write-Output "Host=$Host Port=$Port Db=$DbName User=$User"
Write-Output "SQL: $query"

if ($pwd) {
    $env:PGPASSWORD = $pwd
    psql -h $Host -p $Port -U $User -d $DbName -c $query
}
