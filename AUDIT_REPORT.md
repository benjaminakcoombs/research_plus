# Deep Research Pipeline — Code Audit Report

**Date:** 2026-03-18
**Auditor:** Claude Opus 4.6
**Scope:** All source files in `deep_research/`, prompt templates, CLI, batch scripts, helper scripts, tests
**Method:** Full line-by-line read of every source file (4,436 LOC across 10 Python modules), all prompt templates, shell scripts, and test files. Four parallel audit passes with cross-validation of findings.

---

## Executive Summary

**55 distinct issues identified** across 10 files. The codebase is well-structured with good separation of concerns, but has significant fragility in three areas: (1) resume/checkpoint logic is inconsistent across layers, (2) parsing is regex-heavy with silent failure modes, and (3) the L4 pipeline (newest code) lacks the defensive validation present in L1/L2.

| Severity | Count | Description |
|----------|-------|-------------|
| **P0** | 3 | Will crash or corrupt data |
| **P1** | 12 | Produces wrong results silently |
| **P2** | 22 | Suboptimal but functional |
| **P3** | 18 | Cosmetic/cleanup |

---

## P0 — WILL CRASH OR CORRUPT DATA

### P0-1: Missing Template Files Crash `strategic_briefing` Mode at L3b+

**File:** `deep_research/prompt_builder.py` — lines 186, 203, 238, 272, 298
**Also:** `prompts/strategic_briefing/` directory (confirmed missing files)

**What happens:** When `config.pipeline_mode="strategic_briefing"`, the following methods call `_load_template()` which raises `FileNotFoundError` with no recovery:

- `build_l3b()` → `prompts/strategic_briefing/l3b_refinement.md` ❌ NOT FOUND
- `build_l4a()` → `prompts/strategic_briefing/l4a_report_architect.md` ❌ NOT FOUND
- `build_l4b()` → `prompts/strategic_briefing/l4b_section_writer.md` ❌ NOT FOUND
- `build_l4c()` → `prompts/strategic_briefing/l4c_editorial_review.md` ❌ NOT FOUND
- `build_l4d()` → `prompts/strategic_briefing/l4d_section_revision.md` ❌ NOT FOUND

The `strategic_briefing` directory only contains: `l0_company_profile.md`, `l05_agent_design.md`, `l15_consolidation.md`, `l2_generation.md`, `l3a_synthesis.md`, and `calibration_examples/`.

**What should happen:** Either create these templates, or add a validation gate in `Config.validate()` that checks all required templates exist for the selected pipeline_mode and prevents launching L3b+ in strategic_briefing mode. Since only `situation_assessment` is actively used, the cheapest fix is a guard in the orchestrator's `run_full_pipeline()` that blocks L3b+ for strategic_briefing.

**How to reproduce:**
```python
config = Config(pipeline_mode="strategic_briefing")
pb = PromptBuilder(config)
pb.build_l3b("Test Corp", run, "some l3a output")
# → FileNotFoundError
```

---

### P0-2: Negative Token Budget Silently Truncates All L2 Content to Empty Strings

**File:** `deep_research/context_manager.py` — lines 116-150

**What happens:** In `assemble_l3_input()`, when L0 + L1.5 outputs exceed `max_context_tokens`:

```
available_for_l2 = max_tokens - l0_tokens - l15_tokens - overhead  # Goes NEGATIVE
base_budget = available_for_l2 / max(total_weight, 1)              # Negative
target_tokens = int(base_budget * weight)                           # Negative
target_chars = target_tokens * 4                                    # Negative (e.g., -39000)
text = text[:target_chars]                                          # Python negative slice → ""
```

With negative `target_chars`, Python's `text[:negative]` slices from the end, returning empty string for any value with magnitude > len(text). Every L2 deep dive gets silently zeroed out. L3a receives L0 + L1.5 but zero L2 research.

**What should happen:** Guard after line 119:
```python
available_for_l2 = max_tokens - l0_tokens - l15_tokens - overhead
if available_for_l2 <= 0:
    logger.error(f"L0+L1.5 ({l0_tokens + l15_tokens} tokens) exceeds context limit ({max_tokens})")
    # Either: truncate L0/L1.5 proportionally, or raise, or return without L2
    available_for_l2 = max(available_for_l2, 2000)  # Minimum budget
```

