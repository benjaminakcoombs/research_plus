# Deep Research Pipeline — Comprehensive Improvement Spec

**Date:** March 17, 2026
**Author:** Claude (audit session with Ben)
**Last implementation session:** March 17, 2026
**Scope:** Every bug, config issue, hidden problem, and improvement opportunity identified across the full codebase.

**How to use this document:** Each item has a severity/priority tag. Items marked ALREADY FIXED were patched during one of two sessions. Everything else is ready for implementation by another agent.

---

## IMPLEMENTATION STATUS LEGEND

- ✅ **FIXED** — Implemented and verified
- ⚠️ **DEFERRED** — Intentionally not implemented; reason noted
- 🔍 **NEEDS VERIFICATION** — Probable issue, requires a live run to confirm
- ❓ **NEEDS DECISION** — Blocked on Ben's architectural call
- 📋 **OPEN** — Not yet implemented

---

## TABLE OF CONTENTS

1. ALREADY FIXED (first session)
2. CONFIG CHANGES — immediate, no-code or trivial
3. BUGS — confirmed, will cause incorrect behavior
4. HIDDEN BUGS — probable, need verification
5. STRUCTURAL IMPROVEMENTS — code changes for quality
6. ARCHITECTURE QUESTIONS — need Ben's decision
7. PROMPT TEMPLATE ISSUES
8. MONITORING & OBSERVABILITY
9. QUALITY OF LIFE / DEVELOPER EXPERIENCE
10. ADDITIONAL FINDINGS (from deeper audit)

---

## IMPLEMENTATION SESSION NOTES (March 17, 2026 — second session)

Items implemented, plus two self-introduced bugs found and corrected in the same session:

**Implemented (all verified, tests passing):**
- 2a–2d: All four config changes applied
- 3a: Cost accounting in quality retry path (all attempt costs, not just winner)
- 3b: Resume logic — errored agents re-run on resume (**see correction note below**)
- 3c: Lambda closure in research_runner captures messages by value
- 3d: `rerun_failed.py` accepts run ID as CLI argument
- 3e: `add_contrarian_l2.py` CLI run ID + `build_l3a`/`build_l3b` fix + field names
- 3f: `rerun_failed.py` costs scoping bug
- 4b: Gap-fill agents now run in parallel via `asyncio.gather`
- 7a/10f: `SA_ARCHETYPE_TO_CALIBRATION` — manufacturer/extractor/infrastructure → `energy_technology.md`
- 7b/10a: `{CURRENT_MONTH}`/`{CURRENT_YEAR}` substituted in `build_l3a()`
- 8d: Run summary printed on pipeline completion
- 10h: Per-agent truncation logging in `context_manager.py`

**Self-introduced bugs found and corrected in same session:**

*Bug A — 3b resume logic created duplicates:*
Initial fix set `start_from = first_error_index`, but `run_and_save` appends results to the list — so agents that already succeeded after the first error would be re-run and appended again as duplicates. Corrected fix: strip errored outputs from the list in-place using `output_list_ref.clear() + extend(good_outputs)`, then set `start_from = len(good_outputs)`. This handles mixed success/error states cleanly.

*Bug B — Run summary prefix matching was wrong:*
Layer prefix dict iterated in insertion order, so "l0" matched before "l05" and "l1" before "l15", misattributing L0.5 costs to L0 bucket and L1.5 costs to L1. Corrected fix: changed to an ordered list with longer prefixes first.

---

---

## 1. ALREADY FIXED (this session)

These changes are already committed to the codebase. Documenting for context.

### 1a. L1 research rounds stopped after 1 round
**File:** `research_runner.py`, `run_research()` lines ~205-235
**Root cause:** Continuation logic was gated on `response.stop_reason == "end_turn"`. When the model hit `max_tokens` (which happened on every Bloom L1 agent — output tokens at 16,789 vs 16,000 limit), `stop_reason` was `max_tokens` and the `else: break` terminated the loop after round 1.
**Fix applied:** Removed the `stop_reason` gate. Now always continues to `max_rounds` regardless of stop reason. Added a `max_tokens`-specific continuation prompt. Added safety check for empty content.
**Impact:** This was the single largest contributor to the Bloom quality deficit (~$40 of the $69 cost gap, and the primary reason L1 agents produced shallow single-pass research).

### 1b. Tension point parsing regex didn't match actual output
**File:** `orchestrator.py`, `_parse_tension_points()` lines ~928-945
**Root cause:** Regex `#{1,3}\s*#?(\d+)\.?\s*(.+?)` expected `## #1.` or `## 1.` but actual output uses `## TENSION POINT 1 ★ (TOP 5)` (Bloom) and `### TENSION POINT #1: TITLE` (Acadia). Both formats failed. Fallback captured titles only, with all 6 structured fields empty.
**Fix applied:** Added priority pattern `TENSION\s+POINT\s+#?(\d+)\b[:\s]*(.*)` that handles both formats.
**Verified:** Both Bloom (20 points, all fields populated) and Acadia (20 points, all fields populated) parse correctly.

### 1c. Gap-fill extraction regex missed nested section
**File:** `orchestrator.py`, `_extract_research_gaps()` lines ~496-530
**Root cause:** The regex found "RESEARCH GAPS & CLASSIFICATION CHALLENGE" but terminated at the next `## A) ARCHETYPE CHALLENGE` sub-heading. Actual gap bullets lived under `## B) RESEARCH GAPS`, a nested sub-heading the regex never reached.
**Fix applied:** Three-tier extraction: (1) `## B) RESEARCH GAPS` sub-heading, (2) standalone heading, (3) text-only fallback. Added numbered item extraction alongside bullet extraction.
**Verified:** Bloom extracts 5 gaps. Acadia extracts 5 gaps.

