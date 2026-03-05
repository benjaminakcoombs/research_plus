# Deep Research System — Master Context Document

## For: Claude Code / Codex Implementation

This document provides full context for implementing the Deep Research System. Read this first, then read each referenced file.

---

## What This System Does

Takes a company name as input. Produces a world-class strategic analysis report identifying operationally specific ideas — risks, opportunities, structural unlocks, and information arbitrage. The kind of analysis that costs $50-200k from McKinsey.

The system works by running 3 layers of AI-powered deep research, each building on the last:
- **Layer 1**: 6-10 parallel research agents examine the company from different angles (financials, governance, competitive landscape, etc.)
- **Layer 1.5**: A synthesis step identifies 15-20 "tension points" — anomalies and contradictions that suggest strategic opportunities
- **Layer 2**: 8-12 targeted deep dives investigate the most promising tension points
- **Layer 3**: Final synthesis produces the customer-facing report

Quality comes from the prompts, not the code. The prompts are the IP. The code is orchestration.

---

## File Map

| File | What It Is | Priority |
|------|-----------|----------|
| `prompts/L0_company_profile.md` | Prompt that profiles a company from scratch | Read first |
| `prompts/L05_agent_design.md` | Meta-prompt that generates customized L1 research prompts — THIS IS THE BRAIN | Read second |
| `prompts/L15_consolidation.md` | Prompt that synthesizes L1 outputs into tension points | Read third |
| `prompts/L2_generation.md` | Logic for converting tension points into L2 research prompts | Read fourth |
| `prompts/L3_final_synthesis.md` | Prompt that produces the final customer-facing report | Read fifth |
| `orchestration_spec.md` | Technical spec: architecture, data models, API usage, parallelism, error handling | Read for implementation |

---

## Critical Design Principles

These are non-negotiable. If you're unsure about an implementation decision, re-read these:

### 1. Operational Specificity Is Everything
The system's value comes from producing ideas like "Camellia's macadamia shells could be processed into activated carbon at 3-5x the margin" — not "Camellia should explore ESG opportunities." Every prompt in the system is designed to push toward this level of specificity. Do not simplify or genericize the prompts.

### 2. The Prompts Are the Product
The code is straightforward orchestration (API calls, parallelism, file I/O). The prompts are the intellectual property. Treat them as immutable configuration — they should be loaded from files, not hardcoded, and versioned carefully.

### 3. Iterative Search > Single Search
A research task that does 3-5 rounds of "search → read → identify gaps → search again" produces dramatically better output than one that does a single pass. Build the iterative search loop. It's worth the extra cost.

### 4. Context Window Management Is a First-Class Concern
L1.5 and L3 ingest massive amounts of text. Implement token counting and graceful compression. Never silently truncate — always log when compression is applied.

### 5. Quality Checks Gate the Pipeline
Each layer should have quality checks. If L0 doesn't produce a rich enough profile, L0.5 will generate generic prompts, and everything downstream suffers. Better to re-run L0 than to proceed with bad inputs.

---

## Reference Implementation: Camellia Plc

The system was originally developed for Camellia Plc (LSE: CAM), a UK-listed diversified agriculture holding company. The Camellia implementation is the quality benchmark.

