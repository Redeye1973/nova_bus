#!/bin/bash
# Pre-commit hook: blocks commits containing likely secrets.
# Install: cp scripts/pre-commit-secret-scan.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

PATTERNS=(
    'sk-[a-zA-Z0-9]{20,}'
    'pk-[a-zA-Z0-9]{20,}'
    'AKIA[A-Z0-9]{16}'
    'ghp_[a-zA-Z0-9]{36}'
    'gho_[a-zA-Z0-9]{36}'
    'glpat-[a-zA-Z0-9\-]{20,}'
    'xox[bpas]-[a-zA-Z0-9\-]+'
    'password\s*[:=]\s*[^\s#]{8,}'
    'PRIVATE KEY-----'
)

PASSWORD_ALLOWLIST='password\s*[:=]\s*(\$\{|<|CHANGEME|your-)'

STAGED=$(git diff --cached --name-only --diff-filter=ACM)
[ -z "$STAGED" ] && exit 0

FOUND=0
for file in $STAGED; do
    # skip binary files and known safe patterns
    [[ "$file" == *.png ]] && continue
    [[ "$file" == *.jpg ]] && continue
    [[ "$file" == *.gif ]] && continue
    [[ "$file" == *.mp4 ]] && continue
    [[ "$file" == *vault_mapping.yaml ]] && continue
    [[ "$file" == "scripts/pre-commit-secret-scan.sh" ]] && continue
    [[ "$file" == "infrastructure/tests/test_secret_scan_regex.ps1" ]] && continue
    [[ "$file" == "infrastructure/tests/test_secret_scan_regex.sh" ]] && continue

    content=$(git show ":$file" 2>/dev/null) || continue

    for pattern in "${PATTERNS[@]}"; do
        matches=$(echo "$content" | grep -nEi "$pattern" 2>/dev/null)

        # Refine password detection to avoid false positives on env refs/placeholders.
        if [[ "$pattern" == *"password"* ]] && [ -n "$matches" ]; then
            matches=$(echo "$matches" | grep -viE "$PASSWORD_ALLOWLIST" 2>/dev/null)
        fi

        if [ -n "$matches" ]; then
            echo "BLOCKED: potential secret in $file"
            echo "  pattern: $pattern"
            echo "$matches" | head -3 | sed 's/^/  /'
            echo ""
            FOUND=$((FOUND + 1))
        fi
    done
done

if [ $FOUND -gt 0 ]; then
    echo "============================================"
    echo "COMMIT BLOCKED: $FOUND potential secret(s) found"
    echo "If these are false positives, commit with:"
    echo "  git commit --trailer "Made-with: Cursor" --no-verify"
    echo "============================================"
    exit 1
fi
exit 0