### 1d. No orchestrator-level quality retry for L1/L2 agents
**File:** `orchestrator.py`, `_run_parallel_research_agents()` lines ~163-224
**Root cause:** `max_retries: 2` was defined in config but never used. Quality check logged a warning and kept bad output.
**Fix applied:** Added quality retry loop. Each agent retries up to `max_retries` times on quality failure, keeping the best result.

### 1e. `max_gap_fill_agents` default too low
**File:** `config.py` line 73
**Change:** 1 → 2

### 1f. Cost tracking missing diagnostic fields
**File:** `research_runner.py`, `_record_cost()`
**Change:** Now captures `thinking_tokens` and `stop_reason` from the API response.

---

## 2. CONFIG CHANGES — immediate

### 2a. ✅ FIXED: `research_max_tokens` bumped to 32,000
**File:** `config.py`
**Was:** `research_max_tokens: int = 16000`
**Now:** `research_max_tokens: int = 32000`

**Why this matters:** With extended thinking enabled (`research_thinking_budget: 10000`), the Anthropic API treats `max_tokens` as the TOTAL output budget (thinking + text combined). At 16K total with 10K thinking, the model gets only ~6,000 tokens for text output — roughly 4,500 words. That's not enough for a comprehensive research agent to produce a thorough analysis with sources, anomalies, and structure.

**Evidence:** Every Bloom L1 agent hit 13K-16.8K output tokens. Agents 01, 02, 03 exceeded 16K (16,789; 16,123; 16,117), confirming they were being truncated. This truncation was the proximate cause of `stop_reason: max_tokens` which then triggered the round-continuation bug (1a).

**Cost impact:** Output tokens on Sonnet are $0.015/1K. Extra 16K tokens per agent = ~$0.24/agent/round. Across 8 L1 agents × 3 rounds + 8 L2 agents × 3 rounds = ~$11.50 additional. Well within budget.

**Alternative consideration:** You could also increase `research_thinking_budget` from 10K to 16K. More thinking budget = better search planning. But the text output cap is the binding constraint right now. Recommend: `research_max_tokens: 32000`, `research_thinking_budget: 16000`.

### 2b. ✅ FIXED: `max_concurrent_tasks` bumped to 4
**File:** `config.py`
**Was:** `max_concurrent_tasks: int = 2`
**Now:** `max_concurrent_tasks: int = 4`

**Why:** With 8 L1 agents at concurrency 2, you run 4 sequential batches. At concurrency 4, you run 2 batches — cutting wall-clock time by ~40-50% (from ~2.5h to ~1.5h for a full run). Most Anthropic API tiers support 4+ concurrent streaming requests. If rate-limited, the existing exponential backoff in `_call_with_retry` handles it gracefully.

**Risk:** If on a lower API tier, you may hit rate limits more frequently. The retry logic handles this, but it adds latency. Test with 4 first; dial back to 3 if rate limits are frequent.

### 2c. ✅ FIXED: `max_total_cost_usd` bumped to 150
**File:** `config.py`
**Was:** `max_total_cost_usd: float = 120.0`
**Now:** `max_total_cost_usd: float = 150.0`

**Why:** With the fixes applied (3 rounds per L1, quality retries, gap-fill agents, increased max_tokens), a normal run will cost $65-85. A run with several quality retries could reach $100-110. The $120 hard stop is too close to the expected range — a complex company (lots of SEC filings, international exposure, multi-segment) could legitimately need $110-120 and get killed by the budget check mid-L2. Set to 150 with `warn_cost_usd: 100.0` to give headroom.

### 2d. ✅ FIXED: `warn_cost_usd` bumped to 100
**File:** `config.py`
**Was:** `warn_cost_usd: float = 80.0`
**Now:** `warn_cost_usd: float = 100.0`

### 2e. 📋 OPEN: Pricing table may be stale
**File:** `config.py` lines 11-24
**Action:** Verify current Anthropic pricing for Sonnet 4.6 and Opus 4.6. The table currently has:
- Sonnet: $0.003/1K in, $0.015/1K out
- Opus: $0.015/1K in, $0.075/1K out

If pricing has changed (especially with thinking tokens potentially billed differently), update. Also: the `SEARCH_COST_ESTIMATE = 0.01` per search is a rough guess. Verify against actual billing.

**Note on thinking token pricing:** Anthropic may bill thinking tokens at a different rate than text output tokens. If so, the `estimate_cost` function needs updating:
```python
# Current (may be wrong):
cost = input_tokens * in_rate + output_tokens * out_rate
# Should be:
cost = input_tokens * in_rate + text_tokens * out_rate + thinking_tokens * thinking_rate
```
Check Anthropic's current billing page. If thinking tokens are billed at the same output rate, current code is fine (since `output_tokens` from the API includes thinking). If billed differently, this needs a fix.

---

## 3. BUGS — confirmed

### 3a. ✅ FIXED: Cost accounting bug in quality retry path
**File:** `orchestrator.py`, `_run_parallel_research_agents()` (the code I just wrote)
**Bug:** When an agent fails quality and retries:
1. `_run_single_research` → `runner.run_research()` → `_record_cost()` adds to `runner.total_cost` (CORRECT for budget tracking)
2. On retry, same thing — `runner.total_cost` now reflects ALL attempts
3. But only `best_costs` (the winning attempt) gets added to `run.cost_records`

Result: `runner.total_cost` (used for budget checks) is correct, but `run.cost_records` / `cost_log.json` undercounts if retries happen. The `total_cost_usd` field on the run will be correct (synced from `runner.total_cost`), but the individual cost records won't add up to the total.

