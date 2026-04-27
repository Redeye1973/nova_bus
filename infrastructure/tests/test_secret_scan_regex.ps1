$ErrorActionPreference = 'Stop'

$pattern = 'password\s*[:=]\s*[^\s#]{8,}'
$allow = 'password\s*[:=]\s*(\$\{|<|CHANGEME|your-)'

function Should-Flag([string]$line) {
    if ($line -notmatch $pattern) { return $false }
    if ($line -match $allow) { return $false }
    return $true
}

$passCases = @(
  'POSTGRES_PASSWORD=${NOVA_REF_DB_PASS}',
  'password: ${DB_PASS}',
  'POSTGRES_PASSWORD=<your-password>',
  'password=CHANGEME',
  'password=your-password-here',
  'POSTGRES_PASSWORD=<placeholder>'
)

$failCases = @(
  'password=mySecretPass123',
  'POSTGRES_PASSWORD=hardcoded_value_xyz',
  'password: realPasswordHere',
  'POSTGRES_PASSWORD=p4ssw0rd!verylongstring'
)

foreach ($c in $passCases) {
    if (Should-Flag $c) {
        Write-Error "FAIL should-pass matched: $c"
        exit 1
    }
}

foreach ($c in $failCases) {
    if (-not (Should-Flag $c)) {
        Write-Error "FAIL should-fail not matched: $c"
        exit 1
    }
}

Write-Output 'secret-scan-regex-tests: PASS'
exit 0
