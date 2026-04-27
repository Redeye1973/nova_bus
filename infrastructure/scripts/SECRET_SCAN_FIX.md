# Secret Scan Fix Log

## Located hook implementation
- File: `scripts/pre-commit-secret-scan.sh`
- Blocking regex line: `password\s*[:=]\s*[^\s#]{8,}`
- First observed location: line 13
- Hook loader: `.git/hooks/pre-commit` (same script content)

## Root cause
The password regex matched both hardcoded secrets and legitimate env references like:
`POSTGRES_PASSWORD=${NOVA_REF_DB_PASS}`.

## Fix applied
Because hook uses `grep -E`/`grep -Ei` (no lookahead), implemented two-step filtering:
1. Find broad password candidates.
2. Exclude allowed placeholder/env formats with `grep -vE`:
   - `${VAR}`
   - `<placeholder>`
   - `CHANGEME`
   - `your-*-here` style prefixes

## Validation
Added regression test script:
- `infrastructure/tests/test_secret_scan_regex.sh`

This script asserts allowlisted patterns do NOT match and real hardcoded values DO match.