**Fix:** Change the retry loop to accumulate ALL costs, not just the best:
```python
all_attempt_costs = []
for attempt in range(max_quality_retries + 1):
    output, agent_costs = await self._run_single_research(...)
    all_attempt_costs.extend(agent_costs)
    # ... quality check, keep best ...

# Save ALL costs, not just best
async with save_lock:
    run.cost_records.extend(all_attempt_costs)
```

### 3b. ✅ FIXED (with correction): Errored agents not re-run on resume
**File:** `orchestrator.py`, `_run_parallel_research_agents()` line ~176
**Bug:** Resume logic uses `start_from = len(existing)` — counts ALL outputs including errored ones (those starting with `[ERROR`). An agent that returned `[ERROR: Research task failed: ...]` is treated as "done" on resume and never retried.

**Fix applied:** Option (a) — strip errored outputs from the list in-place before computing `start_from`. Uses `output_list_ref.clear() + extend(good_outputs)` so duplicates cannot occur on mixed success/error runs. Initial implementation had a duplicate bug (see session notes above) that was caught and corrected in the same session.

**Note on option (b):** True targeted re-run (run only errored indices, slot results back in-place) would be even cleaner, but requires tracking original indices through the async gather. `rerun_failed.py` does this correctly if you need it for ad-hoc reruns.

### 3c. ✅ FIXED: Lambda closure captures `messages` by reference
**File:** `research_runner.py`, `run_research()` line ~175
**Bug:**
```python
response = await self._call_with_retry(
    task_id,
    lambda: self.async_client.messages.stream(
        ...
        messages=messages,  # Captured by reference
    ),
)
```
The `lambda` captures `messages` by reference. If `_call_with_retry` retries the lambda after the messages list has been mutated in the continuation loop (which adds assistant/user turns), it would send incorrect messages. Currently this doesn't happen because retries occur within `_call_with_retry` before the function returns, but it's fragile.

**Fix:** Capture by value:
```python
lambda msgs=list(messages): self.async_client.messages.stream(
    ...
    messages=msgs,
)
```

### 3d. ✅ FIXED: `rerun_failed.py` has hardcoded run ID
**File:** `rerun_failed.py` line 30
**Bug:** `run = ResearchRun.load(config.output_dir, "run_7070d661")` — hardcoded to a specific run.
**Fix:** Accept run ID as CLI argument: `sys.argv[1]` or argparse.

### 3e. ✅ FIXED: `add_contrarian_l2.py` has hardcoded run ID and calls nonexistent method
**File:** `add_contrarian_l2.py` line 29 and line 260
**Bugs:**
- Line 29: `RUN_ID = "run_7070d661"` — hardcoded
- Line 260: `prompt_builder.build_l3(...)` — this method doesn't exist. Should be `build_l3a()` or `build_l3b()`.
- Line 296: Sets `run.l3_executive_briefing` which is not a field on `ResearchRun` (the model has `l3a_draft` and `l3b_final`)
**Fix:** Parameterize run ID, fix method name, fix field names.

### 3f. ✅ FIXED: `rerun_failed.py` line 95 has a bug
**File:** `rerun_failed.py` line 95
**Bug:** `run.cost_records.extend(costs if 'costs' in dir() else [])` — `'costs' in dir()` checks if `costs` is defined in the local scope, which it always is (from the try block). But if the agent failed, `costs` is from the last successful call or undefined. This is a scoping bug — should use the actual costs from this iteration.
**Fix:** Track costs explicitly:
```python
agent_costs = []
try:
    text, agent_costs = await runner.run_research(...)
    ...
except Exception:
    ...
run.cost_records.extend(agent_costs)
```

---

## 4. HIDDEN BUGS — probable, need verification

### 4a. 📋 OPEN: `_extract_text` preamble stripper can eat real content or miss preamble
**File:** `research_runner.py` lines 84-97
**Issue:**
```python
preamble_end = re.search(r"^(#{1,3}\s|---)", text, re.MULTILINE)
if preamble_end and preamble_end.start() < 500:
    text = text[preamble_end.start():]
```
Two failure modes:
- If the model starts its output with a plain paragraph (no heading), preamble isn't stripped → output begins with "Now I have sufficient information to provide a comprehensive..." cruft
- If the model puts a `---` as a decorative element within the first 500 chars, real content gets stripped

**Suggested fix:** More targeted preamble removal:
```python
# Strip known preamble patterns
preamble_patterns = [
    r"^(?:Now I (?:have|can|will)|Based on (?:my|the) research|After (?:reviewing|analyzing)|Let me (?:now |)(?:provide|present|compile)).*?\n\n",
    r"^(?:Here is|Below is|The following is).*?\n\n",
]
for pattern in preamble_patterns:
    text = re.sub(pattern, "", text, count=1, flags=re.DOTALL)
```

### 4b. ✅ FIXED: Gap-fill agents run sequentially, not in parallel
**File:** `orchestrator.py`, `run_l15()` lines ~294-337
**Issue:** Gap-fill agents run in a simple sequential loop with `await asyncio.sleep(cooldown)`, while L1 and L2 agents use `_run_parallel_research_agents` with concurrent execution. With 2 gap-fill agents at 3 rounds each, this adds ~20 minutes of unnecessary wall time.
**Fix:** Use `_run_parallel_research_agents` for gap-fill, or at minimum run them concurrently with `asyncio.gather`.

### 4c. ⚠️ DEFERRED (by design): L3b receives ALL_OUTPUTS twice (via L3a reference + direct inclusion)
**File:** `prompt_builder.py`, `build_l3b()` lines 170-179
**Issue:** The L3b prompt includes both `{L3A_OUTPUT}` (which was synthesized FROM the research) and `{ALL_OUTPUTS}` (the raw research itself). This means L3b's input is:
- Template: ~3K tokens
- L3a draft: ~5K tokens
- L1.5 consolidation: ~16K tokens
- L2 outputs: ~81K tokens
- **Total: ~105K tokens** (for Bloom)

