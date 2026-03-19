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
LAYER_ORDER = ["l0", "l05", "l1", "l15", "l2", "l3a_select", "l3a_write", "l3b", "l3c", "l3d", "l4a", "l4b", "l4c", "l4d"]

LAYER_DISPLAY_NAMES = {
    "l0": "L0: Company Profile",
    "l05": "L0.5: Agent Design",
    "l1": "L1: Parallel Research",
    "l15": "L1.5: Consolidation",
    "l2": "L2: Targeted Deep Dives",
    "l3a_select": "L3a-Select: Finding Selection",
    "l3a_write": "L3a-Write: Synthesis Draft",
    "l3b": "L3b: Editorial Refinement",
    "l3c": "L3c: Coherency Audit",
    "l3d": "L3d: PDF Generation",
    "l4a": "L4a: Report Architect",
    "l4b": "L4b: Section Writers",
    "l4c": "L4c: Editorial Review",
    "l4d": "L4d: Section Revision",
}


class CostRecord(BaseModel):
    """Cost tracking for a single API call."""
    task_id: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0  # Not separately tracked by API; included in output_tokens
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
    yield_verdict: str = ""  # DROP / KEEP / HIGHLIGHT — parsed from L2 output's YIELD ASSESSMENT


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


class Critique(BaseModel):
    """Opus critique of a research agent's output.

    Replaces the old Haiku-based scoring system with actionable feedback
    that directs follow-up research rounds.
    """
    agent_name: str
    sufficient: bool = False  # Is the output usable as a working first draft?
    gaps: list[str] = Field(default_factory=list)  # Specific unanswered questions
    weak_claims: list[str] = Field(default_factory=list)  # Claims without evidence (quoted)
    missing_context: list[str] = Field(default_factory=list)  # Absent market/competitive/regulatory context
    follow_up_queries: list[str] = Field(default_factory=list)  # Literal search queries to fill gaps
    summary: str = ""  # One-line summary of the critique


