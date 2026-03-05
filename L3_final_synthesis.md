# L3: Final Synthesis & Report Generation

## Purpose
This is the final synthesis step. It takes ALL prior outputs (L0 profile, L1 research, L1.5 tension points, L2 deep dives) and produces the customer-facing deliverables:
1. Executive Strategic Briefing — the premium output
2. Full Research Compendium — comprehensive reference

This is a pure synthesis task. Run on the most capable reasoning model with maximum context.

---

## PROMPT SUMMARY

The full prompt is at `/prompts/l3_final_synthesis.md`. Key structural elements:

### Deliverable 1: Executive Strategic Briefing

**1. SITUATION OVERVIEW** (500-800 words) — Opinionated strategic narrative

**2. TOP STRATEGIC IDEAS** (8-12 ideas) — For each:
- Idea Title, Insight, Evidence, The Play, Magnitude, Risk
- Confidence level
- **EXECUTION REQUIREMENT** (NEW): What capability, hire, org change, or partnership is needed
- Key Citations

**3. RISK LANDSCAPE** (300-500 words) — Narrative about interacting risks
- NEW: Per-risk pre-mortem ("If this risk materialized, the most likely reason we failed to prevent it is...")

**4. WHAT TO DO NEXT** (200-400 words) — 90-day action sequence

**5. BLIND SPOTS & LIMITATIONS** (200-300 words, NEW)
- What might this analysis have systematically missed?
- What questions need internal data, customer interviews, or operational access?
- What would change under a completely different lens?

### Deliverable 2: Full Research Compendium
- Company profile summary, workstream summaries, tension point tracker, source bibliography, data gaps

### Quality Checklist (expanded)
- Every idea references specific operational facts
- Every idea has comparable examples and magnitude estimates
- At least one idea addresses narrative/positioning (NEW)
- Every idea includes an execution requirement (NEW)
- The blind spots section is honest and specific (NEW)
- At least one contrarian idea
- Data gaps disclosed honestly

---

## VARIABLES

| Variable | Source | Required |
|----------|--------|----------|
| `{COMPANY_NAME}` | User input | Yes |
| `{N_L1_AGENTS}` | Count of L1 agents | Yes |
| `{N_TENSION_POINTS}` | Count from L1.5 | Yes |
| `{N_L2_AGENTS}` | Count of L2 agents | Yes |
| `{ALL_OUTPUTS}` | Concatenated: L0 + all L1 + L1.5 + all L2 outputs | Yes |

## EXPECTED OUTPUT SIZE
- Executive Briefing: 3,000-6,000 words
- Full Research Compendium: 5,000-10,000 words

## KEY CHANGES FROM PREVIOUS VERSION
- Added EXECUTION REQUIREMENT field per idea (capability, hire, org change, or partnership)
- Added Section 5: BLIND SPOTS & LIMITATIONS
- Risk landscape now includes per-risk pre-mortem
- Quality checklist expanded: narrative/positioning, execution requirement, blind spots

## TOKEN BUDGET NOTE
The input to this prompt (ALL_OUTPUTS) could easily be 40,000-80,000 words. This requires a model with at least 128k context window, preferably 200k. If inputs exceed context limits:
- Option A: Summarize L1 outputs before including them (losing some detail)
- Option B: Include only L1.5 consolidation + L2 outputs (L1 detail is captured in L1.5)
- Option C: Split into two passes

Recommended: Option B for the executive briefing, Option A for the compendium.
