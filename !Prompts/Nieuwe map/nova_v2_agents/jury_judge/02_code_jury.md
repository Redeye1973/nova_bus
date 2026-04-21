# 02. Code Jury Agent

## Doel
Evalueert AI-gegenereerde code voor kwaliteit, veiligheid en integratie. Uitbreiding van bestaande UE5 debugger naar volwaardig jury-judge systeem.

## Scope
- GDScript (Godot projecten: Black Ledger, TyrianKloon, NORA)
- Python (NOVA pipeline scripts, agents, utilities)
- C++ (UE5 specifieke code)
- N8n workflow JSON validatie

## Jury Leden

**1. Syntax Validator**
- Tool: Language-specific parsers (ast voor Python, godot --check voor GDScript)
- Checkt: compileert/parseert, geen syntax errors
- Output: pass/fail met error locations

**2. API Existence Checker**
- Tool: Python + API documentation cache
- Checkt: alle aangeroepen methods/classes bestaan in target framework
- Gebruikt: godot_api_cache.json (3000+ classes), Python stdlib + installed packages
- Detecteert hallucinated APIs (veel voorkomend probleem bij AI code)

**3. Logic Flow Detector**
- Tool: Ollama Codestral 22B
- Checkt: logische coherentie, edge cases, exception handling
- Prompt: geeft code blok, vraagt waar bugs zouden kunnen zitten

**4. Regression Detector**
- Tool: Git diff + Ollama
- Checkt: breekt deze change bestaande werkende code?
- Vergelijkt tegen laatste working commit

**5. Security Scanner**
- Tool: semgrep + Ollama
- Checkt: SQL injection, XSS, path traversal, insecure defaults, hardcoded secrets
- Belangrijk voor NOVA productie code

**6. Performance Detector**
- Tool: Ollama + pattern matching
- Checkt: obvious O(n²) in hot paths, memory leaks patterns, blocking IO in async contexts

**7. Style Conformance**
- Tool: black/ruff voor Python, gdformat voor GDScript
- Checkt: project conventions matched

## Judge

**Code Judge**
- Tool: Ollama Qwen 2.5 72B
- Input: alle jury scores, diff context, project impact
- Output verdict:
  - **merge**: alle groen, veilig te committen
  - **review**: menselijke check aanbevolen voor merge
  - **revise**: terugsturen naar Cursor voor fix met specifieke feedback
  - **reject**: fundamentele problemen, opnieuw beginnen

## N8n Workflow Structuur

```
Trigger: Webhook of Git post-commit hook
    ↓
Set: parse code change details
    ↓
Parallel jury calls:
    ├─ HTTP → syntax_validator
    ├─ HTTP → api_checker
    ├─ HTTP → logic_flow (Ollama)
    ├─ HTTP → regression (git diff + Ollama)
    ├─ HTTP → security (semgrep)
    ├─ HTTP → performance (Ollama)
    └─ HTTP → style (linters)
    ↓
Merge + aggregate
    ↓
HTTP → code_judge
    ↓
Switch verdict:
    ├─ merge → git merge + PostgreSQL log
    ├─ review → Telegram notify + PR creation
    ├─ revise → Cursor prompt generation → apply fix → re-test
    └─ reject → Log + revert commit
    ↓
Notification
```

## Cursor Prompt