class ResearchRun(BaseModel):
    """Top-level container for an entire research project."""
    id: str
    company_name: str
    company_ticker: str | None = None
    user_context: str | None = None

    # Pipeline mode
    pipeline_mode: str = "strategic_briefing"  # or "situation_assessment"

    # Situation Assessment specific inputs
    sector: str | None = None
    target_bank: str | None = None
    sub_sector_focus: str | None = None
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

    # L3a (split into selection + writing)
    l3a_select_output: str | None = None  # Full selection workbook (Steps 1-4, for audit/debugging)
    l3a_select_brief: str | None = None  # Writer brief only (after ===WRITER_BRIEF=== delimiter)
    l3a_draft: str | None = None  # Written synthesis draft (output of l3a_write)
    # L3b (editorial refinement)
    l3b_final: str | None = None
    # L3c (coherency audit — fact-checked and internally consistent version)
    l3c_output: str | None = None
    l3c_audit_log: str | None = None
    # L3d (PDF generation — stores relative path to generated PDF)
    l3d_pdf_path: str | None = None

    # L4a (report architect)
    l4a_output: str | None = None
    l4a_style_guide: str | None = None
    l4a_outline: str | None = None
    l4b_task_briefs: list[str] = Field(default_factory=list)
    l4b_task_names: list[str] = Field(default_factory=list)
    l4b_task_sections: list[str] = Field(default_factory=list)  # Which report section each task belongs to
    l4b_task_models: list[str] = Field(default_factory=list)  # "opus" or "sonnet" per task
    l4b_source_assignments: list[list[str]] = Field(default_factory=list)  # Agent names to include per task
    l4b_include_l0: list[bool] = Field(default_factory=list)  # Whether each task gets L0
    l4b_include_l15: list[bool] = Field(default_factory=list)  # Whether each task gets L1.5

    # L4b (section writer outputs)
    l4b_outputs: list[AgentOutput] = Field(default_factory=list)

    # L4c (editorial review)
    l4c_editorial_memo: str | None = None
    l4c_global_notes: str | None = None
    l4c_section_notes: list[str] = Field(default_factory=list)  # Per-section editorial notes

    # L4d (revised sections)
    l4d_outputs: list[AgentOutput] = Field(default_factory=list)
    l4_final_report: str | None = None  # Concatenated final report

    # Cost tracking
    cost_records: list[CostRecord] = Field(default_factory=list)
    total_cost_usd: float = 0.0

    # Quality
    quality_reports: list[QualityReport] = Field(default_factory=list)

    def next_layer(self) -> str | None:
        """Return the next layer to run, or None if complete."""
        try:
            idx = LAYER_ORDER.index(self.current_layer)
            completed_statuses = {
                "l0_complete", "l05_complete", "l1_complete", "l15_complete",
                "l2_complete", "l3a_select_complete", "l3a_write_complete",
                "l3a_complete",  # backward compat
                "l3b_complete", "l3c_complete",
                "l3d_complete", "l4a_complete", "l4b_complete", "l4c_complete",
                "complete",
            }
            if self.status in completed_statuses:
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
            "l3a_select_complete": "l3a_select",
            "l3a_write_complete": "l3a_write",
            "l3a_complete": "l3a_write",  # backward compat
            "l3b_complete": "l3b",
            "l3c_complete": "l3c",
            "l3d_complete": "l3d",
            "l4a_complete": "l4a",
            "l4b_complete": "l4b",
            "l4c_complete": "l4c",
            "complete": "l4d",
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

        # L1 outputs — use agent name as key (stable across save order)
        if self.l1_outputs:
            outputs_dir = run_dir / "l1_outputs"
            outputs_dir.mkdir(exist_ok=True)
            for output in self.l1_outputs:
                safe_name = _safe_filename(output.agent_name)
                (outputs_dir / f"{safe_name}.md").write_text(output.raw_output)

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

        # L2 outputs — use agent name as key (stable across save order)
        if self.l2_outputs:
            outputs_dir = run_dir / "l2_outputs"
            outputs_dir.mkdir(exist_ok=True)
            for output in self.l2_outputs:
                safe_name = _safe_filename(output.agent_name)
                (outputs_dir / f"{safe_name}.md").write_text(output.raw_output)

        if self.l3a_select_output:
            (run_dir / "l3a_select_brief.md").write_text(self.l3a_select_output)

        if self.l3a_draft:
            (run_dir / "l3a_draft.md").write_text(self.l3a_draft)

        if self.l3b_final:
            (run_dir / "l3b_final.md").write_text(self.l3b_final)

        # L3c coherency audit — this is the final document used for PDF generation
        if self.l3c_output:
            if self.pipeline_mode == "situation_assessment":
                (run_dir / "l3_deep_analysis.md").write_text(self.l3c_output)
            else:
                (run_dir / "l3_executive_briefing.md").write_text(self.l3c_output)
            if self.l3c_audit_log:
                (run_dir / "l3c_audit_log.md").write_text(self.l3c_audit_log)

        # L4a report architect
        if self.l4a_output:
            (run_dir / "l4a_report_architect.md").write_text(self.l4a_output)
        if self.l4a_style_guide:
            (run_dir / "l4a_style_guide.md").write_text(self.l4a_style_guide)

        # L4b section writer outputs
        if self.l4b_outputs:
            outputs_dir = run_dir / "l4b_sections"
            outputs_dir.mkdir(exist_ok=True)
            for output in self.l4b_outputs:
                safe_name = _safe_filename(output.agent_name)
                (outputs_dir / f"{safe_name}.md").write_text(output.raw_output)

        # L4c editorial review
        if self.l4c_editorial_memo:
            (run_dir / "l4c_editorial_memo.md").write_text(self.l4c_editorial_memo)

        # L4d revised sections
        if self.l4d_outputs:
            outputs_dir = run_dir / "l4d_revised_sections"
            outputs_dir.mkdir(exist_ok=True)
            for output in self.l4d_outputs:
                safe_name = _safe_filename(output.agent_name)
                (outputs_dir / f"{safe_name}.md").write_text(output.raw_output)

        # Final assembled report
        if self.l4_final_report:
            (run_dir / "l4_full_situation_assessment.md").write_text(self.l4_final_report)

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
        run = cls.model_validate_json(state_path.read_text())

        # Backward compat: older runs used "l3" instead of "l3a"/"l3b"
        if run.current_layer == "l3":
            run.current_layer = "l3b"
        if run.status == "l3_complete":
            run.status = "l3b_complete"

        # Backward compat: older runs used "l3a" as a single layer
        if run.current_layer == "l3a":
            run.current_layer = "l3a_write"
        if run.status == "l3a_complete":
            run.status = "l3a_write_complete"

        # Backward compat: if status is "complete" but current_layer is l3b,
        # update to l3b_complete so next_layer() returns l3c instead of None
        if run.status == "complete" and run.current_layer == "l3b":
            run.status = "l3b_complete"
        # Backward compat: if status is "complete" but current_layer is l3c,
        # update to l3c_complete so next_layer() returns l3d instead of None
        if run.status == "complete" and run.current_layer == "l3c":
            run.status = "l3c_complete"
        # Backward compat: if status is "complete" but current_layer is l3d,
        # update to l3d_complete so next_layer() returns l4a instead of None
        if run.status == "complete" and run.current_layer == "l3d":
            run.status = "l3d_complete"
        # Backward compat: old runs had l3c as PDF generation with l3c_pdf_path
        if hasattr(run, "l3c_pdf_path") and run.l3c_pdf_path and not run.l3d_pdf_path:
            run.l3d_pdf_path = run.l3c_pdf_path

        return run


def _safe_filename(name: str) -> str:
    """Convert a name to a safe filename."""
    import re
    safe = re.sub(r'[^\w\s-]', '', name.lower())
    safe = re.sub(r'[\s]+', '_', safe)
    return safe[:60]
