# Deep Research System — Orchestration Specification

## System Overview

A multi-layered deep research system that takes a company name as input and produces world-class strategic analysis with operationally specific ideas. The system runs 6 steps in sequence, with parallelism at L1 and L2.

```
INPUT: company_name (str) + optional_context (str)
                │
    ┌───────────┴───────────┐
    │  L0: Company Profile   │  1 deep research task (~5-10 min)
    │  (web search required)  │  Output: structured company profile
    └───────────┬───────────┘
                │
    ┌───────────┴───────────┐
    │  L0.5: Agent Design    │  1 synthesis call (~30-60 sec)
    │  (no web search)       │  Output: 6-10 customized L1 prompts
    └───────────┬───────────┘
                │
    ┌───────────┴───────────┐
    │  L1: Parallel Research  │  6-10 deep research tasks in parallel (~5-10 min each)
    │  (web search required)  │  Output: 6-10 dense research reports
    └───────────┬───────────┘
                │
    ┌───────────┴───────────┐
    │  L1.5: Consolidation   │  1 synthesis call (~2-5 min with extended thinking)
    │  (no web search)       │  Output: situation map + 15-20 tension points
    └───────────┬───────────┘
                │
    ┌───────────┴───────────┐
    │  L2: Targeted Dives    │  8-12 deep research tasks in parallel (~5-10 min each)
    │  (web search required)  │  Output: 8-12 hypothesis validation reports
    └───────────┬───────────┘
                │
    ┌───────────┴───────────┐
    │  L3: Final Synthesis   │  1 synthesis call (~3-5 min with extended thinking)
    │  (no web search)       │  Output: Executive Briefing + Full Report
    └───────────┴───────────┘
                │
OUTPUT: Two documents (Markdown → PDF/DOCX)
```

## Total Runtime & Cost Estimates

| Step | Tasks | Runtime (parallel) | Estimated API Cost |
|------|-------|-------------------|-------------------|
| L0 | 1 | 5-10 min | $2-5 |
| L0.5 | 1 | 30-60 sec | $0.50-1 |
| L1 | 6-10 | 5-10 min (parallel) | $15-40 |
| L1.5 | 1 | 2-5 min | $2-5 |
| L2 | 8-12 | 5-10 min (parallel) | $20-50 |
| L3 | 1 | 3-5 min | $3-8 |
| **Total** | **18-35** | **~25-45 min wall clock** | **$40-110** |

Cost varies significantly by model choice and search depth. These estimates assume Claude Opus/Sonnet with iterative web search.

---

## Architecture Decisions

### API Provider & Model Selection

**Research steps (L0, L1, L2)** — Require web search + synthesis:
- PRIMARY: Claude API (claude-sonnet-4-5-20250929) with `web_search` tool + extended thinking
- The iterative search loop is critical — a single search pass misses too much
- Each research task should execute 10-25 web searches iteratively

**Synthesis steps (L0.5, L1.5, L3)** — Require reasoning over long context:
- PRIMARY: Claude API (claude-opus-4-6) with extended thinking, max budget tokens
- These are the most intellectually demanding steps
- L1.5 and L3 need the largest context windows (100k-200k tokens input)

### Iterative Search Loop Architecture

For research steps, don't just make one API call with web_search. Build an iterative research loop:

```python
def run_research_task(prompt: str, max_rounds: int = 5) -> str:
    """
    Runs an iterative deep research task.
    
    Round 1: Initial broad research based on the prompt
    Rounds 2-N: Agent identifies gaps in its research and searches for more
    Final: Agent produces consolidated output
    """
    messages = [{"role": "user", "content": prompt}]
    
    full_output = ""
    
    for round in range(max_rounds):
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=16000,
            thinking={
                "type": "enabled",
                "budget_tokens": 10000
            },
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 10  # 10 searches per round
            }],
            messages=messages
        )
        
        # Extract text content
        assistant_text = extract_text(response)
        full_output += assistant_text
        
        # Check if agent wants to continue researching
        if agent_is_satisfied(response) or round == max_rounds - 1:
            break
        
        # Add continuation prompt
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": "Continue your research. What gaps remain? Search for additional information to fill them, then produce your complete output."
        })
    
    return full_output
```

