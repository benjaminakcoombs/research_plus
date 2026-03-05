# L1.5: Consolidation & Tension Point Identification

## Purpose
This prompt takes all L1 research outputs (6-10 dense reports) and synthesizes them into:
1. A Company Situation Map (executive summary)
2. 15-20 operationally specific tension points with L2 research questions
3. A classification challenge and research gaps assessment (NEW)

This is a synthesis/reasoning task — no web search needed. Run on the most capable reasoning model available (Claude Opus with extended thinking) with maximum context window.

---

## PROMPT SUMMARY

The full prompt is at `/prompts/l15_consolidation.md`. Key structural elements:

**Deliverable 1: Company Situation Map** — Opinionated synthesis: what the company IS, what it SAYS it's doing, what the ENVIRONMENT is doing to it, what's CHANGED recently.

**Deliverable 2: Tension Points & Research Hypotheses** — 15-20 tension points, each with: tension, hypothesis, category, magnitude, time horizon, confidence, L2 research question.

Tension point generation uses:

*Five Generative Frames* (NEW — applied before the specific checklist):
1. WHERE IS VALUE TRAPPED?
2. WHERE IS REALITY DIVERGING FROM NARRATIVE?
3. WHAT WOULD SOMEONE OUTSIDE THIS INDUSTRY SEE?
4. WHAT IS THE REAL CONSTRAINT?
5. WHAT JUST CHANGED THAT CREATES A WINDOW?

*Specific Pattern Checklist* (retained, reframed as examples of the frames):
Narrative-reality gaps, asset optimization, waste-to-value, procurement/scale arbitrage, infrastructure-as-service, capability transfer, relationship arbitrage, competitive blind spots, structural inefficiencies, timing windows, information arbitrage.

*Meta-instruction* (NEW): Calibration examples illustrate specificity level, not idea types. Tension points may involve brand, data, community, perception, pricing power — not limited to physical assets.

*Pre-mortem* (NEW): Top 5 ideas must include "If this idea were tried and failed, the most likely reason would be..."

**Deliverable 3: Classification Challenge & Research Gaps** (NEW)
- Archetype Challenge: Is the L0 classification actually the right lens? What's visible under an alternative framing?
- Research Gaps: What should L1 have investigated but didn't? What would 2-3 additional agents investigate?

---

## VARIABLES

| Variable | Source | Required |
|----------|--------|----------|
| `{COMPANY_NAME}` | User input | Yes |
| `{N_AGENTS}` | Count of L1 agents run | Yes |
| `{ARCHETYPE}` | From L0 archetype classification | Yes |
| `{CALIBRATION_EXAMPLES}` | Auto-selected based on company archetype | Yes |
| `{ALL_L1_OUTPUTS}` | Concatenated outputs from all L1 agents | Yes |

## GAP-FILL MECHANISM
When Deliverable 3 identifies research gaps and `config.enable_gap_fill` is True, the orchestrator will:
1. Parse the RESEARCH GAPS section
2. Generate 1-2 supplementary L1 prompts
3. Run those agents
4. Re-run L1.5 consolidation with expanded corpus

## EXPECTED OUTPUT SIZE
4,000-8,000 words.

## KEY CHANGES FROM PREVIOUS VERSION
- Added five generative frames above the existing checklist
- Meta-instruction clarifies calibration examples show specificity level, not idea types
- Pre-mortem requirement for top 5 ideas
- Deliverable 3 added: classification challenge + research gaps
- Research gaps feed the orchestrator's gap-fill mechanism

## SUCCESS CRITERIA
The consolidation output is good enough if:
1. Every tension point references specific facts from the L1 research (not generic observations)
2. Every L2 research question is specific enough that a researcher knows exactly what to look for
3. The top 5 tension points could be presented to an executive and they'd say "I hadn't thought of that"
4. The ideas span multiple categories (offensive, defensive, structural, information arbitrage)
5. At least some ideas address narrative/positioning, not just operations
6. The classification challenge is thoughtful, not perfunctory
7. Research gaps are specific enough to generate actionable supplementary prompts
