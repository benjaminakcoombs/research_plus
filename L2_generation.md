# L2: Targeted Deep Dive Prompt Generation

## Purpose
This prompt takes the tension points from L1.5 and converts the top 6-8 into targeted deep research prompts. Each L2 prompt investigates a specific hypothesis with a specific research question.

This is a generation task (no web search needed). Run on a reasoning model.

---

## PROMPT SUMMARY

The full prompt is at `/prompts/l2_generation.md`. Key structural elements:

**Critical Requirement: Contrarian & Lateral Ideas** — At least 2-3 prompts must investigate genuinely surprising ideas (cross-industry transplants, asset repurposing, business model inversions, non-obvious customer segments, platform plays).

**Prompt Template** — Each L2 prompt includes:
- Expert persona
- Self-contained context (2-3 paragraphs)
- Hypothesis to investigate
- 6 research questions:
  1. Primary validation question
  2. Supporting evidence question
  3. Comparable/precedent question
  4. Feasibility question
  5. Magnitude question
  6. Execution question (NEW — can the current team/org execute this?)
- Research guidance with named sources
- Output format: Evidence for/against, comparables, feasibility, execution & pre-mortem (NEW), magnitude, confidence, citations

**Execution & Pre-Mortem** (NEW in output format):
- Can the current management team execute this? What capabilities are missing?
- What internal resistance or structural barriers would this face?
- Pre-mortem: If this was attempted and failed within 18 months, what is the single most likely cause?

**Selection Criteria** — Prioritize by expected value, ensure category diversity (including 2-3 lateral/contrarian), prefer points where research changes the assessment, combine related points, exclude purely internal questions.

---

## VARIABLES

| Variable | Source | Required |
|----------|--------|----------|
| `{COMPANY_NAME}` | User input | Yes |
| `{N_L2_AGENTS}` | Configuration (default: 6-8) | Yes |
| `{L15_TENSION_POINTS}` | Full Deliverable 2 from L1.5 consolidation | Yes |

## EXPECTED OUTPUT SIZE
4,000-10,000 words depending on number of agents.

## KEY CHANGES FROM PREVIOUS VERSION
- Added execution question (#6) to research questions
- Added "4b. EXECUTION & PRE-MORTEM" section to output format
- Pre-mortem asks for single most likely cause of failure within 18 months

## SUCCESS CRITERIA
Each L2 prompt should:
1. Be executable by a researcher with no prior context beyond what's in the prompt
2. Have a clear hypothesis to confirm or deny (not an open-ended "research X")
3. Specify where to look and what data points to find
4. Require comparable examples (especially cross-industry)
5. Ask about execution feasibility and failure modes
6. Produce output that definitively moves the assessment of the tension point forward
