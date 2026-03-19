# Index — Research Banking Boutique

<!-- File map, architecture summary, key entry points. Updated each session. -->

## Project Summary

Multi-layer AI research pipeline ("Deep Analysis") for banking/boutique situation assessments and strategic briefings. Two modes: `situation_assessment` (IB MD audience) and `strategic_briefing` (CEO/COO audience). Pipeline: L0 → L0.5 → L1.5 → L2 → L3a → L3b → L3c (PDF). Uses OpenAI/Anthropic APIs with ReportLab for final PDF rendering.

## Architecture

```
L0  (company_profile)    → Company background, financials, market position
L0.5 (agent_design)      → Research agent design with sector-specific calibration
L1.5 (consolidation)     → Consolidate research outputs into structured brief
L2  (generation)         → Generate deal-relevant analysis + contrarian angles
L3a (synthesis)          → Draft full document from research corpus
L3b (refinement)         → Editor pass: pressure-test, cut, strengthen (7-task checklist)
L3c (pdf_generator)      → Programmatic PDF via ReportLab (zero API cost)
```

## File Map

### Core Pipeline (`deep_research/`)
- `__main__.py` — CLI entry point (--run-all defaults to l3c)
- `orchestrator.py` — Pipeline orchestration, layer dispatch
- `models.py` — Data models, layer order, status mappings
- `config.py` — Configuration and paths
- `prompt_builder.py` — Prompt template loading and variable substitution
- `research_runner.py` — API calls to research providers
- `context_manager.py` — Context window management
- `quality_checker.py` — Output quality validation
- `report_generator.py` — Report generation (prefers ReportLab, fallback pandoc)
- `pdf_generator.py` — ReportLab styled PDF generation (L3c)

### Prompts (`prompts/`)
- `situation_assessment/` — Banking/deal mode prompts (l0 through l3b + l4a-l4d + calibration_examples/)
- `strategic_briefing/` — Exec/consulting mode prompts (l0 through l3a + calibration_examples/)

### Docs (`docs/`)
- `CONTEXT.md` — Full project context and architecture
- `SITUATION_ASSESSMENT_OVERVIEW.md` — Output format spec
- `orchestration_spec.md` — Pipeline orchestration specification

### Root-level
- `add_contrarian_l2.py` — Contrarian analysis injection at L2
- `rerun_failed.py` — Retry logic for failed runs
- `generate_pdf.py` — Legacy standalone PDF generator (consider deprecating → D-007)
- `PIPELINE_IMPROVEMENTS_SPEC.md` — Planned improvements
- `AUDIT_REPORT.md` — Code audit results
- `TODO.md` — Active task tracking
- `tests/test_parsing.py` — Parser tests

## Token Budgets

| Session Type | Files to Load | Est. Tokens |
|-------------|--------------|-------------|
| Orientation | config + session-log + index + decisions-key | ~8K |
| Bug fix | Above + target source file(s) | ~15-25K |
| Pipeline tuning | Above + relevant prompts + CONTEXT.md | ~30-40K |
| Feature work | Above + spec + relevant source | ~25-40K |

## Open Items

- `strategic_briefing` mode is missing `l3b_refinement.md` (P0 — will error)
- Calibration example data leakage: Acadia Healthcare in `healthcare_services.md`
- `generate_pdf.py` at root may be redundant with `deep_research/pdf_generator.py`
- `{TARGET_BANK}` not propagating through full prompt chain (OQ-2)
