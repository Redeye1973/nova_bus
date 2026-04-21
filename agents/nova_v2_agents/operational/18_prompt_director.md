# 18. Prompt Director Agent

## Doel
Beheert grote, gestructureerde prompts voor Cursor/Claude Code. Splitst complex werk in behapbare blokken en coördineert execution volgorde.

## Scope
- Mega-prompts (zoals Black Ledger PDF prompts A/B/C/D)
- Multi-step development workflows
- Template-based prompt generation
- Prompt versioning en reuse

## Functionaliteit

**1. Prompt Library**
- Herbruikbare templates per domein
- Versioning van prompts
- Performance tracking (welke prompts werkten)

**2. Prompt Composer**
- Templates + context → final prompt
- Variable injection
- Context aware (welk project, welke tech stack)

**3. Execution Orchestrator**
- Dependency graph van prompts (B na A klaar)
- Parallel execution waar mogelijk
- Checkpoint na elke stap

**4. Result Validator**
- Bij terugontvangst code van Cursor: route naar code jury
- Bij success: mark prompt als successful
- Bij fail: revise prompt en retry

**5. Learning Loop**
- Track welke prompt formulations werken
- Feedback naar prompt library
- Suggest improvements

## Cursor Prompt

```
Bouw een NOVA v2 Prompt Director:

1. Python service `prompt_director/library.py`:
   - FastAPI CRUD voor prompts
   - Store in PostgreSQL
   - Fields: name, category, template, variables, version, success_rate
   - Search/filter functionality

2. Python service `prompt_director/composer.py`:
   - Input: {template_name, context: {}}
   - Jinja2 templating voor variable substitution
   - Validate all required vars present
   - Output: final prompt text

3. Python service `prompt_director/orchestrator.py`:
   - Input: {workflow_name, initial_context}
   - Load workflow definition (DAG van prompts)
   - Execute in topological order
   - Handle parallel paths
   - Checkpoint state na elke stap

4. Python service `prompt_director/cursor_dispatcher.py`:
   - Send prompt naar Cursor via filesystem
   - Write prompt naar .cursor/prompts/{id}.md
   - Watch voor response (modified files)
   - Timeout handling
   - Alternative: Claude Code CLI via subprocess

5. Python service `prompt_director/validator.py`:
   - Receive code output
   - Trigger code jury
   - Get verdict
   - Mark prompt run success/fail

6. Python service `prompt_director/learner.py`:
   - Analyze prompt success rates
   - Identify low-performers
   - Suggest template improvements
   - A/B test variations

7. YAML workflow definition format:
```yaml
name: "black_ledger_feature_add"
steps:
  - id: "design"
    template: "gdscript_class_design"
    output: "design_doc"
  - id: "implementation"
    template: "gdscript_class_implementation"
    depends_on: ["design"]
    variables:
      design: "${design_doc}"
  - id: "tests"
    template: "gdscript_tests"
    depends_on: ["implementation"]
    parallel_with: ["integration"]
  - id: "integration"
    template: "gdscript_integration"
    depends_on: ["implementation"]
```

8. CLI tools:
   - `nova-prompt list --category gdscript`
   - `nova-prompt run --workflow <name> --context <json>`
   - `nova-prompt status <run_id>`
   - `nova-prompt stats --template <name>`

9. Web UI voor prompt management:
   - Browse library
   - Edit templates
   - View workflow runs
   - Performance metrics

10. Integration met bestaande PDF mega-prompts:
    - Parse Black Ledger PDF naar individual prompts
    - Import als workflow definition
    - Execute via orchestrator

Gebruik Python 3.11, FastAPI, Jinja2, PostgreSQL, Redis.
```

## Workflow Library (starter set)

**Game Development:**
- New GDScript class (design → implement → test)
- Add feature to Godot project
- Debug specific Godot error
- Refactor GDScript module

**NOVA Pipeline:**
- Add new jury member to domain
- Bake new city workflow
- Migrate data format

**Narrative:**
- Write new chapter (outline → draft → revise)
- Character dialogue generation
- Scene expansion

## Integration Points

- **Triggered by**: Alex, Monitor agent, other agents needing code work
- **Uses**: Cursor (primary), Claude Code CLI (fallback)
- **Feeds into**: Code Jury voor validation
- **Learns from**: Code Jury verdicts

## Test Scenario's

1. Simple single prompt → execute, get code, validate, commit
2. Complex workflow (5 stappen, some parallel) → orchestrate correctly
3. Failed step → retry with improved prompt
4. Learning loop → low-success template improved over time

## Success Metrics

- Prompt success rate (code jury approves): > 70%
- Workflow completion rate: > 85%
- Average prompt iterations to success: < 2
- Template reuse: > 80% of work via library