This is within Opus's 200K context window, so it works. But it means Opus is processing 97K tokens of research that L3a already synthesized. The question is whether this redundancy is worth the cost (~$3 per L3b call at current Opus pricing).

**My take:** Keep it. L3b's job is editorial — it needs the raw research to upgrade weak data points in the L3a draft with stronger evidence from the corpus. The L3b prompt template explicitly says "Check the L2 deep dives — there may be a more powerful data point... that the L3a draft didn't surface." This is the right design.

**But monitor:** If L2 outputs grow with the fixes (more rounds, richer content), total L3b input could approach 150-180K tokens. Add a warning log if L3b input exceeds 160K tokens, and consider selective L2 inclusion at that point.

### 4d. 🔍 NEEDS VERIFICATION: `thinking_tokens` may use a different API field name
**File:** `research_runner.py`, the fix I applied: `getattr(response.usage, "thinking_tokens", 0)`
**Issue:** The actual Anthropic API field for thinking tokens in the `usage` object might not be `thinking_tokens`. It could be `thinking_budget_tokens`, `cache_creation_input_tokens`, or something else. If the field name is wrong, `getattr` returns 0 silently and we still don't track thinking tokens.
**Action:** Check the actual `response.usage` object by adding a temporary debug log: `logger.debug(f"Usage fields: {response.usage}")` and running a test call. Update the field name accordingly.

### 4e. 🔍 NEEDS VERIFICATION: Synthesis calls use `adaptive` thinking for Opus — no budget cap
**File:** `research_runner.py` lines 288-295
```python
if "opus" in model:
    thinking_config = {"type": "adaptive"}
```
With adaptive thinking, Opus can use unlimited thinking tokens. On long inputs (L3b with 105K input), this could mean 20-50K thinking tokens per call — adding $1.50-3.75 to each synthesis call. This is probably fine for quality, but it's an unbounded cost that isn't tracked in the cost estimator.
**Action:** Either set a thinking budget for Opus synthesis (e.g., 32K) or ensure the cost estimator accounts for actual thinking token usage.

---

## 5. STRUCTURAL IMPROVEMENTS — code changes for quality

### 5a. 📋 OPEN — HIGH PRIORITY: LLM-based quality checker (Haiku)
**File:** New function in `quality_checker.py`
**Current state:** Quality checks are regex-based:
- `has_specifics` = "does it contain a digit" (`re.search(r'\d+', output)`)
- `has_anomalies` = "does it contain the word 'notable'" (`re.search(r"ANOMAL|NOTABLE", ...)`)
- L2 pass rate threshold is 40% — an agent can fail 3 of 6 checks and pass

This means an L1 agent that produces 1,000 words of vague summarization with a single number and the word "notable" passes quality. The quality retries we added (fix 1d) only trigger on genuinely broken outputs, not mediocre ones.

**Proposed implementation:**
```python
async def check_l1_semantic(self, output: str, agent_name: str, runner: ResearchRunner) -> QualityReport:
    """LLM-based quality check using Haiku for speed and cost."""
    prompt = f"""Rate this research agent output 1-5 on each dimension. Be harsh — a 3 means "acceptable for a first-year analyst," a 5 means "a senior banker would cite this in a client meeting."

AGENT: {agent_name}
OUTPUT (first 3000 chars):
{output[:3000]}

Rate each dimension (1-5) and give a one-sentence justification:

1. SPECIFICITY: Does it contain specific numbers, dates, company names, and dollar amounts — not generalities?
2. NOVELTY: Would a sector specialist learn something they didn't already know?
3. SOURCE QUALITY: Are claims attributed to specific, verifiable sources (SEC filings, state databases, named publications)?
4. ACTIONABILITY: Could a deal team use this in a pitch book or diligence checklist?
5. ANOMALY VALUE: Did it surface surprising contradictions, gaps, or non-obvious patterns?

Output as: DIMENSION: SCORE — JUSTIFICATION
Then: OVERALL: PASS/FAIL (PASS requires average >= 3.0 and no dimension below 2)"""

    text, costs = await runner.run_synthesis(
        prompt, task_id=f"quality_check_{agent_name[:20]}",
        model="claude-haiku-4-5-20251001",
    )
    # Parse scores, compute pass/fail
    ...
```

**Cost:** ~$0.01 per check. With 8 L1 + 8 L2 agents = $0.16 per run. Negligible.
**Impact:** HIGH — transforms quality retries from "retry broken outputs" to "retry mediocre outputs." This is the single highest-leverage improvement for output quality.

### 5b. 📋 OPEN — MEDIUM PRIORITY: Priority-weighted L3 context assembly
**File:** `context_manager.py`, `assemble_l3_input()` lines 36-93
**Current:** When L2 outputs exceed `max_tokens`, they're truncated proportionally — every agent gets equal space.
**Problem:** The tension point about a hidden $2.9B service NPV gets the same context budget as a competitive moat durability analysis. The most deal-relevant findings deserve more space.

**Proposed fix:** Tag L2 outputs with their originating tension point's magnitude. Allocate context budget proportionally:
- Transformational: 2x allocation
- Major: 1.5x allocation
- Moderate: 1x allocation

This requires passing the tension point metadata into `assemble_l3_input`, which means either:
(a) Adding a magnitude field to `AgentOutput`, or
(b) Using the L2 prompt names (which reference tension point titles) to look up magnitude from the parsed tension points

Recommend (a) — cleaner, and the data is available at L2 generation time.

