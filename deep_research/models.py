"""Data models for the deep research system."""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


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


class LayerStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


# Map of valid layer progression
LAYER_ORDER = ["l0", "l05", "l1", "l15", "l2", "l3"]

LAYER_DISPLAY_NAMES = {
    "l0": "L0: Company Profile",
    "l05": "L0.5: Agent Design",
    "l1": "L1: Parallel Research",
    "l15": "L1.5: Consolidation",
    "l2": "L2: Targeted Deep Dives",
    "l3": "L3: Final Synthesis",
}


class CostRecord(BaseModel):
    """Cost tracking for a single API call."""
    task_id: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    search_count: int = 0
    estimated_cost_usd: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentOutput(BaseModel):
    """Output from a single research agent."""
    agent_name: str
    agent_type: str  # l1 or l2
    prompt: str
    raw_output: str
    token_count: int = 0
    search_count: int = 0
    execution_time_seconds: float = 0.0
    cost_usd: float = 0.0
    sources_cited: list[str] = Field(default_factory=list)


class TensionPoint(BaseModel):
    """A strategic tension point identified in L1.5."""
    id: int
    title: str
    tension: str = ""
    hypothesis: str = ""
    category: str = ""  # Using str for flexibility in parsing
    magnitude: str = ""
    time_horizon: str = ""
    confidence: str = ""
    l2_research_question: str = ""
    l2_investigated: bool = False
    l2_output: str | None = None
    final_confidence: str | None = None
    included_in_executive_briefing: bool = False


class QualityReport(BaseModel):
    """Results of a quality check on layer output."""
    layer: str
    checks: dict[str, bool] = Field(default_factory=dict)
    pass_rate: float = 0.0
    passed: bool = False
    details: str = ""


class ResearchRun(BaseModel):
    """Top-level container for an entire research project."""
    id: str
    company_name: str
    company_ticker: str | None = None
    user_context: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: str = "pending"  # Current layer status
    current_layer: str = "l0"  # Which layer we're on or completed through

    # L0
    l0_output: str | None = None
    company_archetype: CompanyArchetype | None = None

    # L0.5
    l05_output: str | None = None
    l1_prompts: list[str] = Field(default_factory=list)
    l1_prompt_names: list[str] = Field(default_factory=list)

    # L1
    l1_outputs: list[AgentOutput] = Field(default_factory=list)

    # L1.5
    l15_output: str | None = None
    tension_points: list[TensionPoint] = Field(default_factory=list)
    gap_fill_agents: list[AgentOutput] = Field(default_factory=list)
    l15_rerun: bool = False

    # L2
    l2_prompts: list[str] = Field(default_factory=list)
    l2_prompt_names: list[str] = Field(default_factory=list)
    l2_outputs: list[AgentOutput] = Field(default_factory=list)

    # L3
    l3_executive_briefing: str | None = None
    l3_full_report: str | None = None

    # Cost tracking
    cost_records: list[CostRecord] = Field(default_factory=list)
    total_cost_usd: float = 0.0

    # Quality
    quality_reports: list[QualityReport] = Field(default_factory=list)

    def next_layer(self) -> str | None:
        """Return the next layer to run, or None if complete."""
        try:
            idx = LAYER_ORDER.index(self.current_layer)
            if self.status in ("complete", "l0_complete", "l05_complete",
                               "l1_complete", "l15_complete", "l2_complete"):
                if idx + 1 < len(LAYER_ORDER):
                    return LAYER_ORDER[idx + 1]
                return None
            return self.current_layer
        except ValueError:
            return "l0"

    def completed_layer(self) -> str | None:
        """Return the most recently completed layer."""
        status_to_layer = {
            "l0_complete": "l0",
            "l05_complete": "l05",
            "l1_complete": "l1",
            "l15_complete": "l15",
            "l2_complete": "l2",
            "complete": "l3",
        }
        return status_to_layer.get(self.status)

    def save(self, output_dir: Path) -> None:
        """Save run state and individual outputs to the run directory."""
        run_dir = output_dir / self.id
        run_dir.mkdir(parents=True, exist_ok=True)

        self.updated_at = datetime.now()

        # Save full state
        state_path = run_dir / "run_state.json"
        state_path.write_text(self.model_dump_json(indent=2))

        # Save individual outputs as markdown for easy inspection
        if self.l0_output:
            (run_dir / "l0_profile.md").write_text(self.l0_output)

        if self.l05_output:
            (run_dir / "l05_agent_design.md").write_text(self.l05_output)

        # L1 prompts
        if self.l1_prompts:
            prompts_dir = run_dir / "l1_prompts"
            prompts_dir.mkdir(exist_ok=True)
            for i, (prompt, name) in enumerate(
                zip(self.l1_prompts, self.l1_prompt_names or [f"agent_{i+1:02d}" for i in range(len(self.l1_prompts))])
            ):
                safe_name = _safe_filename(name)
                (prompts_dir / f"{i+1:02d}_{safe_name}.md").write_text(prompt)

        # L1 outputs
        if self.l1_outputs:
            outputs_dir = run_dir / "l1_outputs"
            outputs_dir.mkdir(exist_ok=True)
            for i, output in enumerate(self.l1_outputs):
                safe_name = _safe_filename(output.agent_name)
                (outputs_dir / f"{i+1:02d}_{safe_name}.md").write_text(output.raw_output)

        if self.l15_output:
            (run_dir / "l15_consolidation.md").write_text(self.l15_output)

        # L2 prompts
        if self.l2_prompts:
            prompts_dir = run_dir / "l2_prompts"
            prompts_dir.mkdir(exist_ok=True)
            for i, (prompt, name) in enumerate(
                zip(self.l2_prompts, self.l2_prompt_names or [f"dive_{i+1:02d}" for i in range(len(self.l2_prompts))])
            ):
                safe_name = _safe_filename(name)
                (prompts_dir / f"{i+1:02d}_{safe_name}.md").write_text(prompt)

        # L2 outputs
        if self.l2_outputs:
            outputs_dir = run_dir / "l2_outputs"
            outputs_dir.mkdir(exist_ok=True)
            for i, output in enumerate(self.l2_outputs):
                safe_name = _safe_filename(output.agent_name)
                (outputs_dir / f"{i+1:02d}_{safe_name}.md").write_text(output.raw_output)

        if self.l3_executive_briefing:
            (run_dir / "l3_executive_briefing.md").write_text(self.l3_executive_briefing)

        if self.l3_full_report:
            (run_dir / "l3_full_report.md").write_text(self.l3_full_report)

        # Cost log
        if self.cost_records:
            cost_data = [r.model_dump(mode="json") for r in self.cost_records]
            (run_dir / "cost_log.json").write_text(json.dumps(cost_data, indent=2, default=str))

    @classmethod
    def load(cls, output_dir: Path, run_id: str) -> ResearchRun:
        """Load a run from its state file."""
        state_path = output_dir / run_id / "run_state.json"
        if not state_path.exists():
            raise FileNotFoundError(f"No run found at {state_path}")
        return cls.model_validate_json(state_path.read_text())


def _safe_filename(name: str) -> str:
    """Convert a name to a safe filename."""
    import re
    safe = re.sub(r'[^\w\s-]', '', name.lower())
    safe = re.sub(r'[\s]+', '_', safe)
    return safe[:60]