**How to reproduce:** Run on a company with very verbose L0/L1.5 outputs totaling >150K tokens (the default `max_context_tokens`). L3a synthesis receives no L2 deep dives.

---

### P0-3: Thinking Blocks Appended as Raw API Objects Break Multi-Round Research

**File:** `deep_research/research_runner.py` — lines 248-260

**What happens:** In `run_research()`, when building message history for round 2+:

```python
slim_content = []
for block in response.content:
    block_type = getattr(block, "type", None)
    if block_type == "thinking":
        slim_content.append(block)          # ← Raw Pydantic/API object
    elif block_type == "text":
        slim_content.append({"type": "text", "text": block.text})  # ← Plain dict
```

The `messages.append({"role": "assistant", "content": slim_content})` creates a list mixing raw API response objects with plain dicts. When sent to the API in round 2+, the SDK may fail to serialize the mixed types, or the API may reject the malformed content blocks.

**What should happen:**
```python
if block_type == "thinking":
    slim_content.append({"type": "thinking", "thinking": block.thinking})
```

**How to reproduce:** Run any multi-round research task (all L1 and L2 agents use 3 rounds by default) with extended thinking enabled. Round 2 API call receives mixed object types in assistant message content.

**NOTE:** This may currently "work" if the Anthropic SDK serializes thinking blocks transparently, but it's relying on undocumented SDK behavior and will break on SDK updates. Needs verification — if the SDK handles it, downgrade to P1.

---

## P1 — PRODUCES WRONG RESULTS SILENTLY

### P1-1: L4b Resume Skips Failed Tasks Instead of Retrying Them

**File:** `deep_research/orchestrator.py` — lines 772-773

**What happens:** L4b uses length-based resume:
```python
start_from = len(run.l4b_outputs)
remaining = list(enumerate(zip(prompts, names, run.l4b_task_models)))[start_from:]
```

Unlike L1/L2 (lines 185-191) which filter out `[ERROR...]` outputs and re-run them, L4b treats all outputs equally. If 3 of 5 tasks completed and 1 had an error, `len(l4b_outputs) == 4` (3 good + 1 error). Resume starts from task 5, permanently skipping the errored task.

**What should happen:** Apply the same error-filtering pattern used in L1/L2:
```python
good_outputs = [o for o in run.l4b_outputs if not o.raw_output.startswith("[ERROR")]
errored_count = len(run.l4b_outputs) - len(good_outputs)
run.l4b_outputs.clear()
run.l4b_outputs.extend(good_outputs)
start_from = len(good_outputs)
```

**How to reproduce:** Run L4b with 5 tasks. Task 3 fails with an API error (gets `[ERROR: ...]` output). Interrupt. Resume. Task 3's error is counted as "done" — it's never retried.

---

### P1-2: L4d Resume Has Same Skip-Failed-Tasks Bug

**File:** `deep_research/orchestrator.py` — lines 905-911

**What happens:** Identical to P1-1 but for L4d revisions. Same length-based resume with no error filtering.

---

### P1-3: L4d Section Assembly May Produce Out-of-Order Report on Resume

**File:** `deep_research/orchestrator.py` — lines 988-994

**What happens:**
```python
final_sections = []
for output in run.l4d_outputs:
    if not output.raw_output.startswith("[ERROR"):
        final_sections.append(output.raw_output)
run.l4_final_report = "\n\n---\n\n".join(final_sections)
```

Sections are assembled in the order they appear in `run.l4d_outputs`. With parallel execution under `asyncio.gather()`, outputs are appended as tasks complete (line 976). If task 3 finishes before task 1, the report has Section III before Section I. On a normal run this is fine (tasks usually complete roughly in order), but on resume where some tasks are pre-completed and others are re-run, order can be scrambled.

**What should happen:** Sort by original task index before assembly:
```python
for i, output in sorted(enumerate(run.l4d_outputs), key=lambda x: x[0]):
```
Or better: store section index in AgentOutput metadata and sort by it.

---

### P1-4: L4d Section Notes List Length Mismatch Silently Drops Revisions

**File:** `deep_research/orchestrator.py` — lines 906-911

**What happens:** If `l4c_section_notes` has M items and `l4b_outputs` has N items where 0 < M < N, the `zip()` at line 906 silently truncates to M items. The last N-M sections are never revised and don't appear in the final report.

