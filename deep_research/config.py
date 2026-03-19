"""Configuration for the deep research system."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


# Pricing per 1K tokens (update as prices change)
PRICING = {
    "claude-sonnet-4-5-20250929": {
        "input_per_1k": 0.003,
        "output_per_1k": 0.015,
    },
    "claude-sonnet-4-6": {
        "input_per_1k": 0.003,
        "output_per_1k": 0.015,
    },
    "claude-opus-4-6": {
        "input_per_1k": 0.005,
        "output_per_1k": 0.025,
    },
    "claude-haiku-4-5-20251001": {
        "input_per_1k": 0.0008,
        "output_per_1k": 0.004,
    },
}

# Rough cost per web search tool use
SEARCH_COST_ESTIMATE = 0.01


@dataclass
class Config:
    """Configuration for a deep research run."""

    # Pipeline mode: "strategic_briefing" (exec/consulting) or "situation_assessment" (banking/deal)
    pipeline_mode: str = "strategic_briefing"

    # API
    anthropic_api_key: str = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", "")
    )

    # Model selection
    research_model: str = "claude-sonnet-4-6"  # For web search tasks
    synthesis_model: str = "claude-opus-4-6"  # For reasoning tasks

    # Research parameters
    max_search_rounds: int = 3  # Iterative: search → identify gaps → search again
    searches_per_round: int = 20  # Max web searches per round
    max_concurrent_tasks: int = 4  # Parallel task limit (API rate limits)

    # Thinking budgets
    research_thinking_budget: int = 10000
    synthesis_thinking_budget: int = 32000

    # Max output tokens (must be > thinking budget)
    # With extended thinking enabled, max_tokens is the TOTAL budget (thinking + text).
    # At 16K with 10K thinking budget, the model only gets ~6K tokens for text output.
    # Increasing to 32K gives ~22K text tokens after thinking — enough for thorough analysis.
    research_max_tokens: int = 32000
    synthesis_max_tokens: int = 64000

    # Context window
    max_context_tokens: int = 150000  # Conservative: tiktoken underestimates ~14% vs Anthropic tokenizer

    # Agent counts
    min_l1_agents: int = 6
    max_l1_agents: int = 8
    min_l2_agents: int = 6
    max_l2_agents: int = 8

    # Gap-fill (L1.5 re-run after supplementary research)
    # Gap-fill agents investigate blind spots identified by L1.5 consolidation,
    # typically surfacing cross-industry analogues and structural insights that
    # the initial L1 agents miss. High ROI per dollar spent.
    enable_gap_fill: bool = True
    max_gap_fill_agents: int = 2

    # Cost controls
    # With Opus pricing corrected (was 3x overstated), a full L0→L4d run costs ~$100-130 actual.
    # Budget set to $200 to give headroom for quality retries and L4 full report generation.
    max_total_cost_usd: float = 200.0  # Hard stop
    warn_cost_usd: float = 150.0  # Log warning

    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)

    @property
    def prompts_dir(self) -> Path:
        return self.project_root / "prompts" / self.pipeline_mode

    @property
    def calibration_dir(self) -> Path:
        return self.prompts_dir / "calibration_examples"

    @property
    def output_dir(self) -> Path:
        return self.project_root / "outputs"

    @property
    def examples_dir(self) -> Path:
        return self.project_root / "examples"

    # Output format
    output_format: str = "markdown"  # markdown, pdf, docx

    # Quality thresholds
    l0_min_pass_rate: float = 0.6
    l1_min_pass_rate: float = 0.5
    l15_min_pass_rate: float = 0.5
    max_retries: int = 2

    def validate(self) -> list[str]:
        """Check configuration validity, return list of issues."""
        issues = []
        if not self.anthropic_api_key:
            issues.append("ANTHROPIC_API_KEY not set")
        if not self.prompts_dir.exists():
            issues.append(f"Prompts directory not found: {self.prompts_dir}")
        return issues

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int,
                      search_count: int = 0) -> float:
        """Estimate cost for an API call."""
        pricing = PRICING.get(model, PRICING["claude-sonnet-4-6"])
        cost = (
            (input_tokens / 1000) * pricing["input_per_1k"]
            + (output_tokens / 1000) * pricing["output_per_1k"]
            + search_count * SEARCH_COST_ESTIMATE
        )
        return round(cost, 4)