### 5c. 📋 OPEN — MEDIUM PRIORITY: Findings deduplication between L1 agents
**Issue:** Multiple L1 agents often find the same facts from different angles. For example, both the "Buyer Universe" agent and the "Financial Profile" agent might surface the AEP Wyoming deal. L1.5 consolidation catches some of this, but L2 can end up investigating overlapping territory.
**Proposed:** After L1.5 consolidation, before L2 prompt generation, add a Haiku-powered dedup step that identifies overlapping tension points and merges them. This ensures L2 agents investigate genuinely distinct hypotheses.
**Cost:** ~$0.05 (single Haiku call on ~20 tension point summaries).

### 5d. ⚠️ DEFERRED: L0 should always run 2 rounds
**File:** `orchestrator.py`, `run_l0()`
**Current:** L0 calls `runner.run_research()` which runs up to `max_search_rounds` (3) rounds. But the Bloom L0 only ran 1 round (likely due to the same stop_reason bug, now fixed). Acadia ran 2 rounds.
**After fix 1a:** L0 should now reliably run 3 rounds. But consider whether 3 is optimal — the marginal value of round 3 for company profiling may be low. Recommend keeping at 3 (the fix already ensures it runs), but monitor actual round counts in cost logs to see if round 3 adds value.
**Deferred because:** Fix 1a already addresses the root cause. Monitor next run to confirm L0 now runs 3 full rounds.

---

## 6. ARCHITECTURE QUESTIONS — need Ben's decision

All items in this section are ❓ NEEDS DECISION.

### 6a. Should L3 receive L1.5 consolidation, or just L2 outputs?
**Current:** L3a and L3b both receive `ALL_OUTPUTS` = L1.5 + all L2 outputs.
**Question:** L1.5 is ~16K tokens of intermediate synthesis. L2 agents already contain the relevant L1.5 context in their prompts and go deeper. Is the L1.5 inclusion in L3 additive or redundant?

**Arguments for keeping L1.5 in L3:**
- L1.5 contains the full company situation map (Deliverable 1) which L3 uses as the basis for Section II
- L1.5 contains tension points NOT selected for L2 investigation — these inform the "held-back teaser" paragraph
- L1.5 contains the archetype challenge and research gaps, which provide framing

**Arguments for removing L1.5:**
- Saves ~16K tokens of context budget
- L2 outputs already contain richer versions of the same material
- Reduces noise for Opus during L3 synthesis

**My recommendation:** Keep L1.5 but consider a compressed version — just the situation map + tension point titles (without the full field details). This would be ~5K tokens instead of 16K.

### 6b. Should L0.5 (agent design) be passed to L3?
**Current:** L0.5 output is NOT passed to L3 — only L1.5 and L2.
**Question you raised:** Is L0.5 valuable?

**My take:** L0.5 is critical for pipeline quality but not for the final document. It's the "research architect" that designs what L1 agents investigate. Its value is entirely consumed by L1 — by the time we reach L3, the L0.5 design decisions are baked into the L1/L2 outputs. No change needed.

However, L0.5's COVERAGE ASSESSMENT (which agents are most likely to surface high-value insights, what blind spots exist) could be useful for the gap-fill generation step. Currently gap-fill is triggered by L1.5's "research gaps" section, but L0.5's blind spot analysis is available earlier and could seed better gap-fill prompts.

### 6c. Should L0 (company profile) be passed to L3?
**Current:** L0 is NOT passed to L3. L1.5 consolidation subsumes L0.
**My take:** Correct design. L0 is the foundation, but L1.5 is a strictly better version of the same information. No change needed.

### 6d. What's the right number of gap-fill agents?
**Current (after fix):** `max_gap_fill_agents: 2`
**Acadia run:** Had 2 gap-fill agents. Both produced genuinely novel angles (regulated utility analogy, waste management comparison).
**Question:** Would 3 be better? Or is 2 the sweet spot?

**My take:** 2 is right. The gap-fill prompts are generated from L1.5's "research gaps" section, which typically identifies 3-5 gaps. But the gaps vary in quality — usually 2 are genuinely high-value and the rest are incremental. Running 3 gap-fill agents risks the third being low-marginal-value at ~$7-8 cost. Keep at 2 but allow the Opus gap-fill generator to select the 2 most valuable.

### 6e. Should the contrarian L2 mechanism (`add_contrarian_l2.py`) be integrated into the main pipeline?
**Current:** It's a standalone script that adds lateral/creative L2 agents after the main run.
**My take:** Yes, integrate it. The contrarian angles are often the most valuable part of the output. They should be part of every run, not an afterthought. Implementation: after the standard L2 agents complete, generate 2-3 contrarian prompts using the existing `CONTRARIAN_GENERATION_PROMPT` template, run them in parallel with the same quality retry logic, and include their outputs in L3 input.

This would add ~$15-20 to each run but significantly improve the "how did they know that?" hit rate.

---

## 7. PROMPT TEMPLATE ISSUES

### 7a. ✅ FIXED: Calibration example selection is broken for most archetypes
**File:** `prompt_builder.py` lines 32-47 (`SA_ARCHETYPE_TO_CALIBRATION`)
**Issue:** 10 of 13 archetypes map to `business_services.md` as a fallback. Only 3 have specific calibration files:
- `healthcare_pharma` → `healthcare_services.md`
- `saas_software` → `application_software.md`
- `platform_marketplace` → `application_software.md`

The Bloom run (archetype: `manufacturer`) used `business_services.md` despite `energy_technology.md` existing in the calibration directory. The energy_technology calibration file contains Plug Power examples that are directly relevant to energy/manufacturing companies.

**Fix:** Add mappings:
```python
CompanyArchetype.MANUFACTURER: "energy_technology.md",
CompanyArchetype.INFRASTRUCTURE_UTILITIES: "energy_technology.md",
CompanyArchetype.EXTRACTOR_GROWER: "energy_technology.md",
```