**Alternative: Single-call with high search budget**

If iterative loops prove too complex or slow, use single calls with high `max_uses`:

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 15000
    },
    tools=[{
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 25  # More searches per call
    }],
    messages=[{"role": "user", "content": prompt}]
)
```

Test both approaches and compare output quality. The iterative approach typically produces better coverage but costs more.

### Parallelism

L1 and L2 tasks are independent and should run in parallel:

```python
import asyncio

async def run_layer(prompts: list[str]) -> list[str]:
    """Run multiple research tasks in parallel."""
    tasks = [run_research_task(prompt) for prompt in prompts]
    results = await asyncio.gather(*tasks)
    return results
```

Rate limits may require batching (e.g., 5 concurrent tasks max). Implement with a semaphore:

```python
semaphore = asyncio.Semaphore(5)

async def run_research_task_limited(prompt: str) -> str:
    async with semaphore:
        return await run_research_task(prompt)
```

### Context Window Management

The biggest technical challenge is context window management at L1.5 and L3, where all prior outputs must be synthesized.

**Token budget estimates:**
- L0 output: ~5,000-15,000 tokens
- Each L1 output: ~4,000-12,000 tokens
- Total L1 outputs (8 agents): ~32,000-96,000 tokens
- L1.5 output: ~6,000-15,000 tokens
- Each L2 output: ~3,000-8,000 tokens
- Total L2 outputs (10 agents): ~30,000-80,000 tokens

**For L1.5 consolidation (input: all L1 outputs):**
- Typical input: ~50,000-80,000 tokens
- This fits within Claude's 200k context window
- Use Opus for best synthesis quality

**For L3 final synthesis (input: everything):**
- Typical input: ~80,000-180,000 tokens
- May push limits. Fallback strategies:
  1. Include L1.5 consolidation + all L2 outputs (skip raw L1 outputs since they're captured in L1.5)
  2. Summarize each L1 output to ~1,000 tokens before including
  3. Two-pass: Executive briefing from L1.5+L2, then compendium from L1 summaries

Implement context tracking:

```python
import tiktoken

def count_tokens(text: str) -> int:
    """Estimate token count (Claude uses a similar tokenizer to cl100k)."""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

def fit_to_context(outputs: dict, max_tokens: int = 180000) -> str:
    """Assemble outputs to fit within context window, prioritizing recent layers."""
    # Priority order: L1.5, L2 outputs, L0, L1 outputs (summarized if needed)
    ...
```

---

## Data Model

```python
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class CompanyArchetype(str, Enum):
    MANUFACTURER = "manufacturer"
    EXTRACTOR_GROWER = "extractor_grower"
    RETAILER_DISTRIBUTOR = "retailer_distributor"
    PLATFORM_MARKETPLACE = "platform_marketplace"
    SAAS_SOFTWARE = "saas_software"
    FINANCIAL_SERVICES = "financial_services"
    INFRASTRUCTURE_UTILITIES = "infrastructure_utilities"
    PROFESSIONAL_SERVICES = "professional_services"
    CONGLOMERATE = "conglomerate"
    HEALTHCARE_PHARMA = "healthcare_pharma"
    MEDIA_ENTERTAINMENT = "media_entertainment"
    REAL_ESTATE = "real_estate"
    OTHER = "other"

class TensionCategory(str, Enum):
    OFFENSIVE = "offensive_opportunity"
    DEFENSIVE = "defensive_risk"
    STRUCTURAL = "structural_unlock"
    INFORMATION = "information_arbitrage"

class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Magnitude(str, Enum):
    TRANSFORMATIONAL = "transformational"
    MAJOR = "major"
    MODERATE = "moderate"

class TimeHorizon(str, Enum):
    IMMEDIATE = "immediate_6mo"
    NEAR_TERM = "near_term_6_18mo"
    MEDIUM_TERM = "medium_term_1_3yr"

