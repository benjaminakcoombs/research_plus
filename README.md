# Deep Analysis

Multi-layered AI research pipeline that produces world-class strategic analysis from a company name. Runs 15-20 research agents across 6 pipeline layers, synthesizing hundreds of sources into a single deliverable. Cost: ~$40-70 per run. Time: ~2 hours.

## Two modes

### `strategic_briefing` — Executive strategic analysis
Produces a McKinsey-grade strategic briefing FOR a company's management team. Surfaces operationally specific opportunities, risks, and structural unlocks. The reader is the CEO/COO.

```bash
python -m deep_research "Camellia Plc" --mode strategic_briefing --run-all
```

### `situation_assessment` — Deal intelligence for bankers
Produces an M&A-oriented Situation Assessment ABOUT a company for an external advisor. Surfaces tension points, valuation context, buyer universe, and deal catalysts. The reader is a boutique IB managing director.

```bash
python -m deep_research "Acadia Healthcare" \
  --mode situation_assessment \
  --sector "healthcare services" \
  --sub-sector "behavioral health" \
  --target-bank "Perella Weinberg Partners" \
  --run-all
```

## Pipeline layers

```
L0   Company Profile        → What this company is, does, owns
L0.5 Agent Design           → Designs 6-8 targeted research workstreams
L1   Parallel Research       → 6-8 agents run deep web research in parallel
L1.5 Consolidation          → Synthesizes into 15-20 tension points
L2   Targeted Deep Dives    → Validates top hypotheses with fresh research
L3a  Synthesis Draft        → Produces the structured document from research
L3b  Final Refinement       → Editor pass: sharpens, tightens, makes client-ready
```

Each layer can be run independently. Resume any run from where it stopped:

```bash
# Run just L0
python -m deep_research "Company Name" --stop-after l0

# Resume from a previous run
python -m deep_research --resume run_abc123 --stop-after l1

# List all runs
python -m deep_research --list-runs
```

## Project structure

```
deep_research/             # Python package — orchestration, API calls, quality checks
prompts/
  strategic_briefing/      # Prompt chain for exec/consulting mode
    l0_company_profile.md
    l05_agent_design.md
    l15_consolidation.md
    l2_generation.md
    l3_final_synthesis.md
    calibration_examples/  # Archetype-matched quality anchors
  situation_assessment/    # Prompt chain for banking/deal mode
    l0_company_profile.md
    l05_agent_design.md
    l15_consolidation.md
    l2_generation.md
    l3_final_synthesis.md
    calibration_examples/
docs/                      # Design docs, specs, overviews (not prompts)
  CONTEXT.md               # Master context document
  SITUATION_ASSESSMENT_OVERVIEW.md
  orchestration_spec.md
  pipeline_design/         # Per-layer design notes
outputs/                   # Run outputs (one folder per run)
examples/                  # Reference outputs for benchmarking
```

## Key principle

The prompts are the product. The code is straightforward orchestration. Each mode has its own complete prompt chain tuned for its audience. Treat prompts as versioned configuration — edit them carefully.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key
```

## Configuration

Override defaults via CLI flags:

| Flag | Default | Description |
|------|---------|-------------|
| `--max-cost` | $150 | Hard budget stop |
| `--max-concurrent` | 2 | Parallel API tasks |
| `--research-model` | claude-sonnet-4-6 | Model for web search tasks |
| `--synthesis-model` | claude-opus-4-6 | Model for reasoning/synthesis |
| `--search-rounds` | 3 | Iterative search rounds per agent |
| `--format` | markdown | Output: markdown, pdf, docx, all |