**What made the Camellia prompts exceptional:**
- Asked about specific facilities by name (Kakuzi macadamia processing plant, Mombasa tea auction)
- Probed waste streams (macadamia shells, tea dust, rubber processing waste)
- Mapped local ecosystems (what other companies operate near Camellia's estates? what infrastructure is missing?)
- Asked about procurement scale (what does Camellia buy in volume that smaller operators can't?)
- Required anomaly flagging at the end of every research output
- Used calibration examples (Jostens, Home Depot) to anchor the quality bar for ideas

**Key Camellia output examples (for benchmarking):**
- "Camellia's 3,500 Kakuzi outgrowers are a captive distribution channel for agricultural inputs — fertilizer, agrochemicals, packaging. A Wilmar-style input distribution business could be launched with near-zero capital by leveraging factory-gate credit offsets."
- "KTDA tea factories are in genuine operational distress. Camellia's EP Kenya already manages two third-party factories. A factory management consulting practice targeting KTDA could generate revenue while creating strategic lock-in."
- "Camellia's Bangladeshi estates include a 50-bed hospital with cancer care capabilities. The surrounding 90k population and nearby Chevron/EZ tenants have limited healthcare access. Healthcare commercialization could be both revenue-generating and ESG-positive."

The generalized system must produce ideas at this level of specificity for ANY company, not just Camellia.

---

## Prompt Variable System

Each prompt file uses `{VARIABLE_NAME}` syntax. The prompt builder must substitute these before sending to the API.

**L0 variables:**
- `{COMPANY_NAME}` — from user input
- `{OPTIONAL_USER_CONTEXT}` — from user input (may be empty)

**L0.5 variables:**
- `{L0_OUTPUT}` — complete output from L0

**L1.5 variables:**
- `{COMPANY_NAME}` — from user input
- `{N_AGENTS}` — count of L1 agents run
- `{CALIBRATION_EXAMPLES}` — selected based on company archetype detected in L0
- `{ALL_L1_OUTPUTS}` — concatenated L1 outputs, each labeled with agent name

**L2 generation variables:**
- `{COMPANY_NAME}` — from user input
- `{N_L2_AGENTS}` — configuration parameter (default: 8-12)
- `{L15_TENSION_POINTS}` — Deliverable 2 from L1.5

**L3 variables:**
- `{COMPANY_NAME}` — from user input
- `{N_L1_AGENTS}`, `{N_TENSION_POINTS}`, `{N_L2_AGENTS}` — counts
- `{ALL_OUTPUTS}` — assembled by context manager (may be compressed)

---

## Calibration Example Selection

The consolidation prompt (L1.5) includes industry-matched calibration examples to anchor the quality bar. These are stored in `prompts/calibration_examples/{archetype}.md`.

The company archetype is extracted from the L0 output. The prompt builder selects the matching calibration examples. If no exact match, use `manufacturer.md` as default — those examples illustrate the principles most clearly.

---

## Output Format

The final deliverables should be produced as:
1. **Markdown** — always (this is the canonical format, stored in outputs/)
2. **PDF** — optional, generated from Markdown via pandoc or weasyprint
3. **DOCX** — optional, generated from Markdown via pandoc

The executive briefing should be formatted for professional presentation:
- Clean typography
- Consistent heading hierarchy
- Tables where appropriate
- Citation formatting
- Page breaks between major sections

---

## Cost Tracking

Track and log estimated cost for every API call:

```python
# Approximate pricing (update as prices change)
PRICING = {
    "claude-sonnet-4-5-20250929": {
        "input_per_1k": 0.003,
        "output_per_1k": 0.015,
        "search_per_call": 0.01,  # rough estimate for web search
    },
    "claude-opus-4-6": {
        "input_per_1k": 0.015,
        "output_per_1k": 0.075,
    }
}
```

Implement a running cost tracker that:
- Logs cost per task
- Warns when approaching budget
- Halts gracefully (saving partial outputs) if budget exceeded

---

## Testing Strategy

### Unit Tests
- Prompt builder correctly substitutes variables
- Context manager correctly counts tokens and compresses
- Quality checker correctly identifies missing sections

### Integration Tests
- Run L0 for 3 diverse companies (one manufacturer, one SaaS, one conglomerate)
- Verify L0.5 generates appropriate agent selections for each
- Verify L1 prompts contain company-specific details (not generic)

### Quality Tests (Manual)
- Run full pipeline for Camellia Plc and compare against reference outputs
- Have a human expert rate the top 5 ideas on a 1-10 scale for:
  - Specificity (grounded in operational facts?)
  - Novelty (would an executive say "I hadn't thought of that"?)
  - Feasibility (could this actually be implemented?)
  - Magnitude (is this worth pursuing?)

### Benchmark Companies for Testing
1. **Camellia Plc** (reference — we have ground truth outputs)
2. **Danaher Corporation** (diversified manufacturer — tests archetype selection)
3. **Shopify** (SaaS/platform — tests non-physical-asset ideas)
4. **Glencore** (commodities/extraction — tests value chain analysis)
5. **Berkshire Hathaway** (conglomerate — tests at scale)

---

## Dependencies

```
anthropic>=0.40.0
pydantic>=2.0
tiktoken>=0.5.0
asyncio
aiohttp
rich        # CLI output formatting
pandoc      # Markdown → PDF/DOCX (optional, system dependency)
```

---

## Implementation Order

1. **Data models** (`models.py`) — Pydantic schemas
2. **Prompt builder** (`prompt_builder.py`) — Load prompts, substitute variables, select calibration examples
3. **Research runner** (`research_runner.py`) — Iterative search loop, API calls
4. **Context manager** (`context_manager.py`) — Token counting, compression
5. **Quality checker** — Per-layer quality validation
6. **Orchestrator** (`orchestrator.py`) — Main pipeline
7. **CLI** (`main.py`) — Command-line interface
8. **Report generator** (`report_generator.py`) — Markdown → PDF/DOCX
9. **Tests**

Start with items 1-3 and test them independently before wiring up the orchestrator.
