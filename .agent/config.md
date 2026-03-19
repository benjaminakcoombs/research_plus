# Repo Config — Research Banking Boutique

```yaml
schema_version: 0.3.1
template: code-brownfield
created: 2026-02-25
status: active
```

## Repo Loading Protocol

1. **Read this file** (`.agent/config.md`) — repo instructions and conventions.
2. **Read `.agent/session-log.md`** — what happened last session and what to do next.
3. **Read `.agent/index.md`** — file map, architecture summary, key entry points.
4. **Read `.agent/decisions/decisions-key.md`** — quick reference for active decisions.
5. **Determine session type and load accordingly:**

| Session Type | Load | Token Budget |
|-------------|------|-------------|
| Orientation | config + session-log + index + decisions-key | ~8K |
| Bug fix / small change | Above + relevant source files | ~15-25K |
| Feature work | Above + spec/ + relevant source | ~25-40K |
| Pipeline tuning | Above + prompts/ + outputs/ + CONTEXT.md | ~30-40K |
| Research / discovery | Above + discovery/ notes | ~20-30K |

## Overview

Multi-layer AI research pipeline for banking/boutique situation assessments. Layered architecture (L0 → L05 → L15 → L2 → L3) with orchestration, deep research integration, and contrarian analysis. Uses Python with pytest for testing.

## Key Files & Directories

- `deep_research/` — Core pipeline module (orchestrator, models, prompt_builder, pdf_generator, etc.)
- `deep_research/__main__.py` — CLI entry point (`--run-all` defaults to l3c)
- `deep_research/orchestrator.py` — Pipeline orchestration and layer dispatch
- `prompts/situation_assessment/` — Banking/deal mode prompt chain (l0 through l4d + calibration_examples/)
- `prompts/strategic_briefing/` — Exec/consulting mode prompt chain (l0 through l3a + calibration_examples/)
- `docs/CONTEXT.md` — Full project context and architecture description
- `docs/SITUATION_ASSESSMENT_OVERVIEW.md` — Output format and assessment overview
- `docs/orchestration_spec.md` — Pipeline orchestration specification
- `add_contrarian_l2.py` — Contrarian analysis injection at L2
- `rerun_failed.py` — Retry logic for failed pipeline runs
- `outputs/` — Pipeline output artifacts
- `tests/` — Test suite

## Maintenance Rules

### Tier 1: Every session (mandatory)
1. **Update `.agent/session-log.md`** — what was done, files touched, decisions made.
2. **Sync decisions** — if decisions were made, update both key and full.
3. **Update `.agent/index.md`** — if architecture or key files changed.

### Tier 2: When triggered
4. **Prompt changed** → Document rationale in `.agent/decisions/`. Archive old prompt.
5. **Pipeline layer modified** → Update `CONTEXT.md` and orchestration spec if behavior changed.
6. **New archetype added** → Create template, add to index.
7. **Test failures** → Note patterns in `.agent/discovery/`.

## Session Close

Run Tier 1 maintenance. Then follow the global Session Closing Protocol in workspace `.agent/config.md`.