**Partial fix applied:** MANUFACTURER, EXTRACTOR_GROWER, INFRASTRUCTURE_UTILITIES now map to `energy_technology.md`. Remaining archetypes still default to `business_services.md`.

**Broader fix still open:** Create calibration examples for the remaining unmapped archetypes. Each calibration file is ~4-6K tokens of high-quality tension point examples. The investment is 30 minutes per archetype to write good examples, and they're reused on every run. Priority order:
1. `financial_services.md` (banks, insurance, asset managers)
2. `real_estate.md` (REITs, developers, property managers)
3. `conglomerate.md` (diversified holding companies)
4. `media_entertainment.md` (studios, streaming, gaming)

### 7b. ✅ FIXED: L3a template has a stale `{CURRENT_MONTH} {CURRENT_YEAR}` placeholder
**File:** `prompts/situation_assessment/l3a_synthesis.md` line 28
**Issue:** The template includes `{CURRENT_MONTH} {CURRENT_YEAR}` in the cover page, but `prompt_builder.py` doesn't substitute these variables. They appear as literal text in the output.
**Fix:** Add substitution in `build_l3a()`:
```python
from datetime import datetime
now = datetime.now()
prompt = prompt.replace("{CURRENT_MONTH}", now.strftime("%B"))
prompt = prompt.replace("{CURRENT_YEAR}", str(now.year))
```

### 7c. ⚠️ NOT A BUG (by design): L3b template says "exactly 3 findings" but L3a generates from all tension points
**Not a bug — by design.** L3a produces a comprehensive draft with material from all tension points. L3b curates to the top 3. This filtering step is intentional and well-documented in the L3b template. Documenting here to prevent a future "fix" that breaks it.

### 7d. ⚠️ DEFERRED (monitoring): L1.5 consolidation prompt asks for 15-20 tension points — often gets 20
**File:** `prompts/situation_assessment/l15_consolidation.md` line 23
**Issue:** The prompt says "Identify 15-20 tension points." Both Bloom and Acadia produced exactly 20. This is fine, but the subsequent L2 generation step can only create 6-8 prompts from 20 tension points. The remaining 12-14 tension points are lost — they don't appear in the final document except in the "held-back teaser" paragraph.
**Consider:** Should L1.5 produce fewer, higher-quality tension points (8-12)? Or is 20 the right number because it gives L2 generation more to choose from? I lean toward keeping 20 — the selection pressure at L2 generation forces prioritization, and the held-back teasers create curiosity.

### 7e. 📋 OPEN — HIGH PRIORITY: L2 generation prompt doesn't receive structured tension points

**Agent recommendation: do this next.** The spec buries this in section 7 but it's arguably the highest-leverage remaining quality improvement — reducing Opus's L2 prompt design input from 30K tokens of narrative prose to ~5K tokens of structured data. The `TensionPoint` objects with all fields populated are sitting in `run.tension_points` right now after fix 1b. A 20-line change to `build_l2_generation()` + `run_l2()` to format those into a compact digest would make Opus's prompts meaningfully sharper.
**File:** `orchestrator.py`, `run_l2()` line 384
```python
tp_text = self._extract_tension_points_text(run.l15_output)
```
This passes the raw L1.5 text from "DELIVERABLE 2" onward — a wall of narrative prose. The L2 generator (Opus) has to read through ~30K tokens of unstructured text to find the tension points.

**Alternative:** Pass the structured tension point data we now parse correctly. Build a compact summary:
```
TENSION POINT 1 [DILIGENCE FLAG, Transformational, High confidence]:
Title: SK ecoplant relationship risk
Observation: SK ecoplant represented ~55% of Q3 2025 revenue while selling equity...
L2 Research Question: Obtain full PDA text, identify change-of-control provisions...
---
TENSION POINT 2 [DEAL TIMING SIGNAL, Transformational, High confidence]:
...
```
This would be ~5K tokens instead of ~30K, giving Opus a cleaner input for prompt design.

---

## 8. MONITORING & OBSERVABILITY

### 8a. 📋 OPEN: Add per-layer timing to cost_log.json
**Current:** Cost records have timestamps but no explicit layer-level timing.
**Proposed:** Add `layer_start_time` and `layer_elapsed_seconds` to each cost record, and a summary entry at the end:
```json
{"type": "layer_summary", "layer": "l1", "elapsed_seconds": 1200, "total_cost": 25.50, "agents_run": 8, "quality_retries": 2}
```

### 8b. 📋 OPEN: Add quality check results to cost_log.json
**Current:** Quality reports are stored in `run_state.json` but not in the cost log. When reviewing runs, you have to cross-reference two files.
**Proposed:** Add quality check pass/fail and pass_rate to each agent's cost record.

### 8c. ✅ ALREADY DONE (fix 1f): Log the actual `stop_reason` for every API call
**Status:** The fix in 1f adds stop_reason to cost records. But the log message only shows it if non-empty. Make it always visible:
```
[l1_agent_01_r1] Cost: $1.59 | Tokens: 404K/16K | think: 10K | Searches: 12 | stop: end_turn | Total: $3.44
```
This makes it immediately visible in logs when agents are being truncated (`stop: max_tokens`).

