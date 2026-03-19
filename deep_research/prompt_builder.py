"""Prompt builder — loads templates, substitutes variables, selects calibration examples."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from .config import Config
from .context_manager import (
    assemble_l1_outputs,
    assemble_l1_manifest,
    assemble_l3_input,
    assemble_l2_summaries,
    assemble_l4b_sources,
    assemble_l4b_all_outputs,
)
from .models import CompanyArchetype, ResearchRun

logger = logging.getLogger(__name__)

# Mapping from CompanyArchetype to calibration example file (strategic_briefing mode)
ARCHETYPE_TO_CALIBRATION = {
    CompanyArchetype.MANUFACTURER: "manufacturer.md",
    CompanyArchetype.EXTRACTOR_GROWER: "manufacturer.md",
    CompanyArchetype.RETAILER_DISTRIBUTOR: "retailer.md",
    CompanyArchetype.PLATFORM_MARKETPLACE: "saas.md",
    CompanyArchetype.SAAS_SOFTWARE: "saas.md",
    CompanyArchetype.FINANCIAL_SERVICES: "financial_services.md",
    CompanyArchetype.INFRASTRUCTURE_UTILITIES: "infrastructure.md",
    CompanyArchetype.PROFESSIONAL_SERVICES: "manufacturer.md",
    CompanyArchetype.CONGLOMERATE: "conglomerate.md",
    CompanyArchetype.HEALTHCARE_PHARMA: "healthcare.md",
    CompanyArchetype.MEDIA_ENTERTAINMENT: "manufacturer.md",
    CompanyArchetype.REAL_ESTATE: "manufacturer.md",
    CompanyArchetype.OTHER: "manufacturer.md",
}

# Mapping for situation_assessment mode
SA_ARCHETYPE_TO_CALIBRATION = {
    CompanyArchetype.HEALTHCARE_PHARMA: "healthcare_services.md",
    CompanyArchetype.SAAS_SOFTWARE: "application_software.md",
    CompanyArchetype.PLATFORM_MARKETPLACE: "application_software.md",
    CompanyArchetype.PROFESSIONAL_SERVICES: "business_services.md",
    CompanyArchetype.RETAILER_DISTRIBUTOR: "business_services.md",
    CompanyArchetype.FINANCIAL_SERVICES: "business_services.md",
    # Energy/industrial archetypes → energy_technology calibration examples
    # (Plug Power examples are far more relevant than business services for these)
    CompanyArchetype.MANUFACTURER: "energy_technology.md",
    CompanyArchetype.EXTRACTOR_GROWER: "energy_technology.md",
    CompanyArchetype.INFRASTRUCTURE_UTILITIES: "energy_technology.md",
    # Remaining archetypes default to business_services until dedicated files are created
    CompanyArchetype.CONGLOMERATE: "business_services.md",
    CompanyArchetype.MEDIA_ENTERTAINMENT: "business_services.md",
    CompanyArchetype.REAL_ESTATE: "business_services.md",
    CompanyArchetype.OTHER: "business_services.md",
}


class PromptBuilder:
    """Loads prompt templates and substitutes variables."""

    def __init__(self, config: Config):
        self.config = config
        self.prompts_dir = config.prompts_dir
        self.calibration_dir = config.calibration_dir

    def _load_template(self, name: str) -> str:
        """Load a prompt template file."""
        path = self.prompts_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Prompt template not found: {path}")
        return path.read_text()

    def _load_calibration(self, archetype: CompanyArchetype | None) -> str:
        """Load calibration examples for the given archetype."""
        if self.config.pipeline_mode == "situation_assessment":
            calibration_map = SA_ARCHETYPE_TO_CALIBRATION
            default_file = "business_services.md"
        else:
            calibration_map = ARCHETYPE_TO_CALIBRATION
            default_file = "manufacturer.md"

        if archetype is None:
            filename = default_file
        else:
            filename = calibration_map.get(archetype, default_file)

        path = self.calibration_dir / filename
        if not path.exists():
            logger.warning(f"Calibration file not found: {path}, using {default_file}")
            path = self.calibration_dir / default_file
        if not path.exists():
            logger.error("No calibration examples found!")
            return ""
        return path.read_text()

    def build_l0(
        self,
        company_name: str,
        user_context: str | None = None,
        sector: str | None = None,
        sub_sector_focus: str | None = None,
        target_bank: str | None = None,
    ) -> str:
        """Build the L0 company profiling prompt."""
        template = self._load_template("l0_company_profile.md")

        context_parts = []
        if user_context:
            context_parts.append(f"Additional context from the requester: {user_context}")
        if sector:
            context_parts.append(f"Sector context: {sector}")
        if sub_sector_focus:
            context_parts.append(f"Sub-sector focus: {sub_sector_focus}")
        if target_bank:
            context_parts.append(f"This analysis is being prepared for: {target_bank}")

        context_text = "\n".join(context_parts)

        prompt = template.replace("{COMPANY_NAME}", company_name)
        prompt = prompt.replace("{OPTIONAL_USER_CONTEXT}", context_text)
        return prompt

    def build_l05(self, l0_output: str) -> str:
        """Build the L0.5 agent design prompt."""
        template = self._load_template("l05_agent_design.md")
        return template.replace("{L0_OUTPUT}", l0_output)

    def build_l15(
        self,
        company_name: str,
        n_agents: int,
        archetype: CompanyArchetype | None,
        l1_outputs: list,
    ) -> str:
        """Build the L1.5 consolidation prompt."""
        template = self._load_template("l15_consolidation.md")
        calibration = self._load_calibration(archetype)

        all_l1_text = assemble_l1_outputs(l1_outputs)

        # Map archetype to display name for the classification challenge
        archetype_display = archetype.value.upper().replace("_", "/") if archetype else "UNKNOWN"

        prompt = template.replace("{COMPANY_NAME}", company_name)
        prompt = prompt.replace("{N_AGENTS}", str(n_agents))
        prompt = prompt.replace("{ARCHETYPE}", archetype_display)
        prompt = prompt.replace("{CALIBRATION_EXAMPLES}", calibration)
        prompt = prompt.replace("{ALL_L1_OUTPUTS}", all_l1_text)
        return prompt

    def build_l2_generation(
        self,
        company_name: str,
        l15_tension_points: str,
        n_agents: int,
    ) -> str:
        """Build the L2 prompt generation prompt."""
        template = self._load_template("l2_generation.md")

        prompt = template.replace("{COMPANY_NAME}", company_name)
        prompt = prompt.replace("{N_L2_AGENTS}", str(n_agents))
        prompt = prompt.replace("{L15_TENSION_POINTS}", l15_tension_points)
        return prompt

    def build_l3a(self, company_name: str, run: ResearchRun) -> str:
        """Build the L3a synthesis prompt."""
        template = self._load_template("l3a_synthesis.md")

        all_outputs = assemble_l3_input(run, self.config.max_context_tokens)
        now = datetime.now()

        prompt = template.replace("{COMPANY_NAME}", company_name)
        prompt = prompt.replace("{N_L1_AGENTS}", str(len(run.l1_outputs)))
        prompt = prompt.replace("{N_TENSION_POINTS}", str(len(run.tension_points)))
        prompt = prompt.replace("{N_L2_AGENTS}", str(len(run.l2_outputs)))
        prompt = prompt.replace("{ALL_OUTPUTS}", all_outputs)
        # Substitute date placeholders so the cover page shows the correct month/year
        prompt = prompt.replace("{CURRENT_MONTH}", now.strftime("%B"))
        prompt = prompt.replace("{CURRENT_YEAR}", str(now.year))
        return prompt

    def build_l3b(self, company_name: str, run: ResearchRun, l3a_output: str) -> str:
        """Build the L3b refinement prompt."""
        template = self._load_template("l3b_refinement.md")

        all_outputs = assemble_l3_input(run, self.config.max_context_tokens)

        prompt = template.replace("{COMPANY_NAME}", company_name)
        prompt = prompt.replace("{L3A_OUTPUT}", l3a_output)
        prompt = prompt.replace("{ALL_OUTPUTS}", all_outputs)
        return prompt

    # ── L4 Full Report Pipeline ─────────────────────────────────────────

    def build_l4a(self, company_name: str, run: ResearchRun) -> str:
        """Build the L4a report architect prompt.

        Input: L3b teaser + L0 + L1.5 + L2 summaries (~600 words each).
        Output: Style guide + section assignments + assembly notes.
        """
        template = self._load_template("l4a_report_architect.md")
        l2_summaries = assemble_l2_summaries(run.l2_outputs)
        l1_manifest = assemble_l1_manifest(run.l1_outputs)

        prompt = template.replace("{COMPANY_NAME}", company_name)
        prompt = prompt.replace("{N_TENSION_POINTS}", str(len(run.tension_points)))
        prompt = prompt.replace("{L3B_OUTPUT}", run.l3b_final or "")
        prompt = prompt.replace("{L0_OUTPUT}", run.l0_output or "")
        prompt = prompt.replace("{L15_OUTPUT}", run.l15_output or "")
        prompt = prompt.replace("{L1_MANIFEST}", l1_manifest)
        prompt = prompt.replace("{L2_SUMMARIES}", l2_summaries)
        return prompt

    def build_l4b(
        self,
        company_name: str,
        run: ResearchRun,
        task_name: str,
        section_reference: str,
        section_brief: str,
        style_guide: str,
        full_outline: str,
        section_requirements: str,
        section_connections: str,
        target_length: str,
        source_agent_names: list[str],
        include_l3b: bool = False,
        include_l0: bool = True,
        include_l15: bool = True,
    ) -> str:
        """Build a single L4b section writer prompt.

        Each section writer gets: the template + style guide + outline + its brief +
        its assigned source documents (specific L1/L2 agents + optionally L0, L1.5, L3b).
        """
        template = self._load_template("l4b_section_writer.md")

        assigned_sources = assemble_l4b_sources(
            run,
            source_agent_names,
            include_l0=include_l0,
            include_l15=include_l15,
            include_l3b=include_l3b,
        )

        prompt = template.replace("{COMPANY_NAME}", company_name)
        prompt = prompt.replace("{SECTION_TITLE}", task_name)
        prompt = prompt.replace("{SECTION_REFERENCE}", section_reference)
        prompt = prompt.replace("{SECTION_BRIEF}", section_brief)
        prompt = prompt.replace("{STYLE_GUIDE}", style_guide)
        prompt = prompt.replace("{FULL_OUTLINE}", full_outline)
        prompt = prompt.replace("{SECTION_REQUIREMENTS}", section_requirements)
        prompt = prompt.replace("{SECTION_CONNECTIONS}", section_connections)
        prompt = prompt.replace("{TARGET_LENGTH}", target_length)
        prompt = prompt.replace("{ASSIGNED_SOURCES}", assigned_sources)
        return prompt

    def build_l4c(
        self,
        company_name: str,
        run: ResearchRun,
        style_guide: str,
        full_outline: str,
    ) -> str:
        """Build the L4c editorial review prompt.

        Input: All L4b section outputs + style guide + outline + L1.5 (for fact-checking).
        Output: Editorial memo with per-section notes.
        """
        template = self._load_template("l4c_editorial_review.md")
        all_section_outputs = assemble_l4b_all_outputs(run.l4b_outputs)

        prompt = template.replace("{COMPANY_NAME}", company_name)
        prompt = prompt.replace("{N_SECTIONS}", str(len(run.l4b_outputs)))
        prompt = prompt.replace("{STYLE_GUIDE}", style_guide)
        prompt = prompt.replace("{FULL_OUTLINE}", full_outline)
        prompt = prompt.replace("{L15_OUTPUT}", run.l15_output or "")
        prompt = prompt.replace("{ALL_SECTION_OUTPUTS}", all_section_outputs)
        return prompt

    def build_l4d(
        self,
        company_name: str,
        task_name: str,
        section_reference: str,
        style_guide: str,
        global_notes: str,
        section_notes: str,
        cross_section_notes: str,
        current_section_text: str,
    ) -> str:
        """Build a single L4d section revision prompt.

        Each revision agent gets: its section text + editorial notes + style guide.
        """
        template = self._load_template("l4d_section_revision.md")

        prompt = template.replace("{COMPANY_NAME}", company_name)
        prompt = prompt.replace("{SECTION_TITLE}", task_name)
        prompt = prompt.replace("{SECTION_REFERENCE}", section_reference)
        prompt = prompt.replace("{STYLE_GUIDE}", style_guide)
        prompt = prompt.replace("{GLOBAL_NOTES}", global_notes)
        prompt = prompt.replace("{SECTION_NOTES}", section_notes)
        prompt = prompt.replace("{CROSS_SECTION_NOTES}", cross_section_notes)
        prompt = prompt.replace("{CURRENT_SECTION_TEXT}", current_section_text)
        return prompt