```python
sections_to_revise = list(enumerate(zip(
    run.l4b_outputs,
    run.l4b_task_names,
    run.l4b_task_sections,
    run.l4c_section_notes if run.l4c_section_notes else [""] * len(run.l4b_outputs),
)))[start_from:]
```

**What should happen:** Pad section_notes to match:
```python
notes = run.l4c_section_notes or []
notes += [""] * (len(run.l4b_outputs) - len(notes))
```

---

### P1-5: Missing Haiku Pricing — Quality Checks Billed at 4-6x Actual Cost

**File:** `deep_research/config.py` — lines 11-24, 125

**What happens:** Quality checking uses `claude-haiku-4-5-20251001` (in `quality_checker.py`), but the `PRICING` table has no Haiku entry. The fallback at line 125:
```python
pricing = PRICING.get(model, PRICING["claude-sonnet-4-6"])
```
Bills Haiku calls at Sonnet rates ($3/$15 per MTok vs Haiku's ~$0.80/$4 per MTok). Cost estimates for quality checks are inflated ~4-6x. This distorts budget tracking — the pipeline may hit `warn_cost_usd` or `max_total_cost_usd` earlier than it should.

**What should happen:** Add Haiku to PRICING:
```python
"claude-haiku-4-5-20251001": {"input_per_1k": 0.0008, "output_per_1k": 0.004},
```

---

### P1-6: Partial API Failure in Multi-Round Research Silently Returns Truncated Results

**File:** `deep_research/research_runner.py` — lines 213-217

**What happens:**
```python
except anthropic.APIError as e:
    logger.error(f"  [{task_id}] API error in round {round_num + 1}: {e}")
    if round_num > 0 and all_text:
        break   # ← Silent truncation on round 2+
    raise       # ← Only raises on round 1
```

If round 2 or 3 fails, the code silently returns round 1's output without any indication that the research was truncated. The caller (orchestrator) treats this as a complete 3-round result. The agent gets credited with full research when it actually only did 1 round.

**What should happen:** Either always raise, or return a flag/metadata indicating partial completion so the orchestrator can decide whether to retry or accept.

---

### P1-7: Gap-Fill Agents Added to L1 Outputs Create Cost Tracking Inconsistency

**File:** `deep_research/orchestrator.py` — lines 407-452

**What happens:** Gap-fill agents are appended to `run.l1_outputs` (line 452), making them indistinguishable from original L1 agents. On resume, the error-filtering logic at lines 185-191 processes gap-fill agents alongside L1 agents. If a gap-fill agent errored, it gets cleared and "re-run" — but the re-run uses L1 prompts, not gap-fill prompts. Additionally, gap-fill costs are tracked separately in `gap_costs_all` but then merged into `run.cost_records` (line 454), making it impossible to distinguish gap-fill costs from L1 costs post-hoc.

**What should happen:** Keep gap-fill outputs in a separate list (`run.gap_fill_outputs`) that isn't touched by L1 resume logic. Only merge them into the L1.5 input assembly, not into `run.l1_outputs`.

---

### P1-8: Semantic Quality Score Averages Over Incomplete Dimensions

**File:** `deep_research/quality_checker.py` — lines 244-268, 328-350

**What happens:** The semantic quality check prompts Haiku to return 5 dimension scores (SPECIFICITY, NOVELTY, SOURCE_QUALITY, ACTIONABILITY, ANOMALY_VALUE). If Haiku only returns 4, the average is computed as `sum(scores.values()) / len(scores)` — averaging over 4, not 5. A missing low score inflates the average, causing bad outputs to pass quality checks.

**What should happen:** Validate all 5 dimensions were parsed. Treat missing dimensions as score 1 (worst):
```python
expected = {"SPECIFICITY", "NOVELTY", "SOURCE_QUALITY", "ACTIONABILITY", "ANOMALY_VALUE"}
for dim in expected - set(scores.keys()):
    scores[dim] = 1  # Penalize missing evaluations
```

---

### P1-9: CLI Resume Allows Backward Layer Progression

**File:** `deep_research/__main__.py` — lines 314-321, ~366

**What happens:** `--resume run_abc123 --stop-after l0` loads a run that's already at L1+, then attempts to run it "backward" to L0. The `next_layer()` check happens later but the run is already being processed.

**What should happen:** After loading the run, validate that `stop_after` >= `run.next_layer()`. Error immediately if backward.

---

### P1-10: `rerun_failed.py` Doesn't Check If Run Reached L1

**File:** `rerun_failed.py` — lines 35-50

**What happens:** If called on a run that's still at L0 or L0.5, `run.l1_outputs` is empty. The script prints "No failed agents to re-run!" as if everything is fine, when in reality L1 was never attempted.

**What should happen:** Check `run.status` to confirm L1 was at least attempted before declaring success.

---

### P1-11: `rerun_failed.py` Index Mismatch Between Prompts and Outputs

**File:** `rerun_failed.py` — lines 56-58

**What happens:** Accesses `run.l1_prompts[idx]` and `run.l1_prompt_names[idx]` using indices from `run.l1_outputs`. If these lists are out of sync (crash during L0.5 prompt generation, manual editing), this throws an unhandled `IndexError`.

**What should happen:** Bounds check before access.

---

### P1-12: No Validation of L4b Input List Lengths Before zip()

**File:** `deep_research/orchestrator.py` — lines 735 (approx)

**What happens:** L4b zips `prompts`, `names`, and `run.l4b_task_models` without checking they're the same length. If L4a parsing extracted 5 tasks but only 3 model assignments, `zip()` silently truncates to 3 tasks. Two sections are never written.

**What should happen:** Explicit length validation:
```python
lengths = [len(run.l4b_task_names), len(run.l4b_task_briefs), len(run.l4b_task_models)]
if len(set(lengths)) > 1:
    raise ValueError(f"L4b lists have inconsistent lengths: {lengths}")
```

---

## P2 — SUBOPTIMAL BUT FUNCTIONAL

### P2-1: L4d Revisions Always Use Sonnet, Ignoring L4a Model Choice

**File:** `deep_research/orchestrator.py` — lines 940-944

L4b respects `run.l4b_task_models` (Opus or Sonnet per L4a), but L4d passes `model=None` (defaults to Sonnet) for all revisions. If L4a specified Opus for "Executive Summary" because it needs higher reasoning quality, the revision downgrades to Sonnet.

---

### P2-2: Preamble Stripping Can Match Real Content

**File:** `deep_research/research_runner.py` — lines 97-107

Pattern at line 107: `r"^(?:Three |Two |The |These |This )(?:critical|key|important|remaining).*?\n\n"` matches legitimate output starting with "Three critical factors affecting..." — stripping the heading and first paragraph.

**Fix:** Only apply preamble patterns to the first ~200 chars, or add a guard: if >50% of content would be stripped, skip.

---

### P2-3: Fuzzy Source Matching in L4b Context Assembly Returns Wrong Agent

**File:** `deep_research/context_manager.py` — lines 261-272

Substring matching `if name_lower in key or key in name_lower` can match the wrong agent when names overlap (e.g., "Analysis" matches both "Carbon Credit Analysis" and "Market Analysis").

---

### P2-4: L4c Editorial Memo Parsing Failure Silently Masked

**File:** `deep_research/orchestrator.py` — lines 875-877

If `_parse_l4c_editorial_memo()` returns empty section_notes, the ternary at line 910 treats `[]` as falsy and substitutes empty strings. No warning is logged that parsing failed.

---

### P2-5: Fuzzy Section Name Matching Fails on Similar Task Names

**File:** `deep_research/orchestrator.py` — lines 1199-1217

First 30 chars of task name used for matching. Tasks like "Market Opportunity — Revenue" and "Market Opportunity — Margins" both match the same section notes.

---

### P2-6: Empty Tension Points Not Filtered Before L2

**File:** `deep_research/orchestrator.py` — lines 1752-1828

Parser creates TensionPoint objects with all-empty fields if L1.5 output has headers but no content. These get formatted and sent to L2, wasting tokens researching nothing.

---

### P2-7: L4a Task Brief Can Be Empty

**File:** `deep_research/orchestrator.py` — lines 1098-1106

If L4a output has `BRIEF:` followed immediately by `SOURCE DOCUMENTS:`, the parsed brief is "". L4b section writer receives an empty brief.

---

### P2-8: Budget Uses Estimated Cost, Not Actual

**File:** `deep_research/research_runner.py` — lines 40-49; `config.py` — lines 122-131

Budget check uses `self.total_cost` which aggregates estimated costs from `estimate_cost()`. These use static per-search estimates ($0.01) and tiktoken token counts (~14% underestimate per the comment at config.py line 63). Over a full run, actual API charges could exceed the $150 hard stop by 10-15%.

---

### P2-9: L4a Task Boundary Detection Fragile to Content Containing "DELIVERABLE"

**File:** `deep_research/orchestrator.py` — lines 1063-1077

For the last task block, the end boundary is found by searching for "DELIVERABLE 3" or "ASSEMBLY NOTES". If the task brief contains the text "DELIVERABLE 3", the block gets truncated prematurely.

---

### P2-10: Costs Lost on Exception in L4b/L1/L2

**File:** `deep_research/orchestrator.py` — lines 809-819 (L4b), 151-160 (L1/L2)

When an exception occurs mid-API-call, the runner may have already incurred costs. The exception handler sets `agent_costs = []`, losing those costs from tracking.

---

### P2-11: No Placeholder Validation in Prompt Builder

**File:** `deep_research/prompt_builder.py` — all `build_*` methods

If a template contains `{UNDEFINED_VAR}` that isn't substituted, it's sent to the API as literal text. No warning, no error.

---

### P2-12: Calibration File Fallback Returns Empty String

**File:** `deep_research/prompt_builder.py` — lines 94-95

If both archetype-specific and default calibration files are missing, returns "". L1.5 synthesis loses all calibration guidance.

---

### P2-13: `--dry-run` Not in Mutually Exclusive Group with `--stop-after`

**File:** `deep_research/__main__.py` — lines 68-78, 355-365

`--stop-after l2 --dry-run` is accepted but contradictory. `--dry-run` silently overrides to stop after L0.5.

---

### P2-14: Batch Script Uses Unsafe Variable Expansion in Python Subprocess

**File:** `run_batch.sh` — lines 152-166

`'$state_file'` inside double-quoted Python string expands unsafely. Paths with spaces or quotes break the subprocess.

---

### P2-15: Batch Script Doesn't Track or Report Failed Runs

**File:** `run_batch.sh` — lines 118-132, 217

Failed companies are silently skipped. No summary of failures at end. Exit code 0 even if all runs fail.

---

### P2-16: `add_contrarian_l2.py` Doesn't Restore State on Parse Failure

**File:** `add_contrarian_l2.py` — lines 184-189

If prompt parsing fails, early return happens without saving. If prompts were partially added to lists before the parse call, state is inconsistent.

---

### P2-17: Missing `l4d_complete` Status Convention

**File:** `deep_research/models.py` — lines 214-241

All layers use `"<layer>_complete"` pattern except L4d, which uses `"complete"`. Inconsistent naming makes status logic harder to reason about.

---

### P2-18: Unescaped Dots in Quality Check Regex

**File:** `deep_research/quality_checker.py` — line 154

`r"NEAR.TERM"` matches any character between NEAR and TERM, not just space/hyphen.

---

### P2-19: `re` Module Imported Inside Function (Per-Call Overhead)

**File:** `deep_research/research_runner.py` — line 96

`import re` inside `_extract_text()` runs on every API response.

---

### P2-20: Retry Attempts Not Tracked in Cost Records

**File:** `deep_research/research_runner.py` — lines 140-160

If a request is retried 3 times before succeeding, only the successful attempt's cost is recorded. Failed attempts that incurred API charges are invisible.

---

### P2-21: L0.5 Code Block Matching Vulnerable to Duplicates

**File:** `deep_research/orchestrator.py` — lines 1643-1648

`find()` always locates the first occurrence of identical code blocks, so multiple agents could receive the same prompt.

---

### P2-22: Pipeline Mode Not Persisted/Used on Resume

**File:** `deep_research/prompt_builder.py` — lines 23-57, 75-96

On resume, prompt builder uses `config.pipeline_mode` (from current CLI invocation), not `run.pipeline_mode` (from original run). If modes differ, different calibration examples and templates are used mid-run.

---

## P3 — COSMETIC/CLEANUP (18 issues, summarized)

| ID | File | Issue |
|----|------|-------|
| P3-1 | `orchestrator.py` | Archetype extraction has confusing fallback logic with silent default to OTHER |
| P3-2 | `orchestrator.py` | Cross-section notes filtering uses loose substring matching, likely to miss relevant notes |
| P3-3 | `orchestrator.py` | Resume logging suppressed when errored_count > 0 (lines 201-202) |
| P3-4 | `orchestrator.py` | Missing section_reference in L4b AgentOutput metadata |
| P3-5 | `orchestrator.py` | Inconsistent null/empty return values across parsing methods |
| P3-6 | `orchestrator.py` | L4a style guide extraction log says "using full output" but returns "" |
| P3-7 | `orchestrator.py` | L2 prompt parsing has redundant fallback that produces same result |
| P3-8 | `research_runner.py` | Unused import: `SEARCH_COST_ESTIMATE` (line 13) |
| P3-9 | `research_runner.py` | Fragile model detection via `"opus" in model` string matching |
| P3-10 | `config.py` | Stale model entry `claude-sonnet-4-5-20250929` |
| P3-11 | `quality_checker.py` | "Pokee" in attribution detection regex (line 385) — likely test artifact |
| P3-12 | `quality_checker.py` | Inconsistent quality thresholds (60% for L0/L2, 50% for others) undocumented |
| P3-13 | `quality_checker.py` | Task ID truncated to 20 chars, potential collision on similar agent names |
| P3-14 | `context_manager.py` | ERROR outputs silently skipped in L1 manifest (no logging) |
| P3-15 | `context_manager.py` | Token counting fallback `len(text) // 4` undocumented approximation |
| P3-16 | `run_batch.sh` | No validation of empty COMPANIES array before iteration |
| P3-17 | `tests/test_parsing.py` | No CLI argument edge case tests (backward resume, conflicting flags) |
| P3-18 | `tests/test_parsing.py` | No parsing edge case tests (0 agents, missing fields, typos in verdicts) |

---

## Recommendations — Prioritized Fix Order

### Phase 1: Critical Path (fix before next production run)

1. **P0-2** — Add bounds check for negative token budget in `context_manager.py`
2. **P0-3** — Convert thinking blocks to dicts in `research_runner.py`
3. **P1-1 + P1-2** — Apply L1/L2 error-filtering resume pattern to L4b and L4d
4. **P1-4** — Pad section_notes list to match l4b_outputs length
5. **P1-12** — Validate all L4b input lists have equal length

### Phase 2: Accuracy (fix before trusting cost/quality metrics)

6. **P1-5** — Add Haiku pricing to PRICING table
7. **P1-6** — Surface partial-round failures instead of silently truncating
8. **P1-8** — Validate all 5 semantic quality dimensions are present
9. **P2-8** — Add safety margin to budget checking (multiply estimates by 1.15)

### Phase 3: Robustness (fix to harden resume/CLI)

10. **P0-1** — Block strategic_briefing mode at L3b+ (or create templates)
11. **P1-3** — Sort L4d sections by task index before final assembly
12. **P1-9** — Validate stop_after >= next_layer on resume
13. **P1-7** — Separate gap-fill outputs from L1 outputs
14. **P2-13** — Add --dry-run to mutually exclusive CLI group

### Phase 4: Polish (batch when convenient)

15. All P2 parsing robustness issues (P2-2, P2-3, P2-5, P2-7, P2-9)
16. All P2 helper script issues (P2-14, P2-15, P2-16)
17. All P3 issues

---

## Appendix: Files Audited

| File | Lines | Issues Found |
|------|-------|-------------|
| `deep_research/orchestrator.py` | 1,893 | 25 |
| `deep_research/research_runner.py` | 411 | 8 |
| `deep_research/config.py` | 131 | 3 |
| `deep_research/models.py` | 373 | 1 |
| `deep_research/prompt_builder.py` | 308 | 4 |
| `deep_research/quality_checker.py` | 428 | 4 |
| `deep_research/context_manager.py` | 287 | 4 |
| `deep_research/__main__.py` | 467 | 3 |
| `run_batch.sh` | ~220 | 3 |
| `rerun_failed.py` / `add_contrarian_l2.py` | ~200 | 3 |
| `tests/test_parsing.py` | ~300 | 2 |
| Prompt templates (6 files) | ~600 | 1 (missing files) |
