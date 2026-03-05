# Deep Research System

A multi-layered AI research system that takes a company name and produces world-class strategic analysis with operationally specific ideas.

## How It Works

```
Company Name → L0 Profile → L0.5 Agent Design → L1 Parallel Research (6-10 agents)
→ L1.5 Consolidation (tension points) → L2 Targeted Deep Dives (8-12 agents)
→ L3 Final Synthesis → Executive Briefing + Full Report
```

**Total runtime:** ~25-45 minutes (most steps run in parallel)
**Estimated cost:** $40-110 per company (Claude API)

## Quick Start

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here

python -m deep_research "Camellia Plc"
```

## Documentation

| Document | Purpose |
|----------|---------|
| `CONTEXT.md` | Master context — read this first |
| `orchestration_spec.md` | Technical architecture & implementation spec |
| `prompts/L0_company_profile.md` | Company profiling prompt |
| `prompts/L05_agent_design.md` | Meta-prompt that generates research agents |
| `prompts/L15_consolidation.md` | Synthesis & tension point identification |
| `prompts/L2_generation.md` | Converts tension points to deep dive prompts |
| `prompts/L3_final_synthesis.md` | Final report generation |

## Key Design Principles

1. **Operational specificity** — Ideas must reference specific assets, capabilities, and facts
2. **Iterative search** — Multiple rounds of search produce dramatically better research
3. **Calibration examples** — Industry-matched examples anchor the quality bar
4. **Quality gates** — Each layer validates output before proceeding

## Origin

Developed from a hand-crafted research system for Camellia Plc (LSE: CAM) that produced 28 operationally specific strategic ideas. Generalized to work for any company.