class ResearchRun(BaseModel):
    """Top-level container for an entire research project."""
    id: str
    company_name: str
    company_ticker: str | None = None
    user_context: str | None = None
    created_at: datetime
    status: str  # pending, l0_complete, l1_running, l1_complete, etc.
    
    # Outputs
    l0_output: str | None = None
    company_archetype: CompanyArchetype | None = None
    l05_output: str | None = None  # Agent design output
    l1_prompts: list[str] = []
    l1_outputs: list[AgentOutput] = []
    l15_output: str | None = None  # Consolidation
    tension_points: list[TensionPoint] = []
    l2_prompts: list[str] = []
    l2_outputs: list[AgentOutput] = []
    l3_executive_briefing: str | None = None
    l3_full_report: str | None = None

class AgentOutput(BaseModel):
    """Output from a single research agent."""
    agent_name: str
    agent_type: str  # l1 or l2
    prompt: str
    raw_output: str
    token_count: int
    search_count: int
    execution_time_seconds: float
    sources_cited: list[str] = []

class TensionPoint(BaseModel):
    """A strategic tension point identified in L1.5."""
    id: int
    title: str
    tension: str
    hypothesis: str
    category: TensionCategory
    magnitude: Magnitude
    time_horizon: TimeHorizon
    confidence: Confidence
    l2_research_question: str
    l2_investigated: bool = False
    l2_output: str | None = None
    final_confidence: Confidence | None = None
    included_in_executive_briefing: bool = False
```

---

## File Structure

```
deep_research_system/
├── README.md
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── orchestrator.py       # Main pipeline orchestration
│   ├── research_runner.py    # Iterative search loop implementation
│   ├── prompt_builder.py     # Assembles prompts from templates + variables
│   ├── context_manager.py    # Token counting + context window fitting
│   ├── models.py             # Pydantic data models
│   ├── report_generator.py   # Markdown → PDF/DOCX conversion
│   └── config.py             # API keys, model selection, cost limits
├── prompts/
│   ├── L0_company_profile.md
│   ├── L05_agent_design.md
│   ├── L15_consolidation.md
│   ├── L2_generation.md
│   ├── L3_final_synthesis.md
│   └── calibration_examples/
│       ├── manufacturer.md
│       ├── retailer.md
│       ├── saas.md
│       ├── financial_services.md
│       ├── healthcare.md
│       └── conglomerate.md
├── outputs/
│   └── {run_id}/
│       ├── l0_profile.md
│       ├── l05_agent_design.md
│       ├── l1_agents/
│       │   ├── agent_01_core_business.md
│       │   ├── agent_02_governance.md
│       │   └── ...
│       ├── l15_consolidation.md
│       ├── l2_agents/
│       │   ├── dive_01_carbon_credits.md
│       │   └── ...
│       ├── l3_executive_briefing.md
│       ├── l3_full_report.md
│       └── metadata.json
├── examples/
│   └── camellia/             # Reference implementation
│       ├── l1_prompts.md     # The original Camellia prompts
│       └── sample_outputs/   # Example outputs for quality benchmarking
└── tests/
    ├── test_prompt_builder.py
    ├── test_context_manager.py
    └── test_quality.py       # Output quality assertions
```

---

## Pipeline Implementation

```python
# orchestrator.py (pseudocode)

