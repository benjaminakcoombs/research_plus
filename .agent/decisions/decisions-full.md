# Decisions — Full Detail

<!-- Active decisions with rationale. Load when making or reviewing decisions. -->

## D-001 — Product name = "Deep Analysis" (2026-03-16)

**Context:** Previously called "Super Research" and "Pokee Deep Research." Neither conveyed the right positioning — "Super Research" is generic and "Pokee Deep Research" leads with the brand before the user understands value.
**Decision:** Rename to "Deep Analysis." It signals depth + interpretation (not just research retrieval).
**Status:** Active

## D-002 — Two pipeline modes: strategic_briefing and situation_assessment (2026-03-16)

**Context:** The pipeline originally had a single output mode that tried to serve both executive/consulting readers and banking/deal readers. These audiences have fundamentally different needs.
**Decision:** Split into two modes with distinct prompt chains, calibration examples, and output formats:
- `strategic_briefing` — reader = CEO/COO, focus on strategic implications
- `situation_assessment` — reader = boutique IB MD, focus on deal-relevant angles
**Status:** Active

## D-003 — L3 split into L3a (synthesis) + L3b (refinement) (2026-03-16)

**Context:** Single-pass L3 synthesis was producing outputs that read like research summaries, not polished analyst documents. Quality ceiling was too low.
**Decision:** Two-agent L3 approach:
- L3a: synthesis draft from research corpus
- L3b: editor/refinement pass reading as target audience (7-task checklist)
**Status:** Active

## D-004 — Deep Analysis doc format: 2,500-3,500 words, top 3 findings, hold back rest (2026-03-16)

**Context:** Early outputs were too long and tried to cover everything, diluting impact.
**Decision:** Constrain to 2,500-3,500 words. Lead with top 3 findings only. Hold back buyer universe and remaining findings as teasers for follow-up engagement.
**Status:** Active

## D-005 — Pokee positioning: soft sell in "About This Analysis" section (2026-03-16)

**Context:** Hard-selling Pokee in the document undermines credibility. The document itself IS the proof of value.
**Decision:** Show-don't-tell via document quality. Pokee mention only in a brief "About This Analysis" section at the end.
**Status:** Active

## D-006 — Folder reorg: prompts/ split by mode, design docs to docs/ (2026-03-16)

**Context:** 4 copies of prompt chains were scattered across the repo root and archive directories. Confusing which was active.
**Decision:** Consolidate into clean structure: `prompts/strategic_briefing/` and `prompts/situation_assessment/`. Move design docs to `docs/`. Remove `prompts_archive/` and root-level duplicate `.md` files.
**Status:** Active

## D-007 — L3c is programmatic (ReportLab), not LLM-based (2026-03-18)

**Context:** PDF generation could be an LLM step (have the model generate styled output) or a programmatic step (template + render).
**Decision:** L3c uses ReportLab for zero API cost, <1s execution. Deterministic, reproducible output.
**Status:** Active

## D-008 — --run-all default endpoint moved from l3b → l3c (2026-03-18)

**Context:** After adding L3c PDF generation, `--run-all` still stopped at L3b, meaning PDFs weren't generated on full runs unless explicitly requested.
**Decision:** Move default endpoint to l3c so PDFs are always generated on full runs. L3c is non-blocking — if reportlab missing or generation fails, layer still completes (l3c_pdf_path = None).
**Status:** Active