### 8d. ✅ FIXED: Add a run summary at completion
**Proposed:** When a run completes, print a structured summary:
```
=== RUN COMPLETE: run_0dc78fbd (Bloom Energy) ===
Total cost: $72.43 | Elapsed: 1h 47m
L0:   $2.50 (2 rounds, 19 searches)
L1:   $28.30 (8 agents × 3 rounds, 2 quality retries, 190 searches)
Gap:  $12.40 (2 agents × 3 rounds, 44 searches)
L1.5: $5.80 (2 passes)
L2:   $18.50 (8 agents × 2.5 avg rounds, 1 quality retry, 96 searches)
L3:   $4.93 (L3a + L3b)
Tension points parsed: 20 (all fields populated)
Research gaps found: 5
Quality: L0 90% | L1 avg 80% | L1.5 80% | L2 avg 67% | L3 80%
```

### 8e. 📋 OPEN: Add a `--dry-run` mode
**File:** `__main__.py`
**Proposed:** Run L0 and L0.5 only, then print:
```
DRY RUN: Bloom Energy
  L0 cost: $2.50
  Agent design: 8 L1 agents planned
  Estimated L1 cost: $24-35 (8 agents × 3 rounds × $1-1.5/round)
  Estimated gap-fill: $10-15 (2 agents × 3 rounds)
  Estimated L2 cost: $18-25 (8 agents × 3 rounds × $0.75-1.0/round)
  Estimated L3 cost: $5-8
  TOTAL ESTIMATE: $60-86
  Budget: $150 (headroom: $64-90)
  Proceed? [Y/n]
```
This gives cost visibility before committing to the expensive L1+ phases.

---

## 9. QUALITY OF LIFE / DEVELOPER EXPERIENCE

### 9a. 📋 OPEN: The `tests/test_parsing.py` file exists but was never checked
**Action:** Verify it covers the tension point parsing, gap extraction, and agent prompt parsing. After the regex fixes, existing tests may be broken. Update them.
**Status note:** The 5 existing tests pass, but they were not examined to confirm they actually test the parsing logic changed in fixes 1b and 1c. The parsing changes are regex-based and fragile — test coverage here is important before the next run.

### 9b. 📋 OPEN: Add integration test that runs a cheap company through L0 + L0.5
**Proposed:** A test that runs a small, well-known public company (e.g., "Chipotle Mexican Grill") through L0 and L0.5 only, verifying:
- L0 quality check passes
- L0.5 generates 6-8 parseable agent prompts
- Archetype is correctly detected
- Cost is under $5
This catches regression in prompt templates, parsing logic, and API integration.

### 9c. ⚠️ PARTIALLY DONE: `rerun_failed.py` and `add_contrarian_l2.py` should be CLI subcommands
**Current:** Both scripts now accept run ID as CLI argument (fixed in 3d/3e). Full integration into `__main__.py` as subcommands still open.
**Proposed:** Add to `__main__.py`:
```bash
python -m deep_research --rerun-failed run_abc123
python -m deep_research --add-contrarian run_abc123 --count 3
```

### 9d. 📋 OPEN: Add `--company-ticker` flag for better L0 targeting
**Current:** L0 searches by company name only. For companies with common names (e.g., "Bloom Energy" vs "Bloom"), the web search may return irrelevant results.
**Proposed:** Add `--ticker` flag that gets included in the L0 prompt: "The company trades as NYSE: BE" — this dramatically improves search precision.

### 9e. 📋 OPEN: Save the actual prompts sent to the API, not just the template outputs
**Issue:** `run_state.json` saves the prompts as they were generated by L0.5 and L2 generation. But it doesn't save the actual multi-turn messages sent in rounds 2-3 (which include the model's own prior output + the continuation prompt). For debugging, you'd want to see exactly what the API received.
**Proposed:** Add a `--save-messages` flag that dumps the full message history for each agent to a debug directory. Off by default (the messages are huge — 400K+ tokens each).

---

## 10. ADDITIONAL FINDINGS (from deeper audit)

### 10a. ✅ FIXED (same as 7b): `{CURRENT_MONTH}` and `{CURRENT_YEAR}` are never substituted in L3a
**File:** `prompt_builder.py`, `build_l3a()` lines 157-168
**Evidence:** The Bloom L3b output says "January 2026" instead of "March 2026" — Opus guessed the date from context (the AEP deal it led with was from January). The L3a template has `{CURRENT_MONTH} {CURRENT_YEAR}` on the cover page, but `build_l3a()` only substitutes `{COMPANY_NAME}`, `{N_L1_AGENTS}`, `{N_TENSION_POINTS}`, `{N_L2_AGENTS}`, `{ALL_OUTPUTS}`.
**Fix:**
```python
from datetime import datetime
now = datetime.now()
prompt = prompt.replace("{CURRENT_MONTH}", now.strftime("%B"))
prompt = prompt.replace("{CURRENT_YEAR}", str(now.year))
```

### 10b. 📋 OPEN: Acadia used single-pass L3; Bloom used L3a+L3b — schema divergence
**Finding:** The Acadia run (run_3b5161c2) has `l3_executive_briefing` and `l3_full_report` fields, used a single `l3_synthesis` task ($3.32). The Bloom run has `l3a_draft` and `l3b_final` fields, used `l3a_synthesis` + `l3b_refinement` ($6.15 total). The current `ResearchRun` model defines `l3a_draft` and `l3b_final` but NOT `l3_executive_briefing` or `l3_full_report`.
**Implication:** Old runs can still be loaded (Pydantic ignores extra fields by default), but the code can't access the old field names programmatically. If you ever need to compare or reprocess old runs, this is a problem.
**Fix:** Either add the old fields as aliases, or create a migration script that renames fields in old `run_state.json` files.

### 10c. 📋 OPEN (minor): `build_l3b` does a no-op `{COMPANY_NAME}` substitution
**File:** `prompt_builder.py` line 177
**Issue:** The L3b template doesn't contain `{COMPANY_NAME}` — confirmed by scanning. The `prompt.replace("{COMPANY_NAME}", company_name)` call is a no-op. Not a bug (no-ops are harmless), but misleading.
**Action:** Minor — either add `{COMPANY_NAME}` to the L3b template where appropriate, or remove the substitution from `build_l3b()`.