class DeepResearchOrchestrator:
    
    def __init__(self, config: Config):
        self.research_runner = ResearchRunner(config)
        self.prompt_builder = PromptBuilder()
        self.context_manager = ContextManager()
    
    async def run(self, company_name: str, context: str | None = None) -> ResearchRun:
        run = ResearchRun(
            id=generate_id(),
            company_name=company_name,
            user_context=context,
            created_at=datetime.now(),
            status="started"
        )
        
        # === L0: Company Profile ===
        print(f"[L0] Profiling {company_name}...")
        l0_prompt = self.prompt_builder.build_l0(company_name, context)
        run.l0_output = await self.research_runner.run_research(l0_prompt)
        run.status = "l0_complete"
        
        # === L0.5: Agent Design ===
        print(f"[L0.5] Designing research agents...")
        l05_prompt = self.prompt_builder.build_l05(run.l0_output)
        l05_response = await self.research_runner.run_synthesis(l05_prompt)
        run.l05_output = l05_response
        run.l1_prompts = self.parse_agent_prompts(l05_response)
        run.company_archetype = self.extract_archetype(run.l0_output)
        run.status = "l05_complete"
        
        # === L1: Parallel Research ===
        print(f"[L1] Running {len(run.l1_prompts)} research agents in parallel...")
        l1_results = await self.run_parallel_research(run.l1_prompts)
        run.l1_outputs = l1_results
        run.status = "l1_complete"
        
        # === L1.5: Consolidation ===
        print(f"[L1.5] Consolidating research outputs...")
        l15_prompt = self.prompt_builder.build_l15(
            company_name=company_name,
            n_agents=len(run.l1_outputs),
            archetype=run.company_archetype,
            l1_outputs=run.l1_outputs
        )
        
        # Check context window fit
        l15_input_tokens = self.context_manager.count_tokens(l15_prompt)
        if l15_input_tokens > 180000:
            l15_prompt = self.context_manager.compress_for_l15(l15_prompt)
        
        run.l15_output = await self.research_runner.run_synthesis(
            l15_prompt, 
            model="claude-opus-4-6"  # Use best model for consolidation
        )
        run.tension_points = self.parse_tension_points(run.l15_output)
        run.status = "l15_complete"
        
        # === L2: Targeted Deep Dives ===
        print(f"[L2] Generating targeted research prompts...")
        l2_gen_prompt = self.prompt_builder.build_l2_generation(
            company_name=company_name,
            tension_points=run.tension_points,
            n_agents=min(12, len(run.tension_points))
        )
        l2_gen_response = await self.research_runner.run_synthesis(l2_gen_prompt)
        run.l2_prompts = self.parse_agent_prompts(l2_gen_response)
        
        print(f"[L2] Running {len(run.l2_prompts)} deep dives in parallel...")
        l2_results = await self.run_parallel_research(run.l2_prompts)
        run.l2_outputs = l2_results
        run.status = "l2_complete"
        
        # === L3: Final Synthesis ===
        print(f"[L3] Producing final report...")
        l3_prompt = self.prompt_builder.build_l3(
            company_name=company_name,
            all_outputs=self.context_manager.assemble_l3_input(run)
        )
        l3_response = await self.research_runner.run_synthesis(
            l3_prompt,
            model="claude-opus-4-6"
        )
        run.l3_executive_briefing = self.extract_executive_briefing(l3_response)
        run.l3_full_report = self.extract_full_report(l3_response)
        run.status = "complete"
        
        # === Save outputs ===
        self.save_run(run)
        
        return run
```

---

## Configuration

```python
# config.py

class Config:
    # API
    anthropic_api_key: str
    
    # Model selection
    research_model: str = "claude-sonnet-4-5-20250929"  # For web search tasks
    synthesis_model: str = "claude-opus-4-6"            # For reasoning tasks
    
    # Research parameters
    max_search_rounds: int = 5        # Iterative search rounds per task
    searches_per_round: int = 10      # Web searches per round
    max_concurrent_tasks: int = 5     # Parallel task limit (API rate limits)
    
    # Context window
    max_context_tokens: int = 180000  # Leave headroom from 200k limit
    
    # Agent counts
    min_l1_agents: int = 6
    max_l1_agents: int = 10
    min_l2_agents: int = 6
    max_l2_agents: int = 12
    
    # Cost controls
    max_total_cost_usd: float = 150.0  # Hard stop
    warn_cost_usd: float = 80.0        # Log warning
    
    # Output
    output_dir: str = "outputs"
    output_format: str = "markdown"  # markdown, pdf, docx
```

---

## Error Handling & Resilience

```python
# Key error scenarios and handling:

# 1. API rate limits
# → Implement exponential backoff with jitter
# → Reduce concurrency dynamically

# 2. Research task produces low-quality output
# → Implement quality checks (minimum word count, presence of required sections)
# → Re-run with modified prompt if quality check fails (max 2 retries)