```
Bouw een NOVA v2 Code Jury systeem dat bestaande code-output van AI (Cursor, Claude Code) valideert:

1. Python service `code_jury/syntax_validator.py`:
   - FastAPI POST /validate
   - Input: {language: "gdscript|python|cpp", code: string, file_path: string}
   - Output: {valid: bool, errors: [{line, column, message}]}
   - Python: gebruik ast.parse
   - GDScript: gebruik godot --check-only via subprocess
   - C++: gebruik clang-format --dry-run + optional clang-tidy

2. Python service `code_jury/api_checker.py`:
   - FastAPI POST /check
   - Input: code + language
   - Output: {exists: [...], missing: [{name, line}], suggestions: [...]}
   - Voor GDScript: laad godot_api_cache.json (generate via godot --doc-tool)
   - Voor Python: dynamic import attempt + stdlib check
   - Detecteer calls naar niet-bestaande APIs

3. Python service `code_jury/logic_flow.py`:
   - FastAPI POST /analyze
   - Input: code + context
   - Output: {score: 0-10, issues: [{severity, description, line}]}
   - Roept Ollama Codestral aan met structured prompt
   - Prompt vraagt: unreachable code, edge cases, null checks, type issues

4. Python service `code_jury/regression_detector.py`:
   - FastAPI POST /regression
   - Input: {old_code, new_code, test_command?}
   - Output: {breaks_behavior: bool, confidence: 0-1, affected_functions: []}
   - Git diff analyseren
   - Ollama vraagt: breaks deze change iets?
   - Optioneel: run test suite en compare

5. Python service `code_jury/security_scanner.py`:
   - FastAPI POST /scan
   - Input: code + language
   - Output: {score: 0-10, vulnerabilities: [...]}
   - Run semgrep met standard rulesets
   - Plus Ollama check op secrets patterns

6. Python service `code_jury/code_judge.py`:
   - FastAPI POST /verdict
   - Input: alle jury outputs
   - Output: {verdict, reasoning, fix_suggestions: []}
   - Logic:
     - Syntax invalid → reject direct
     - API missing → revise met specifieke missing items
     - Security critical → reject
     - Logic issues high severity → revise
     - Alle groen → merge
     - Mixed → review

7. N8n workflow `code_jury_workflow.json`:
   - Git webhook trigger (via GitHub/Gitea webhook)
   - Of handmatig via POST /code-review
   - Parallel jury calls
   - Judge
   - Verdict routing
   - Bij "revise": genereer Cursor prompt met specifieke feedback
   - Bij "merge": trigger git actions
   - Metrics naar PostgreSQL

8. Cursor feedback integration script `cursor_feedback.py`:
   - Neemt judge "revise" verdict
   - Genereert gestructureerde prompt voor Cursor
   - Bijvoorbeeld: "Fix de volgende issues in [file]: 1) [issue1 op regel X]..."
   - Schrijft naar .cursor/prompts/ voor quick access

Gebruik Python 3.11, FastAPI, async httpx, pydantic v2.
Test met samples uit L:\Nova\SpaceShooter\scripts (bestaande Black Ledger code).
```

## Integratie met Bestaande UE5 Debugger

De huidige UE5 debugger in L:\Nova\agents\ue5_debugger wordt jury member #1 (syntax validator specifiek voor Unreal Python). Zijn error detection patterns migreren naar de nieuwe Syntax Validator met Unreal-specific rules.

## Test Scenario's

1. **AI genereert GDScript met hallucinated API**: api_checker flagged, judge: revise met correcte API suggestie
2. **AI genereert code met SQL injection**: security_scanner red, judge: reject
3. **AI fix breekt bestaande test**: regression_detector flagged, judge: revise
4. **AI genereert clean refactor**: alle jury groen, judge: merge

## Success Metrics

- 95%+ detectie rate op bewuste kapotte test cases
- < 10% false positive rate
- Gemiddelde jury tijd < 60 seconden per file
- Judge accuracy vs human review > 85%

## Koppeling met Cursor Workflow

Wanneer Cursor code genereert:
1. Cursor commit naar lokale git branch
2. Pre-commit hook triggert code jury via localhost N8n
3. Jury-judge binnen 1-2 minuten
4. Bij revise: Cursor krijgt automatisch nieuwe prompt met feedback
5. Cursor past aan, nieuwe commit, nieuwe jury run
6. Max 3 iteraties, dan escaleer naar human

Dit vervangt de huidige ad-hoc "Claude fixt, we hopen dat het werkt" met structured validation.
