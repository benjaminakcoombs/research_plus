# Session Log

## 2026-03-18 — L3c: Automated PDF generation step

### What was done
1. **Added L3c layer** — programmatic (no LLM call) step after L3b that converts the refined markdown to a styled PDF using ReportLab, matching the Pokee AI Deep Analysis house style (cover page, TOC, section headers, tables, footnotes, Pokee branding).
2. **Created `deep_research/pdf_generator.py`** — generalized the standalone `generate_pdf.py` script into a proper module with `build_pdf()` and `build_pdf_from_run()` entry points. Accepts company_name and date_label overrides.
3. **Updated `models.py`** — added `l3c` to `LAYER_ORDER`, `LAYER_DISPLAY_NAMES`, status mappings (`l3c_complete`), and `l3c_pdf_path` field on `ResearchRun`. Added backward-compat handling.
4. **Updated `orchestrator.py`** — added `run_l3c()` method (calls `build_pdf_from_run`, no API cost) and wired it into the `run_to` dispatch table.
5. **Updated `__main__.py`** — `--run-all` default stop now `l3c` (was `l3b`), added L3c to `show_run` display, print_summary shows PDF path when available.
6. **Updated `report_generator.py`** — `generate_reports()` now prefers the ReportLab styled generator over pandoc, with fallback to pandoc if reportlab is not installed.
7. **Verified** — functional test against existing Fervo Energy L3 markdown produces 28KB PDF matching original output.

### Files touched
- `deep_research/pdf_generator.py` (new)
- `deep_research/models.py`
- `deep_research/orchestrator.py`
- `deep_research/__main__.py`
- `deep_research/report_generator.py`

### Decisions made
- D-006: L3c is programmatic (ReportLab), not LLM-based — zero API cost, runs in <1s
- D-007: L3c is non-blocking — if reportlab missing or generation fails, layer still completes (l3c_pdf_path = None)
- D-008: `--run-all` default endpoint moved from l3b → l3c so PDFs are always generated on full runs

### Next session priorities
1. Write `l3b_refinement.md` for `strategic_briefing` mode (P0 — will error without it)
2. Fix calibration example data leakage (Acadia in healthcare_services.md)
3. Audit `strategic_briefing` L3a prompt — may need rewrite to match new quality bar
4. Update `.agent/config.md` to reflect new folder structure
5. Consider deprecating root-level `generate_pdf.py` now that `deep_research/pdf_generator.py` exists

---

## 2026-03-16 — Major refactor: folder reorg, L3 rewrite, L3a/L3b split

### What was done
1. **Reviewed Acadia SA output** — identified 8 issues (weak hook, generic buyer universe, CTA problems, factual nits).
2. **Reorganized prompt folder structure** — consolidated 4 copies of prompt chains into 2 clean modes:
   - `prompts/strategic_briefing/` (exec/consulting, reader = CEO/COO)
   - `prompts/situation_assessment/` (banking/deal, reader = boutique IB MD)
   - Moved design docs to `docs/`
   - Removed `prompts_archive/` and root-level duplicate `.md` files
3. **Renamed product** — "Super Research" → "Deep Analysis"
4. **Rewrote L3 situation_assessment prompt** — complete rewrite of `l3a_synthesis.md` with exact document structure (Cover Page → Opportunity → Company Situation → 3 Key Findings → Deal Context → About).
5. **Split L3 into L3a + L3b** — two-agent approach:
   - L3a: synthesis draft from research corpus
   - L3b: editor/refinement pass reading as target audience
   - Updated all code: `prompt_builder.py`, `models.py`, `orchestrator.py`, `__main__.py`, `config.py`, `quality_checker.py`, `report_generator.py`
6. **Fixed `strategic_advice` → `strategic_briefing`** — renamed across all Python files.
7. **Wrote `l3b_refinement.md` for situation_assessment** — 7-task refinement checklist (pressure-test hook, cut known facts, strengthen evidence, verify deal context, check About section, strip internal refs, final read-through).
8. **Fixed bug** — `build_l3b` used `template` instead of `prompt` on second replacement, losing `{COMPANY_NAME}` substitution.

### Files touched
- `prompts/situation_assessment/l3a_synthesis.md` (renamed + rewritten)
- `prompts/situation_assessment/l3b_refinement.md` (new)
- `prompts/strategic_briefing/l3a_synthesis.md` (renamed)
- `deep_research/prompt_builder.py`
- `deep_research/models.py`
- `deep_research/orchestrator.py`
- `deep_research/__main__.py`
- `deep_research/config.py`
- `deep_research/quality_checker.py`
- `deep_research/report_generator.py`
- `README.md`
- `docs/CONTEXT.md`, `docs/SITUATION_ASSESSMENT_OVERVIEW.md`, `docs/orchestration_spec.md` (moved)

### Decisions made
- D-001: Product name = "Deep Analysis"
- D-002: Two modes: `strategic_briefing` and `situation_assessment`
- D-003: L3 split into L3a (synthesis) + L3b (refinement) for quality
- D-004: Deep Analysis format: 2,500-3,500 words, top 3 findings only, hold back buyer universe + remaining findings as teasers
- D-005: Soft-sell Pokee in "About This Analysis" section (show don't tell)

### Next session priorities
1. Write `l3b_refinement.md` for `strategic_briefing` mode (P0 — will error without it)
2. Fix calibration example data leakage (Acadia in healthcare_services.md)
3. Audit `strategic_briefing` L3a prompt — may need rewrite to match new quality bar
4. Update `.agent/config.md` to reflect new folder structure