# 3. Context window overflow at L1.5 or L3
# → Automatically compress using summarization
# → Log warning about potential quality loss

# 4. L0 produces insufficient profile
# → Check for minimum required sections
# → If critical sections missing, run supplementary L0 search

# 5. Cost exceeds budget
# → Track cumulative cost throughout pipeline
# → Halt gracefully with partial outputs if budget exceeded
```

---

## Quality Assurance

Implement automated quality checks at each layer:

```python
class QualityChecker:
    
    def check_l0(self, output: str) -> QualityReport:
        """Verify L0 profile has required sections and specificity."""
        checks = {
            "has_segments": "Business Model" in output or "segment" in output.lower(),
            "has_financials": bool(re.search(r'\$[\d,]+|£[\d,]+|revenue', output.lower())),
            "has_geographies": any(country in output for country in COUNTRY_LIST),
            "has_competitors": "competitor" in output.lower() or "compete" in output.lower(),
            "has_facilities": any(word in output.lower() for word in ["facility", "plant", "factory", "office", "warehouse", "estate"]),
            "min_length": len(output.split()) > 2000,
            "has_data_gaps": "[DATA GAP" in output,
            "has_recommendations": "Research Agent Recommendations" in output or "recommend" in output.lower(),
        }
        return QualityReport(checks=checks, pass_rate=sum(checks.values()) / len(checks))
    
    def check_l1(self, output: str, agent_type: str) -> QualityReport:
        """Verify L1 output has required depth and anomaly section."""
        checks = {
            "min_length": len(output.split()) > 1500,
            "has_specifics": bool(re.search(r'\d+', output)),  # Contains numbers
            "has_anomalies": "ANOMAL" in output.upper() or "NOTABLE" in output.upper(),
            "has_sources": bool(re.search(r'(source|report|filing|according)', output.lower())),
        }
        return QualityReport(checks=checks, pass_rate=sum(checks.values()) / len(checks))
    
    def check_l15(self, output: str) -> QualityReport:
        """Verify consolidation has required tension points."""
        checks = {
            "has_situation_map": "SITUATION" in output.upper() or "COMPANY MAP" in output.upper(),
            "has_tension_points": "TENSION" in output.upper(),
            "min_tension_count": output.upper().count("TENSION POINT") >= 10 or output.upper().count("HYPOTHESIS") >= 10,
            "has_categories": any(cat in output.upper() for cat in ["OFFENSIVE", "DEFENSIVE", "STRUCTURAL", "INFORMATION ARBITRAGE"]),
            "has_l2_questions": "LAYER 2" in output.upper() or "L2" in output.upper() or "RESEARCH QUESTION" in output.upper(),
            "has_magnitudes": any(mag in output.upper() for mag in ["TRANSFORMATIONAL", "MAJOR", "MODERATE"]),
        }
        return QualityReport(checks=checks, pass_rate=sum(checks.values()) / len(checks))
```

---

## Observability & Logging

Log everything for debugging and quality improvement:

```python
# For each research task, log:
{
    "task_id": "l1_agent_03",
    "prompt_tokens": 1500,
    "output_tokens": 8000,
    "thinking_tokens": 5000,
    "search_count": 18,
    "execution_time_seconds": 340,
    "estimated_cost_usd": 2.50,
    "quality_score": 0.85,
    "retry_count": 0,
    "sources_found": ["company_annual_report_2024.pdf", "reuters_article_2025-01-15", ...]
}
```

---

## CLI Interface

```bash
# Basic usage
python -m deep_research "Camellia Plc"

# With context
python -m deep_research "Camellia Plc" --context "UK-listed agri-conglomerate, focus on near-term opportunities"

# Resume from checkpoint
python -m deep_research --resume run_abc123

# Specific layer only (for debugging)
python -m deep_research "Camellia Plc" --start-from l1 --l0-output outputs/run_abc123/l0_profile.md

# Cost limit
python -m deep_research "Camellia Plc" --max-cost 100

# Output format
python -m deep_research "Camellia Plc" --format pdf
```