### 10d. 📋 OPEN — CLIENT-FACING: The Bloom cover page is missing "DEEP ANALYSIS" header and "Confidential" marker
**Evidence:** L3a template specifies the cover should start with "DEEP ANALYSIS" and include "Confidential". The actual Bloom output starts with `---\nContents:\n...`. The model dropped the header.
**Root cause:** The L3a template puts the cover page in a code block (triple backticks), signaling to the model that it's a template. But Opus sometimes interprets code blocks as "reproduce this literally" and sometimes as "use this as a guide." The cover page reproduction is inconsistent.
**Fix:** Move the cover page out of a code block in the L3a template — make it regular markdown with explicit instructions like "Start your output with exactly this text:" followed by the cover content in a quoted block.

### 10e. ⚠️ NOT A BUG: L3a template has `{N_L1_AGENTS}` and `{N_L2_AGENTS}` used in two places each
**Observation:** These appear in both the template header (line 7-9, context description) and in the About section template (line 160). Both are correctly substituted by `build_l3a()`. No bug — just noting for completeness.

### 10f. ✅ FIXED (same as 7a): SA calibration mapping doesn't use `energy_technology.md` for any archetype
**File:** `prompt_builder.py` lines 32-47
**Issue:** `energy_technology.md` exists in the calibration directory (created March 17, same day as Bloom run) but is never selected by `SA_ARCHETYPE_TO_CALIBRATION`. The Bloom run (archetype: `manufacturer`) got `business_services.md` instead.
**Evidence:** The `energy_technology.md` file contains 7 high-quality Plug Power tension point examples — directly relevant for energy/industrial companies. The `business_services.md` file contains generic business services examples.
**Impact:** The L1.5 consolidation prompt received business services calibration examples instead of energy technology examples, likely reducing the quality of tension point generation for the Bloom run.
**Fix:** Add to `SA_ARCHETYPE_TO_CALIBRATION`:
```python
CompanyArchetype.MANUFACTURER: "energy_technology.md",
CompanyArchetype.INFRASTRUCTURE_UTILITIES: "energy_technology.md",
CompanyArchetype.EXTRACTOR_GROWER: "energy_technology.md",
```

### 10g. 🔍 NEEDS VERIFICATION: L2 deep dive count doesn't account for gap-fill agents
**File:** `orchestrator.py`, `run_l2()` line 380
```python
n_agents = min(self.config.max_l2_agents, max(len(run.tension_points), self.config.min_l2_agents))
```
**Issue:** With the tension point parsing fix, `len(run.tension_points)` now returns 20. So `n_agents = min(8, max(20, 6)) = 8`. This is fine — L2 generation is capped at `max_l2_agents`.
But: the gap-fill agents' findings are NOT represented as tension points. They contribute to L1.5 consolidation (which regenerates after gap-fill), but their unique angles may not surface as distinct tension points in the re-consolidation. If gap-fill agents find something genuinely novel (e.g., the "regulated utility" analogy for Acadia's CTC network), it should become a tension point that can be selected for L2 investigation.
**Action:** Verify this by checking whether gap-fill findings appear in the re-consolidated tension points. If they don't, the gap-fill value is being diluted at L2 generation.

### 10h. ✅ FIXED: The L2 context assembly truncates uniformly but should log WHICH agents got truncated
**File:** `context_manager.py`, `assemble_l3_input()` lines 70-93
**Issue:** When truncation happens, the warning message says "Truncating L2 outputs to fit" but doesn't say which agents were truncated or by how much. For debugging, you need to know if a critical L2 finding was cut short.
**Fix:** Log per-agent truncation:
```python
if count_tokens(text) > target_per_l2:
    original_tokens = count_tokens(text)
    text = text[:target_chars] + "\n\n[... truncated for context window ...]"
    logger.warning(
        f"  L2 agent '{output.agent_name}' truncated from {original_tokens} to ~{target_per_l2} tokens"
    )
```

---

## APPENDIX: ESTIMATED COST PROFILE AFTER ALL FIXES

*Updated to reflect what was actually implemented vs. still open.*

**Implemented fixes that affect cost:** 2a (max_tokens 32K), 2b (concurrency 4), 2c/2d (budget headroom), 4b (gap-fill parallel — wall time only, not cost), all bug fixes.

**Not yet implemented that would affect cost:** 5a (Haiku quality checks, +$0.20/run), contrarian integration if 6e decided yes (+$10-15/run).

Assuming all config changes and structural improvements are implemented:

| Layer | Before (Bloom) | After (estimated) | Notes |
|---|---|---|---|
| L0 | $1.09 (1 round) | $2.50-3.50 (3 rounds) | Increased max_tokens |
| L0.5 | $1.75 | $1.75-2.00 | Unchanged |
| L1 | $12.65 (8×1 round) | $28-38 | 8 agents × 3 rounds + quality retries + larger output |
| Gap Fill | $0 | $12-18 | 2 agents × 3 rounds |
| L1.5 | $2.88 | $5.50-6.50 | Initial + re-consolidation |
| L2 | $16.40 | $20-28 | Quality retries, larger output |
| Contrarian L2 | $0 | $10-15 | 2-3 lateral agents (if integrated) |
| L3 | $6.15 | $6-9 | Unchanged pipeline, slightly more input |
| Quality checks | $0 | $0.20-0.50 | Haiku semantic checks |
| **TOTAL** | **$42** | **$87-120** |

The sweet spot is $75-95 for a standard run. Complex companies (multi-segment, international, heavy SEC filing history) may approach $110-120.
