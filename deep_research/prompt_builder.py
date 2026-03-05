"""Prompt builder — loads templates, substitutes variables, selects calibration examples."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import Config
from .context_manager import assemble_l1_outputs, assemble_l3_input
from .models import CompanyArchetype, ResearchRun

logger = logging.getLogger(__name__)

# Mapping from CompanyArchetype to calibration example file
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
        if archetype is None:
            filename = "manufacturer.md"
        else:
            filename = ARCHETYPE_TO_CALIBRATION.get(archetype, "manufacturer.md")

        path = self.calibration_dir / filename
        if not path.exists():
            logger.warning(f"Calibration file not found: {path}, using manufacturer.md")
            path = self.calibration_dir / "manufacturer.md"
        if not path.exists():
            logger.error("No calibration examples found!")
            return ""
        return path.read_text()

    def build_l0(self, company_name: str, user_context: str | None = None) -> str:
        """Build the L0 company profiling prompt."""
        template = self._load_template("l0_company_profile.md")

        context_text = ""
        if user_context:
            context_text = f"Additional context from the requester: {user_context}"

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

    def build_l3(self, company_name: str, run: ResearchRun) -> str:
        """Build the L3 final synthesis prompt."""
        template = self._load_template("l3_final_synthesis.md")

        all_outputs = assemble_l3_input(run, self.config.max_context_tokens)

        prompt = template.replace("{COMPANY_NAME}", company_name)
        prompt = prompt.replace("{N_L1_AGENTS}", str(len(run.l1_outputs)))
        prompt = prompt.replace("{N_TENSION_POINTS}", str(len(run.tension_points)))
        prompt = prompt.replace("{N_L2_AGENTS}", str(len(run.l2_outputs)))
        prompt = prompt.replace("{ALL_OUTPUTS}", all_outputs)
        return prompt
