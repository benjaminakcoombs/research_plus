"""Orchestrator — runs the multi-layer research pipeline with stop/resume support."""

from __future__ import annotations

import asyncio
import logging
import re
import time
import uuid
from datetime import datetime
from pathlib import Path

from .config import Config
from .context_manager import count_tokens
from .models import (
    LAYER_ORDER,
    LAYER_DISPLAY_NAMES,
    AgentOutput,
    CompanyArchetype,
    ResearchRun,
    TensionPoint,
)
from .prompt_builder import PromptBuilder
from .quality_checker import QualityChecker
from .research_runner import BudgetExceededError, ResearchRunner

logger = logging.getLogger(__name__)


class DeepResearchOrchestrator:
    """Runs the multi-layer deep research pipeline.

    Supports:
    - Full pipeline execution (run_all)
    - Layer-by-layer execution (run_to)
    - Resume from checkpoint (load + run_to)
    """

    def __init__(self, config: Config):
        self.config = config
        self.prompt_builder = PromptBuilder(config)
        self.quality_checker = QualityChecker()
        self.runner: ResearchRunner | None = None

    def _ensure_runner(self) -> ResearchRunner:
        if self.runner is None:
            self.runner = ResearchRunner(self.config)
        return self.runner

    def _generate_run_id(self) -> str:
        short = uuid.uuid4().hex[:8]
        return f"run_{short}"

    # ── Layer execution methods ─────────────────────────────────────────

    async def run_l0(self, run: ResearchRun) -> ResearchRun:
        """L0: Company Profile — deep research with web search."""
        runner = self._ensure_runner()
        logger.info(f"[L0] Profiling {run.company_name}...")

        prompt = self.prompt_builder.build_l0(run.company_name, run.user_context)

        text, costs = await runner.run_research(prompt, task_id="l0_profile")
        run.l0_output = text
        run.cost_records.extend(costs)
        run.total_cost_usd = runner.total_cost

        # Quality check
        qr = self.quality_checker.check_l0(text)
        run.quality_reports.append(qr)

        if not qr.passed:
            logger.warning(f"[L0] Quality check failed ({qr.pass_rate:.0%}). Proceeding anyway.")

        # Extract archetype
        run.company_archetype = self._extract_archetype(text)
        logger.info(f"[L0] Detected archetype: {run.company_archetype}")

        run.status = "l0_complete"
        run.current_layer = "l0"
        return run

    async def run_l05(self, run: ResearchRun) -> ResearchRun:
        """L0.5: Agent Design — synthesis, no web search."""
        runner = self._ensure_runner()
        logger.info("[L0.5] Designing research agents...")

        if not run.l0_output:
            raise ValueError("Cannot run L0.5 without L0 output")

        prompt = self.prompt_builder.build_l05(run.l0_output)

        text, costs = await runner.run_synthesis(prompt, task_id="l05_design")
        run.l05_output = text
        run.cost_records.extend(costs)
        run.total_cost_usd = runner.total_cost

        # Quality check
        qr = self.quality_checker.check_l05(text)
        run.quality_reports.append(qr)

        # Parse agent prompts
        prompts, names = self._parse_agent_prompts(text)
        run.l1_prompts = prompts
        run.l1_prompt_names = names

        logger.info(f"[L0.5] Generated {len(prompts)} L1 agent prompts")
        for i, name in enumerate(names, 1):
            logger.info(f"  Agent {i}: {name}")

        run.status = "l05_complete"
        run.current_layer = "l05"
        return run

    async def run_l1(self, run: ResearchRun) -> ResearchRun:
        """L1: Research — runs each agent sequentially, saving after each."""
        runner = self._ensure_runner()

        if not run.l1_prompts:
            raise ValueError("Cannot run L1 without L1 prompts (run L0.5 first)")

        n = len(run.l1_prompts)
        cooldown = 10  # seconds between agents

        # Resume support: skip agents we already have outputs for
        start_from = len(run.l1_outputs)
        if start_from > 0:
            logger.info(f"[L1] Resuming from agent {start_from + 1}/{n} ({start_from} already done)")
        else:
            logger.info(f"[L1] Running {n} research agents sequentially...")

        for i in range(start_from, n):
            prompt = run.l1_prompts[i]
            name = run.l1_prompt_names[i]
            task_id = f"l1_agent_{i + 1:02d}"

            if i > start_from:
                logger.info(f"  [{task_id}] Cooling down {cooldown}s...")
                await asyncio.sleep(cooldown)

            logger.info(f"  [{task_id}] Starting: {name} ({i + 1}/{n})")
            start = time.time()
            agent_costs = []

            try:
                text, agent_costs = await runner.run_research(prompt=prompt, task_id=task_id)
                elapsed = time.time() - start
                total_cost = sum(c.estimated_cost_usd for c in agent_costs)
                search_count = sum(c.search_count for c in agent_costs)

                logger.info(
                    f"  [{task_id}] Complete: {name} "
                    f"({elapsed:.0f}s, ${total_cost:.2f}, {search_count} searches)"
                )

                output = AgentOutput(
                    agent_name=name,
                    agent_type="l1",
                    prompt=prompt,
                    raw_output=text,
                    token_count=sum(c.output_tokens for c in agent_costs),
                    search_count=search_count,
                    execution_time_seconds=elapsed,
                    cost_usd=total_cost,
                )
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"  [{task_id}] Failed: {name} ({elapsed:.0f}s): {e}")
                output = AgentOutput(
                    agent_name=name,
                    agent_type="l1",
                    prompt=prompt,
                    raw_output=f"[ERROR: Research task failed: {e}]",
                    execution_time_seconds=elapsed,
                )

            # Quality check
            qr = self.quality_checker.check_l1(output.raw_output, output.agent_name)
            run.quality_reports.append(qr)
            if not qr.passed:
                logger.warning(f"  [{task_id}] Quality check failed for '{name}'")

            # Append and save immediately
            run.l1_outputs.append(output)
            run.cost_records.extend(agent_costs)
            run.total_cost_usd = runner.total_cost
            run.save(self.config.output_dir)
            logger.info(f"  [{task_id}] Saved to disk ({i + 1}/{n} complete)")

        passed = sum(1 for o in run.l1_outputs if not o.raw_output.startswith("[ERROR"))
        logger.info(f"[L1] Complete: {passed}/{n} agents succeeded")

        run.status = "l1_complete"
        run.current_layer = "l1"
        return run

    async def run_l15(self, run: ResearchRun) -> ResearchRun:
        """L1.5: Consolidation — synthesis of all L1 outputs."""
        runner = self._ensure_runner()

        if not run.l1_outputs:
            raise ValueError("Cannot run L1.5 without L1 outputs")

        logger.info("[L1.5] Consolidating research outputs...")

        prompt = self.prompt_builder.build_l15(
            company_name=run.company_name,
            n_agents=len(run.l1_outputs),
            archetype=run.company_archetype,
            l1_outputs=run.l1_outputs,
        )

        # Check context window
        token_count = count_tokens(prompt)
        logger.info(f"[L1.5] Input size: {token_count} tokens")
        if token_count > self.config.max_context_tokens:
            logger.warning(
                f"[L1.5] Input ({token_count} tokens) exceeds limit "
                f"({self.config.max_context_tokens}). Content may be compressed."
            )

        text, costs = await runner.run_synthesis(
            prompt,
            task_id="l15_consolidation",
            model=self.config.synthesis_model,
        )

        run.l15_output = text
        run.cost_records.extend(costs)
        run.total_cost_usd = runner.total_cost

        # Quality check
        qr = self.quality_checker.check_l15(text)
        run.quality_reports.append(qr)

        # Parse tension points
        run.tension_points = self._parse_tension_points(text)
        logger.info(f"[L1.5] Identified {len(run.tension_points)} tension points")

        # Gap-fill: if research gaps identified and enabled, run supplementary agents
        if self.config.enable_gap_fill and not run.l15_rerun:
            gaps = self._extract_research_gaps(text)
            if gaps:
                logger.info(f"[L1.5] Found {len(gaps)} research gaps, generating gap-fill agents...")
                gap_prompts = await self._generate_gap_fill_prompts(gaps, run)
                if gap_prompts:
                    # Run gap-fill agents
                    cooldown = 10
                    for i, prompt in enumerate(gap_prompts):
                        task_id = f"l1_gap_{i + 1:02d}"
                        if i > 0:
                            logger.info(f"  [{task_id}] Cooling down {cooldown}s...")
                            await asyncio.sleep(cooldown)

                        logger.info(f"  [{task_id}] Running gap-fill agent {i + 1}/{len(gap_prompts)}")
                        start = time.time()
                        agent_gap_costs: list = []
                        try:
                            gap_text, agent_gap_costs = await runner.run_research(
                                prompt=prompt, task_id=task_id
                            )
                            elapsed = time.time() - start
                            total_cost = sum(c.estimated_cost_usd for c in agent_gap_costs)
                            search_count = sum(c.search_count for c in agent_gap_costs)

                            gap_output = AgentOutput(
                                agent_name=f"Gap Fill: {gaps[i][:60]}",
                                agent_type="l1",
                                prompt=prompt,
                                raw_output=gap_text,
                                token_count=sum(c.output_tokens for c in agent_gap_costs),
                                search_count=search_count,
                                execution_time_seconds=elapsed,
                                cost_usd=total_cost,
                            )
                        except Exception as e:
                            elapsed = time.time() - start
                            logger.error(f"  [{task_id}] Gap-fill failed: {e}")
                            gap_output = AgentOutput(
                                agent_name=f"Gap Fill: {gaps[i][:60]}",
                                agent_type="l1",
                                prompt=prompt,
                                raw_output=f"[ERROR: Gap-fill research failed: {e}]",
                                execution_time_seconds=elapsed,
                            )

                        run.gap_fill_agents.append(gap_output)
                        run.l1_outputs.append(gap_output)
                        run.cost_records.extend(agent_gap_costs)
                        run.total_cost_usd = runner.total_cost
                        run.save(self.config.output_dir)

                    # Re-run L1.5 consolidation with expanded corpus
                    logger.info("[L1.5] Re-running consolidation with gap-fill outputs...")
                    run.l15_rerun = True

                    prompt = self.prompt_builder.build_l15(
                        company_name=run.company_name,
                        n_agents=len(run.l1_outputs),
                        archetype=run.company_archetype,
                        l1_outputs=run.l1_outputs,
                    )

                    text, costs = await runner.run_synthesis(
                        prompt,
                        task_id="l15_consolidation_v2",
                        model=self.config.synthesis_model,
                    )

                    run.l15_output = text
                    run.cost_records.extend(costs)
                    run.total_cost_usd = runner.total_cost

                    # Re-check quality and re-parse tension points
                    qr = self.quality_checker.check_l15(text)
                    run.quality_reports.append(qr)
                    run.tension_points = self._parse_tension_points(text)
                    logger.info(
                        f"[L1.5] Re-consolidation complete: {len(run.tension_points)} tension points"
                    )

        run.status = "l15_complete"
        run.current_layer = "l15"
        return run

    async def run_l2(self, run: ResearchRun) -> ResearchRun:
        """L2: Generate targeted prompts then run deep dives in parallel."""
        runner = self._ensure_runner()

        if not run.l15_output:
            raise ValueError("Cannot run L2 without L1.5 output")

        # Step 1: Generate L2 prompts
        n_agents = min(self.config.max_l2_agents, max(len(run.tension_points), self.config.min_l2_agents))
        logger.info(f"[L2] Generating {n_agents} targeted research prompts...")

        # Extract tension points section from L1.5 output (Deliverable 2)
        tp_text = self._extract_tension_points_text(run.l15_output)

        gen_prompt = self.prompt_builder.build_l2_generation(
            company_name=run.company_name,
            l15_tension_points=tp_text,
            n_agents=n_agents,
        )

        gen_text, gen_costs = await runner.run_synthesis(
            gen_prompt,
            task_id="l2_generation",
        )
        run.cost_records.extend(gen_costs)
        run.total_cost_usd = runner.total_cost

        # Parse L2 prompts
        prompts, names = self._parse_l2_prompts(gen_text)
        run.l2_prompts = prompts
        run.l2_prompt_names = names

        logger.info(f"[L2] Generated {len(prompts)} L2 agent prompts")

        # Save state with prompts before running (so user can inspect)
        run.save(self.config.output_dir)

        # Step 2: Run L2 research sequentially, saving after each
        cooldown = 10
        start_from = len(run.l2_outputs)
        if start_from > 0:
            logger.info(f"[L2] Resuming from agent {start_from + 1}/{len(prompts)} ({start_from} already done)")
        else:
            logger.info(f"[L2] Running {len(prompts)} deep dives sequentially...")

        for i in range(start_from, len(prompts)):
            prompt = prompts[i]
            name = names[i]
            task_id = f"l2_agent_{i + 1:02d}"

            if i > start_from:
                logger.info(f"  [{task_id}] Cooling down {cooldown}s...")
                await asyncio.sleep(cooldown)

            logger.info(f"  [{task_id}] Starting: {name} ({i + 1}/{len(prompts)})")
            start = time.time()

            try:
                text, costs = await runner.run_research(prompt=prompt, task_id=task_id)
                elapsed = time.time() - start
                total_cost = sum(c.estimated_cost_usd for c in costs)
                search_count = sum(c.search_count for c in costs)

                logger.info(
                    f"  [{task_id}] Complete: {name} "
                    f"({elapsed:.0f}s, ${total_cost:.2f}, {search_count} searches)"
                )

                output = AgentOutput(
                    agent_name=name,
                    agent_type="l2",
                    prompt=prompt,
                    raw_output=text,
                    token_count=sum(c.output_tokens for c in costs),
                    search_count=search_count,
                    execution_time_seconds=elapsed,
                    cost_usd=total_cost,
                )
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"  [{task_id}] Failed: {name} ({elapsed:.0f}s): {e}")
                output = AgentOutput(
                    agent_name=name,
                    agent_type="l2",
                    prompt=prompt,
                    raw_output=f"[ERROR: Research task failed: {e}]",
                    execution_time_seconds=elapsed,
                )

            # Quality check
            qr = self.quality_checker.check_l2(output.raw_output, output.agent_name)
            run.quality_reports.append(qr)

            # Append and save immediately
            run.l2_outputs.append(output)
            run.total_cost_usd = runner.total_cost
            run.save(self.config.output_dir)
            logger.info(f"  [{task_id}] Saved to disk ({i + 1}/{len(prompts)} complete)")

        passed = sum(1 for o in run.l2_outputs if not o.raw_output.startswith("[ERROR"))
        logger.info(f"[L2] Complete: {passed}/{len(prompts)} agents succeeded")

        run.status = "l2_complete"
        run.current_layer = "l2"
        return run

    async def run_l3(self, run: ResearchRun) -> ResearchRun:
        """L3: Final Synthesis — produce executive briefing and full report."""
        runner = self._ensure_runner()

        if not run.l2_outputs:
            raise ValueError("Cannot run L3 without L2 outputs")

        logger.info("[L3] Producing final report...")

        prompt = self.prompt_builder.build_l3(
            company_name=run.company_name,
            run=run,
        )

        token_count = count_tokens(prompt)
        logger.info(f"[L3] Input size: {token_count} tokens")

        text, costs = await runner.run_synthesis(
            prompt,
            task_id="l3_synthesis",
            model=self.config.synthesis_model,
        )

        run.cost_records.extend(costs)
        run.total_cost_usd = runner.total_cost

        # Quality check
        qr = self.quality_checker.check_l3(text)
        run.quality_reports.append(qr)

        # Split into executive briefing and full report
        run.l3_executive_briefing, run.l3_full_report = self._split_l3_output(text)

        logger.info("[L3] Final synthesis complete")

        run.status = "complete"
        run.current_layer = "l3"
        return run

    # ── Gap-fill methods ──────────────────────────────────────────────

    def _extract_research_gaps(self, l15_output: str) -> list[str]:
        """Extract research gap descriptions from L1.5 Deliverable 3."""
        gaps = []

        # Look for RESEARCH GAPS section
        gap_section = re.search(
            r"RESEARCH\s+GAPS?\s*:?(.*?)(?=\n#{1,3}\s|\n===|\Z)",
            l15_output,
            re.IGNORECASE | re.DOTALL,
        )
        if not gap_section:
            return gaps

        section_text = gap_section.group(1)

        # Extract bullet items
        bullets = re.findall(r"[-*]\s+(.+?)(?=\n[-*]|\n\n|\Z)", section_text, re.DOTALL)
        for bullet in bullets:
            cleaned = bullet.strip()
            if len(cleaned) > 20:  # Skip trivially short items
                gaps.append(cleaned)

        return gaps[:self.config.max_gap_fill_agents]

    async def _generate_gap_fill_prompts(
        self, gaps: list[str], run: ResearchRun
    ) -> list[str]:
        """Generate 1-2 L1-style research prompts to fill identified gaps."""
        runner = self._ensure_runner()

        gap_descriptions = "\n".join(f"- {g}" for g in gaps)
        l0_summary = (run.l0_output or "")[:3000]  # Truncate for prompt size

        synthesis_prompt = f"""You are a research architect. Based on the research gaps identified below, write {len(gaps)} focused research agent prompt(s). Each prompt should be self-contained and suitable for a deep research agent with web access.

COMPANY: {run.company_name}

COMPANY PROFILE (abbreviated):
{l0_summary}

RESEARCH GAPS TO FILL:
{gap_descriptions}

For each gap, write a complete research prompt (300-800 words) that:
1. Assigns a specific expert persona
2. Provides enough company context to work independently
3. Asks specific, answerable research questions
4. Requires operational specificity and cited sources
5. Ends with a NOTABLE ANOMALIES section

Output each prompt in a code block, preceded by:
AGENT N: [descriptive name]

Write {len(gaps)} prompts total."""

        text, costs = await runner.run_synthesis(
            synthesis_prompt,
            task_id="gap_fill_generation",
        )
        run.cost_records.extend(costs)
        run.total_cost_usd = runner.total_cost

        # Parse prompts from code blocks
        code_blocks = re.findall(r"```(?:\w*\n)?(.*?)```", text, re.DOTALL)
        prompts = [b.strip() for b in code_blocks if len(b.strip()) > 100]

        logger.info(f"Generated {len(prompts)} gap-fill prompts")
        return prompts[:self.config.max_gap_fill_agents]

    # ── Pipeline control methods ────────────────────────────────────────

    async def run_to(
        self,
        run: ResearchRun,
        stop_after: str,
    ) -> ResearchRun:
        """Run the pipeline from the current state up to (and including) stop_after layer.

        Args:
            run: The research run (may be partially complete).
            stop_after: Layer to stop after (l0, l05, l1, l15, l2, l3).
        """
        if stop_after not in LAYER_ORDER:
            raise ValueError(f"Invalid layer: {stop_after}. Must be one of {LAYER_ORDER}")

        stop_idx = LAYER_ORDER.index(stop_after)

        # Determine starting point
        start_layer = run.next_layer()
        if start_layer is None:
            logger.info("Run is already complete.")
            return run

        start_idx = LAYER_ORDER.index(start_layer)

        if start_idx > stop_idx:
            logger.info(
                f"Already past {stop_after} "
                f"(current: {run.status}). Nothing to do."
            )
            return run

        # Run each layer in sequence
        layer_runners = {
            "l0": self.run_l0,
            "l05": self.run_l05,
            "l1": self.run_l1,
            "l15": self.run_l15,
            "l2": self.run_l2,
            "l3": self.run_l3,
        }

        for layer in LAYER_ORDER[start_idx:stop_idx + 1]:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"  {LAYER_DISPLAY_NAMES[layer]}")
            logger.info(f"{'=' * 60}")

            try:
                run = await layer_runners[layer](run)
            except BudgetExceededError as e:
                logger.error(f"Budget exceeded during {layer}: {e}")
                logger.info("Saving partial outputs...")
                run.save(self.config.output_dir)
                raise

            # Save after each layer
            run.save(self.config.output_dir)
            logger.info(
                f"  Saved to: {self.config.output_dir / run.id}"
            )
            logger.info(f"  Running cost: ${run.total_cost_usd:.2f}")

        return run

    async def run_all(
        self,
        company_name: str,
        user_context: str | None = None,
    ) -> ResearchRun:
        """Run the full pipeline from scratch."""
        run = self.create_run(company_name, user_context)
        return await self.run_to(run, stop_after="l3")

    def create_run(
        self,
        company_name: str,
        user_context: str | None = None,
    ) -> ResearchRun:
        """Create a new research run."""
        run = ResearchRun(
            id=self._generate_run_id(),
            company_name=company_name,
            user_context=user_context,
            created_at=datetime.now(),
            status="pending",
            current_layer="l0",
        )

        # Create output directory
        run_dir = self.config.output_dir / run.id
        run_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created new run: {run.id}")
        logger.info(f"Output directory: {run_dir}")

        return run

    def load_run(self, run_id: str) -> ResearchRun:
        """Load an existing run from disk."""
        run = ResearchRun.load(self.config.output_dir, run_id)
        logger.info(f"Loaded run {run_id} (status: {run.status})")

        # Restore cost tracker state
        if self.runner is None:
            self.runner = ResearchRunner(self.config)
        self.runner.total_cost = run.total_cost_usd

        return run

    # ── Parsing methods ─────────────────────────────────────────────────

    def _extract_archetype(self, l0_output: str) -> CompanyArchetype:
        """Extract company archetype from L0 output."""
        archetype_map = {
            "MANUFACTURER": CompanyArchetype.MANUFACTURER,
            "EXTRACTOR": CompanyArchetype.EXTRACTOR_GROWER,
            "GROWER": CompanyArchetype.EXTRACTOR_GROWER,
            "RETAILER": CompanyArchetype.RETAILER_DISTRIBUTOR,
            "DISTRIBUTOR": CompanyArchetype.RETAILER_DISTRIBUTOR,
            "PLATFORM": CompanyArchetype.PLATFORM_MARKETPLACE,
            "MARKETPLACE": CompanyArchetype.PLATFORM_MARKETPLACE,
            "SAAS": CompanyArchetype.SAAS_SOFTWARE,
            "SOFTWARE": CompanyArchetype.SAAS_SOFTWARE,
            "FINANCIAL": CompanyArchetype.FINANCIAL_SERVICES,
            "INFRASTRUCTURE": CompanyArchetype.INFRASTRUCTURE_UTILITIES,
            "UTILITIES": CompanyArchetype.INFRASTRUCTURE_UTILITIES,
            "PROFESSIONAL": CompanyArchetype.PROFESSIONAL_SERVICES,
            "CONGLOMERATE": CompanyArchetype.CONGLOMERATE,
            "HEALTHCARE": CompanyArchetype.HEALTHCARE_PHARMA,
            "PHARMA": CompanyArchetype.HEALTHCARE_PHARMA,
            "MEDIA": CompanyArchetype.MEDIA_ENTERTAINMENT,
            "ENTERTAINMENT": CompanyArchetype.MEDIA_ENTERTAINMENT,
            "REAL ESTATE": CompanyArchetype.REAL_ESTATE,
        }

        # Look for explicit archetype classification
        archetype_pattern = re.compile(
            r"(?:archetype|classify|classification)[:\s—-]+\**\s*"
            r"(MANUFACTURER|EXTRACTOR|GROWER|RETAILER|DISTRIBUTOR|PLATFORM|MARKETPLACE|"
            r"SAAS|SOFTWARE|FINANCIAL|INFRASTRUCTURE|UTILITIES|PROFESSIONAL|"
            r"CONGLOMERATE|HEALTHCARE|PHARMA|MEDIA|ENTERTAINMENT|REAL ESTATE)",
            re.IGNORECASE,
        )

        match = archetype_pattern.search(l0_output)
        if match:
            key = match.group(1).upper()
            if key in archetype_map:
                return archetype_map[key]

        # Fallback: search for the keywords in the first ~2000 chars
        header = l0_output[:2000].upper()
        for key, archetype in archetype_map.items():
            if key in header:
                return archetype

        logger.warning("Could not detect archetype, defaulting to OTHER")
        return CompanyArchetype.OTHER

    def _parse_agent_prompts(self, l05_output: str) -> tuple[list[str], list[str]]:
        """Parse individual agent prompts from L0.5 output.

        Expected format:
            AGENT N: LENS NAME
            ...
            ```
            prompt text
            ```

        Returns (prompts, names).
        """
        prompts = []
        names = []

        # Find all AGENT N: NAME sections
        agent_pattern = re.compile(
            r"AGENT\s+(\d+)\s*:\s*(.+?)(?:\n|$)",
            re.IGNORECASE,
        )

        # Find all code blocks
        code_blocks = re.findall(r"```(?:\w*\n)?(.*?)```", l05_output, re.DOTALL)

        # Match agents to their code blocks
        agent_matches = list(agent_pattern.finditer(l05_output))

        if code_blocks and agent_matches:
            # Strategy: For each agent header, find the next code block after it
            for i, match in enumerate(agent_matches):
                name = match.group(2).strip().rstrip("*").strip()
                pos = match.end()

                # Find the next code block after this position
                next_block = None
                for block in code_blocks:
                    block_pos = l05_output.find(block, pos - 100)  # small lookback
                    if block_pos >= pos - 100:
                        next_block = block.strip()
                        break

                if next_block and len(next_block) > 100:
                    prompts.append(next_block)
                    names.append(name)

        # Fallback: if parsing found fewer than expected, use all substantial code blocks
        if len(prompts) < 4 and len(code_blocks) >= 4:
            logger.warning(
                f"Agent-to-block matching found only {len(prompts)} prompts. "
                f"Falling back to all {len(code_blocks)} code blocks."
            )
            prompts = []
            names = []
            for i, block in enumerate(code_blocks):
                block = block.strip()
                if len(block) > 200:  # Substantial enough to be a prompt
                    prompts.append(block)
                    # Try to find the agent name from nearby text
                    if i < len(agent_matches):
                        names.append(agent_matches[i].group(2).strip().rstrip("*").strip())
                    else:
                        names.append(f"Agent {i + 1}")

        logger.info(f"Parsed {len(prompts)} agent prompts from L0.5 output")
        return prompts, names

    def _parse_l2_prompts(self, gen_output: str) -> tuple[list[str], list[str]]:
        """Parse L2 prompts from generation output.

        Expected format:
            L2 AGENT N: DESCRIPTIVE TITLE
            ...
            ```
            prompt text
            ```
        """
        prompts = []
        names = []

        agent_pattern = re.compile(
            r"L2\s+AGENT\s+(\d+)\s*:\s*(.+?)(?:\n|$)",
            re.IGNORECASE,
        )
        code_blocks = re.findall(r"```(?:\w*\n)?(.*?)```", gen_output, re.DOTALL)
        agent_matches = list(agent_pattern.finditer(gen_output))

        if code_blocks and agent_matches:
            for match in agent_matches:
                name = match.group(2).strip().rstrip("*").strip()
                pos = match.end()

                next_block = None
                for block in code_blocks:
                    block_pos = gen_output.find(block, pos - 100)
                    if block_pos >= pos - 100:
                        next_block = block.strip()
                        break

                if next_block and len(next_block) > 100:
                    prompts.append(next_block)
                    names.append(name)

        # Fallback
        if len(prompts) < 4 and len(code_blocks) >= 4:
            prompts = []
            names = []
            for i, block in enumerate(code_blocks):
                block = block.strip()
                if len(block) > 200:
                    prompts.append(block)
                    if i < len(agent_matches):
                        names.append(agent_matches[i].group(2).strip().rstrip("*").strip())
                    else:
                        names.append(f"L2 Dive {i + 1}")

        logger.info(f"Parsed {len(prompts)} L2 prompts")
        return prompts, names

    def _parse_tension_points(self, l15_output: str) -> list[TensionPoint]:
        """Parse tension points from L1.5 output."""
        points = []

        # Look for numbered tension point headers
        # Patterns like "## #1." or "## 1." or "### Tension Point 1:" etc.
        tp_pattern = re.compile(
            r"(?:^|\n)#{1,3}\s*#?(\d+)\.?\s*(.+?)(?:\n|$)",
            re.MULTILINE,
        )

        matches = list(tp_pattern.finditer(l15_output))

        for i, match in enumerate(matches):
            tp_id = int(match.group(1))
            title = match.group(2).strip().rstrip("*").strip()

            # Extract the content between this header and the next
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(l15_output)
            content = l15_output[start:end]

            # Parse fields from content
            tension = _extract_field(content, r"TENSION[:\s]", r"HYPOTHESIS")
            hypothesis = _extract_field(content, r"HYPOTHESIS[:\s]", r"CATEGORY")
            category = _extract_field(content, r"CATEGORY[:\s]", r"(?:POTENTIAL\s+)?MAGNITUDE")
            magnitude = _extract_field(content, r"(?:POTENTIAL\s+)?MAGNITUDE[:\s]", r"TIME\s+HORIZON")
            time_horizon = _extract_field(content, r"TIME\s+HORIZON[:\s]", r"CONFIDENCE")
            confidence = _extract_field(content, r"CONFIDENCE[:\s]", r"(?:LAYER\s+2|L2)\s+RESEARCH")
            l2_question = _extract_field(content, r"(?:LAYER\s+2|L2)\s+RESEARCH\s+QUESTION[:\s]", r"(?:---|$)")

            points.append(TensionPoint(
                id=tp_id,
                title=title,
                tension=tension,
                hypothesis=hypothesis,
                category=category,
                magnitude=magnitude,
                time_horizon=time_horizon,
                confidence=confidence,
                l2_research_question=l2_question,
            ))

        if not points:
            logger.warning("Could not parse structured tension points. Creating generic entries.")
            # Fallback: look for any numbered items
            numbered = re.findall(r"(\d+)\.\s+\*\*(.+?)\*\*", l15_output)
            for num_str, title in numbered:
                points.append(TensionPoint(id=int(num_str), title=title))

        logger.info(f"Parsed {len(points)} tension points")
        return points

    def _extract_tension_points_text(self, l15_output: str) -> str:
        """Extract just the tension points section from L1.5 output."""
        # Look for Deliverable 2 section
        markers = [
            "DELIVERABLE 2",
            "TENSION POINTS",
            "RESEARCH HYPOTHESES",
        ]

        for marker in markers:
            idx = l15_output.upper().find(marker)
            if idx >= 0:
                return l15_output[idx:]

        # Fallback: return everything after the first major numbered section
        match = re.search(r"#{1,3}\s*#?1\.", l15_output)
        if match:
            return l15_output[match.start():]

        return l15_output

    def _split_l3_output(self, text: str) -> tuple[str, str]:
        """Split L3 output into executive briefing and full report."""
        # Look for Deliverable 2 / Full Research Compendium separator
        patterns = [
            r"(?:^|\n)#{1,2}\s*DELIVERABLE\s*2",
            r"(?:^|\n)#{1,2}\s*FULL\s+RESEARCH\s+COMPENDIUM",
            r"(?:^|\n)#{1,2}\s*RESEARCH\s+COMPENDIUM",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                briefing = text[:match.start()].strip()
                report = text[match.start():].strip()
                return briefing, report

        # Fallback: return all as briefing
        return text, ""


def _extract_field(content: str, start_pattern: str, end_pattern: str) -> str:
    """Extract text between two regex-defined field markers.

    Used for parsing structured tension point fields from L1.5 output.
    """
    start_match = re.search(start_pattern, content, re.IGNORECASE)
    if not start_match:
        return ""

    text_start = start_match.end()

    end_match = re.search(end_pattern, content[text_start:], re.IGNORECASE)
    if end_match:
        text = content[text_start:text_start + end_match.start()]
    else:
        # Take everything to the end
        text = content[text_start:]

    # Clean up: remove leading/trailing whitespace, bold markers, etc.
    text = text.strip()
    text = re.sub(r"^\*\*\s*", "", text)
    text = re.sub(r"\s*\*\*$", "", text)
    return text.strip()
