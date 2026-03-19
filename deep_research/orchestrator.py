"""Orchestrator — runs the multi-layer research pipeline with stop/resume support."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from datetime import datetime
from pathlib import Path

from .config import Config
from .context_manager import count_tokens

HAIKU_MODEL = "claude-haiku-4-5-20251001"
from .models import (
    LAYER_ORDER,
    LAYER_DISPLAY_NAMES,
    AgentOutput,
    CompanyArchetype,
    QualityReport,
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

    def _generate_run_id(self, company_name: str = "") -> str:
        """Generate a readable run ID: SA_CompanyName_YYMMDDHHMM or run_hex8 fallback."""
        mode_prefix = "SA" if self.config.pipeline_mode == "situation_assessment" else "SB"
        if company_name:
            safe = company_name.replace(" ", "").replace(",", "").replace(".", "")[:20]
            timestamp = datetime.now().strftime("%y%m%d%H%M")
            return f"{mode_prefix}_{safe}_{timestamp}"
        short = uuid.uuid4().hex[:8]
        return f"run_{short}"

    async def _haiku_parse(self, prompt: str, task_id: str) -> str | None:
        """Call Haiku for lightweight parsing/extraction tasks.

        Returns the text response, or None if the call fails (caller should fall back to regex).
        Cost: ~$0.004 per call (4K input, 300 output).
        """
        runner = self._ensure_runner()
        try:
            text, costs = await runner.run_synthesis(
                prompt,
                task_id=task_id,
                model=HAIKU_MODEL,
            )
            return text
        except Exception as e:
            logger.warning(f"[{task_id}] Haiku parse failed: {e}. Falling back to regex.")
            return None

    async def _haiku_parse_json(self, prompt: str, task_id: str) -> dict | list | None:
        """Call Haiku and parse JSON from the response.

        Returns parsed JSON, or None if the call or parsing fails.
        """
        text = await self._haiku_parse(prompt, task_id)
        if text is None:
            return None
        # Extract JSON from response — Haiku may wrap it in ```json blocks
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        json_str = json_match.group(1) if json_match else text
        try:
            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            logger.warning(f"[{task_id}] Could not parse JSON from Haiku response. Falling back to regex.")
            return None

    # ── Layer execution methods ─────────────────────────────────────────

    async def run_l0(self, run: ResearchRun) -> ResearchRun:
        """L0: Company Profile — deep research with web search."""
        runner = self._ensure_runner()
        logger.info(f"[L0] Profiling {run.company_name}...")

        prompt = self.prompt_builder.build_l0(
            run.company_name,
            run.user_context,
            sector=run.sector,
            sub_sector_focus=run.sub_sector_focus,
            target_bank=run.target_bank,
        )

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
        run.company_archetype = await self._extract_archetype(text)
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

    async def _run_single_research(
        self, runner, prompt: str, name: str, task_id: str, agent_type: str,
    ) -> tuple[AgentOutput, list]:
        """Run a single research agent task. Returns (output, costs)."""
        logger.info(f"  [{task_id}] Starting: {name}")
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
                agent_type=agent_type,
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
                agent_type=agent_type,
                prompt=prompt,
                raw_output=f"[ERROR: Research task failed: {e}]",
                execution_time_seconds=elapsed,
            )

        return output, agent_costs

    async def _run_parallel_research_agents(
        self, run: ResearchRun, prompts: list[str], names: list[str],
        agent_type: str,
    ) -> list[tuple[AgentOutput, list]]:
        """Run research agents in parallel batches, respecting concurrency limit.

        Includes quality-based retry: if an agent's output fails its quality check,
        the agent is re-run up to max_retries times. This ensures each agent produces
        output that meets minimum quality thresholds before proceeding.

        Saves each agent's output to disk as it completes (incremental save).
        """
        runner = self._ensure_runner()
        semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        save_lock = asyncio.Lock()
        max_quality_retries = self.config.max_retries  # From config (default: 2)

        # Resume support: build the set of indices we already have GOOD outputs for.
        # Errored outputs ("[ERROR...") are excluded — those agents will be re-run.
        # Strategy: strip errored entries from the list, then run starting from len(good).
        # This handles mixed success/error states without creating duplicates.
        output_list_ref = run.l1_outputs if agent_type == "l1" else run.l2_outputs
        good_outputs = [o for o in output_list_ref if not o.raw_output.startswith("[ERROR")]
        errored_count = len(output_list_ref) - len(good_outputs)

        # Replace the list in-place so downstream readers see the cleaned state
        output_list_ref.clear()
        output_list_ref.extend(good_outputs)

        start_from = len(good_outputs)
        if errored_count > 0:
            logger.info(
                f"[{agent_type.upper()}] Resume: {len(good_outputs)} succeeded, "
                f"{errored_count} errored — will re-run errored agents"
            )

        remaining_prompts = list(enumerate(zip(prompts, names)))[start_from:]
        if start_from > 0 and errored_count == 0:
            logger.info(f"[{agent_type.upper()}] Resuming from agent {start_from + 1}/{len(prompts)} ({start_from} already done)")

        n = len(prompts)
        logger.info(f"[{agent_type.upper()}] Running {n - start_from} agents (max {self.config.max_concurrent_tasks} concurrent)...")

        # Collect results in order — pre-allocate slots
        results: list[tuple[AgentOutput, list] | None] = [None] * len(remaining_prompts)

        # Error retries are separate from quality retries — connection failures
        # need a cooldown before retry, not an immediate re-run.
        max_error_retries = 2
        error_cooldown_seconds = 60  # Wait before retrying a crashed agent

        async def run_and_save(slot_idx, i, prompt, name):
            task_id = f"{agent_type}_agent_{i + 1:02d}"
            best_output = None
            best_costs = []
            best_qr = None
            all_attempt_costs = []  # Track ALL costs across retries (bug 3a fix)
            error_retries_used = 0

            for attempt in range(max_quality_retries + 1 + max_error_retries):
                async with semaphore:
                    output, agent_costs = await self._run_single_research(
                        runner, prompt, name, task_id, agent_type,
                    )

                all_attempt_costs.extend(agent_costs)  # Accumulate all attempt costs

                # Distinguish errors from low quality — different retry strategies
                is_error = output.raw_output.startswith("[ERROR")

                if is_error:
                    if error_retries_used < max_error_retries:
                        error_retries_used += 1
                        logger.warning(
                            f"  [{task_id}] Agent errored: {output.raw_output[:100]}. "
                            f"Waiting {error_cooldown_seconds}s before retry "
                            f"({error_retries_used}/{max_error_retries})..."
                        )
                        await asyncio.sleep(error_cooldown_seconds)
                        continue
                    else:
                        logger.error(
                            f"  [{task_id}] Agent errored after {max_error_retries} retries. "
                            f"Giving up."
                        )
                        # Still save the error output as best if nothing else worked
                        if best_output is None:
                            best_output = output
                            best_costs = agent_costs
                            best_qr = QualityReport(
                                layer=agent_type, passed=False, pass_rate=0.0,
                                details=f"Agent errored: {output.raw_output[:200]}",
                            )
                        break

                # Quality check (only for non-errored outputs)
                if agent_type == "l1":
                    qr = self.quality_checker.check_l1(output.raw_output, output.agent_name)
                else:
                    qr = self.quality_checker.check_l2(output.raw_output, output.agent_name)

                # Semantic quality check (Haiku-powered, ~$0.01 per check)
                if agent_type == "l1":
                    semantic_qr = await self.quality_checker.check_l1_semantic(
                        output.raw_output, agent_name=output.agent_name, runner=runner,
                    )
                elif agent_type == "l2":
                    semantic_qr = await self.quality_checker.check_l2_semantic(
                        output.raw_output, agent_name=output.agent_name, runner=runner,
                    )
                else:
                    semantic_qr = None

                if semantic_qr:
                    run.quality_reports.append(semantic_qr)
                    # Semantic check is authoritative — it understands content quality,
                    # not just keyword presence. If Haiku says it's good, trust it even
                    # if regex disagrees. If Haiku says it's bad, override regex pass.
                    qr = semantic_qr

                # Keep the best result (highest pass rate)
                if best_qr is None or qr.pass_rate > best_qr.pass_rate:
                    best_output = output
                    best_costs = agent_costs
                    best_qr = qr

                if qr.passed:
                    break

                # Count quality retries separately from error retries
                quality_attempts = attempt - error_retries_used
                if quality_attempts < max_quality_retries:
                    logger.warning(
                        f"  [{task_id}] Quality check failed ({qr.pass_rate:.0%}): {qr.details}. "
                        f"Retrying ({quality_attempts + 1}/{max_quality_retries})..."
                    )
                else:
                    logger.warning(
                        f"  [{task_id}] Quality check failed after {max_quality_retries + 1} attempts "
                        f"({best_qr.pass_rate:.0%}). Using best result."
                    )
                    break

            results[slot_idx] = (best_output, all_attempt_costs)

            # Save incrementally under lock — record ALL attempt costs so cost_records
            # sums correctly to total_cost_usd (which includes retry costs via runner.total_cost).
            async with save_lock:
                run.quality_reports.append(best_qr)

                output_list = run.l1_outputs if agent_type == "l1" else run.l2_outputs
                output_list.append(best_output)
                run.cost_records.extend(all_attempt_costs)
                run.total_cost_usd = runner.total_cost
                run.save(self.config.output_dir)
                done = len(output_list)
                logger.info(f"  [{task_id}] Saved to disk ({done}/{n} complete)")

        tasks = [
            run_and_save(slot_idx, i, prompt, name)
            for slot_idx, (i, (prompt, name)) in enumerate(remaining_prompts)
        ]

        await asyncio.gather(*tasks)

        # Return results in original order (for any downstream use)
        return [r for r in results if r is not None]

    async def run_l1(self, run: ResearchRun) -> ResearchRun:
        """L1: Research — runs agents in parallel batches."""
        if not run.l1_prompts:
            raise ValueError("Cannot run L1 without L1 prompts (run L0.5 first)")

        await self._run_parallel_research_agents(
            run, run.l1_prompts, run.l1_prompt_names, "l1",
        )

        n = len(run.l1_prompts)
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
        qr = self.quality_checker.check_l15(text, pipeline_mode=self.config.pipeline_mode)
        run.quality_reports.append(qr)

        # Parse tension points
        run.tension_points = await self._parse_tension_points(text)
        logger.info(f"[L1.5] Identified {len(run.tension_points)} tension points")

        # Gap-fill: if research gaps identified and enabled, run supplementary agents
        if self.config.enable_gap_fill and not run.l15_rerun:
            gaps = await self._extract_research_gaps(text)
            if gaps:
                logger.info(f"[L1.5] Found {len(gaps)} research gaps, generating gap-fill agents...")
                gap_prompts = await self._generate_gap_fill_prompts(gaps, run)
                if gap_prompts:
                    # Run gap-fill agents in parallel (concurrent up to max_concurrent_tasks).
                    # Previously ran sequentially with cooldowns — this cut ~20min of wall time.
                    logger.info(f"  [gap-fill] Running {len(gap_prompts)} agents in parallel...")
                    semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
                    save_lock = asyncio.Lock()

                    gap_outputs: list[AgentOutput | None] = [None] * len(gap_prompts)
                    gap_costs_all: list = []

                    async def run_gap_agent(i: int, prompt: str):
                        task_id = f"l1_gap_{i + 1:02d}"
                        logger.info(f"  [{task_id}] Running gap-fill agent {i + 1}/{len(gap_prompts)}")
                        start = time.time()
                        agent_gap_costs: list = []
                        try:
                            async with semaphore:
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
                            agent_gap_costs = []

                        gap_outputs[i] = gap_output
                        async with save_lock:
                            gap_costs_all.extend(agent_gap_costs)

                    await asyncio.gather(*[run_gap_agent(i, p) for i, p in enumerate(gap_prompts)])

                    for gap_output in gap_outputs:
                        if gap_output is not None:
                            run.gap_fill_agents.append(gap_output)
                            # Note: gap-fill outputs are kept in gap_fill_agents only,
                            # NOT appended to l1_outputs. This prevents L1 resume logic
                            # from treating them as regular L1 agents and re-running them
                            # with L1 prompts if they errored.
                    run.cost_records.extend(gap_costs_all)
                    run.total_cost_usd = runner.total_cost
                    run.save(self.config.output_dir)

                    # Re-run L1.5 consolidation with expanded corpus (L1 + gap-fill)
                    all_l1_for_consolidation = run.l1_outputs + run.gap_fill_agents
                    logger.info(
                        f"[L1.5] Re-running consolidation with gap-fill outputs "
                        f"({len(run.l1_outputs)} L1 + {len(run.gap_fill_agents)} gap-fill)..."
                    )
                    run.l15_rerun = True

                    prompt = self.prompt_builder.build_l15(
                        company_name=run.company_name,
                        n_agents=len(all_l1_for_consolidation),
                        archetype=run.company_archetype,
                        l1_outputs=all_l1_for_consolidation,
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
                    qr = self.quality_checker.check_l15(text, pipeline_mode=self.config.pipeline_mode)
                    run.quality_reports.append(qr)
                    run.tension_points = await self._parse_tension_points(text)
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

        # Build structured tension point digest for L2 generation.
        # Instead of passing ~30K tokens of raw L1.5 narrative, format the parsed
        # TensionPoint objects into a compact ~5K token summary. This gives Opus
        # a much cleaner input for designing L2 prompts.
        if run.tension_points:
            tp_lines = []
            for tp in run.tension_points:
                parts = [f"TENSION POINT {tp.id}"]
                tags = []
                if tp.category:
                    tags.append(tp.category.upper())
                if tp.magnitude:
                    tags.append(tp.magnitude)
                if tp.confidence:
                    tags.append(f"Confidence: {tp.confidence}")
                if tags:
                    parts[0] += f" [{', '.join(tags)}]"

                tp_lines.append(parts[0])
                if tp.title:
                    tp_lines.append(f"Title: {tp.title}")
                if tp.tension:
                    tp_lines.append(f"Observation: {tp.tension}")
                if tp.hypothesis:
                    tp_lines.append(f"Hypothesis: {tp.hypothesis}")
                if tp.time_horizon:
                    tp_lines.append(f"Time Horizon: {tp.time_horizon}")
                if tp.l2_research_question:
                    tp_lines.append(f"L2 Research Question: {tp.l2_research_question}")
                tp_lines.append("---")

            tp_text = "\n".join(tp_lines)
            logger.info(
                f"[L2] Using structured tension point digest "
                f"({len(run.tension_points)} points, ~{count_tokens(tp_text)} tokens) "
                f"instead of raw L1.5 text"
            )
        else:
            # Fallback to raw text if parsing failed
            tp_text = self._extract_tension_points_text(run.l15_output)
            logger.warning("[L2] No parsed tension points available, falling back to raw L1.5 text")

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

        # Step 2: Run L2 research in parallel batches
        await self._run_parallel_research_agents(
            run, prompts, names, "l2",
        )

        # Parse yield verdicts from L2 outputs
        for output in run.l2_outputs:
            if not output.raw_output.startswith("[ERROR"):
                verdict = self._parse_yield_verdict(output.raw_output)
                output.yield_verdict = verdict
                if verdict:
                    logger.info(f"  [L2] {output.agent_name}: yield verdict = {verdict}")
                else:
                    logger.warning(f"  [L2] {output.agent_name}: no yield verdict found, defaulting to KEEP")
                    output.yield_verdict = "KEEP"

        passed = sum(1 for o in run.l2_outputs if not o.raw_output.startswith("[ERROR"))
        logger.info(f"[L2] Complete: {passed}/{len(prompts)} agents succeeded")

        run.status = "l2_complete"
        run.current_layer = "l2"
        return run

    async def run_l3a(self, run: ResearchRun) -> ResearchRun:
        """L3a: Synthesis — produce initial draft of the final document."""
        runner = self._ensure_runner()

        if not run.l2_outputs:
            raise ValueError("Cannot run L3a without L2 outputs")

        logger.info("[L3a] Producing synthesis draft...")

        prompt = self.prompt_builder.build_l3a(
            company_name=run.company_name,
            run=run,
        )

        token_count = count_tokens(prompt)
        logger.info(f"[L3a] Input size: {token_count} tokens")

        text, costs = await runner.run_synthesis(
            prompt,
            task_id="l3a_synthesis",
            model=self.config.synthesis_model,
        )

        run.cost_records.extend(costs)
        run.total_cost_usd = runner.total_cost

        run.l3a_draft = text

        logger.info("[L3a] Synthesis draft complete")

        run.status = "l3a_complete"
        run.current_layer = "l3a"
        return run

    async def run_l3b(self, run: ResearchRun) -> ResearchRun:
        """L3b: Refinement — take the L3a draft and produce the final client-ready document."""
        runner = self._ensure_runner()

        if not run.l3a_draft:
            raise ValueError("Cannot run L3b without L3a draft")

        logger.info("[L3b] Refining to final output...")

        prompt = self.prompt_builder.build_l3b(
            company_name=run.company_name,
            run=run,
            l3a_output=run.l3a_draft,
        )

        token_count = count_tokens(prompt)
        logger.info(f"[L3b] Input size: {token_count} tokens")

        text, costs = await runner.run_synthesis(
            prompt,
            task_id="l3b_refinement",
            model=self.config.synthesis_model,
        )

        run.cost_records.extend(costs)
        run.total_cost_usd = runner.total_cost

        # Quality check on the final output
        qr = self.quality_checker.check_l3(text, pipeline_mode=self.config.pipeline_mode)
        run.quality_reports.append(qr)

        run.l3b_final = text

        logger.info("[L3b] Final refinement complete")

        run.status = "l3b_complete"
        run.current_layer = "l3b"
        return run

    async def run_l3c(self, run: ResearchRun) -> ResearchRun:
        """L3c: PDF Generation — convert the L3b markdown to a styled PDF.

        This is a programmatic step (no LLM call). It uses ReportLab to produce
        a professional PDF matching the Pokee AI Deep Analysis house style.
        """
        from .pdf_generator import build_pdf_from_run

        if not run.l3b_final:
            raise ValueError("Cannot run L3c without L3b output")

        logger.info("[L3c] Generating styled PDF...")

        # Ensure L3b markdown is saved to disk before PDF generation
        run.save(self.config.output_dir)

        pdf_path = build_pdf_from_run(run, self.config.output_dir)

        if pdf_path is not None:
            # Store the path relative to the run directory for portability
            run_dir = self.config.output_dir / run.id
            run.l3c_pdf_path = str(pdf_path.relative_to(run_dir))
            logger.info(f"[L3c] PDF generated: {pdf_path}")
        else:
            logger.warning("[L3c] PDF generation skipped (reportlab not installed or L3b file missing)")
            # Still mark as complete — PDF is a nice-to-have, not blocking
            run.l3c_pdf_path = None

        run.status = "l3c_complete"
        run.current_layer = "l3c"
        return run

    # ── L4 Full Report Pipeline ────────────────────────────────────────

    async def run_l4a(self, run: ResearchRun) -> ResearchRun:
        """L4a: Report Architect — design the full report structure."""
        runner = self._ensure_runner()

        if not run.l3b_final:
            raise ValueError("Cannot run L4a without L3b output")

        logger.info("[L4a] Designing full report architecture...")

        prompt = self.prompt_builder.build_l4a(
            company_name=run.company_name,
            run=run,
        )

        token_count = count_tokens(prompt)
        logger.info(f"[L4a] Input size: {token_count} tokens")

        text, costs = await runner.run_synthesis(
            prompt,
            task_id="l4a_architect",
            model=self.config.synthesis_model,
        )

        run.l4a_output = text
        run.cost_records.extend(costs)
        run.total_cost_usd = runner.total_cost

        # Parse the three deliverables from L4a output
        style_guide = self._parse_l4a_style_guide(text)
        outline = self._parse_l4a_outline(text)
        tasks = await self._parse_l4a_task_assignments(text, run)

        run.l4a_style_guide = style_guide
        run.l4a_outline = outline

        if tasks:
            run.l4b_task_names = [t["name"] for t in tasks]
            run.l4b_task_briefs = [t["brief"] for t in tasks]
            run.l4b_task_sections = [t["section"] for t in tasks]
            run.l4b_task_models = [t["model"] for t in tasks]
            run.l4b_source_assignments = [t["sources"] for t in tasks]
            run.l4b_include_l0 = [t["include_l0"] for t in tasks]
            run.l4b_include_l15 = [t["include_l15"] for t in tasks]

        logger.info(f"[L4a] Designed {len(tasks)} writing tasks")
        for i, t in enumerate(tasks, 1):
            logger.info(f"  Task {i}: {t['name']} ({t['model']}, {t['length']})")

        run.status = "l4a_complete"
        run.current_layer = "l4a"
        return run

    async def run_l4b(self, run: ResearchRun) -> ResearchRun:
        """L4b: Section Writers — run parallel agents to write report sections."""
        runner = self._ensure_runner()

        if not run.l4b_task_briefs:
            raise ValueError("Cannot run L4b without L4a task assignments")

        # Validate all L4b input lists have the same length (prevents silent zip truncation)
        list_lengths = {
            "task_names": len(run.l4b_task_names),
            "task_briefs": len(run.l4b_task_briefs),
            "task_sections": len(run.l4b_task_sections),
            "task_models": len(run.l4b_task_models),
            "source_assignments": len(run.l4b_source_assignments),
        }
        unique_lengths = set(list_lengths.values())
        if len(unique_lengths) > 1:
            raise ValueError(
                f"L4b input lists have inconsistent lengths (would cause silent task drops): {list_lengths}"
            )

        logger.info(f"[L4b] Running {len(run.l4b_task_briefs)} section writers...")

        style_guide = run.l4a_style_guide or ""
        outline = run.l4a_outline or ""

        # Build prompts for each task
        prompts = []
        names = []
        # Default flags for backward compat if lists are empty
        include_l0_list = run.l4b_include_l0 or [True] * len(run.l4b_task_names)
        include_l15_list = run.l4b_include_l15 or [True] * len(run.l4b_task_names)

        for i, (name, brief, section, model, sources, inc_l0, inc_l15) in enumerate(zip(
            run.l4b_task_names,
            run.l4b_task_briefs,
            run.l4b_task_sections,
            run.l4b_task_models,
            run.l4b_source_assignments,
            include_l0_list,
            include_l15_list,
        )):
            # Determine if this section needs L3b (Section I typically does)
            include_l3b = section.upper().startswith("I") and not section.upper().startswith("II")

            prompt = self.prompt_builder.build_l4b(
                company_name=run.company_name,
                run=run,
                task_name=name,
                section_reference=f"Section {section} of VIII",
                section_brief=brief,
                style_guide=style_guide,
                full_outline=outline,
                section_requirements="See brief above.",
                section_connections="See brief above.",
                target_length=self._extract_target_length(brief),
                source_agent_names=sources,
                include_l3b=include_l3b,
                include_l0=inc_l0,
                include_l15=inc_l15,
            )
            prompts.append(prompt)
            names.append(name)

        # Run section writers in parallel using the existing parallel infrastructure
        # but with synthesis (no web search) rather than research
        semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        save_lock = asyncio.Lock()

        # Resume support: filter out errored outputs (same pattern as L1/L2)
        good_outputs = [o for o in run.l4b_outputs if not o.raw_output.startswith("[ERROR")]
        errored_count = len(run.l4b_outputs) - len(good_outputs)
        run.l4b_outputs.clear()
        run.l4b_outputs.extend(good_outputs)
        start_from = len(good_outputs)
        remaining = list(enumerate(zip(prompts, names, run.l4b_task_models)))[start_from:]

        if errored_count > 0:
            logger.info(
                f"[L4b] Resume: {len(good_outputs)} succeeded, "
                f"{errored_count} errored — will re-run errored tasks"
            )
        elif start_from > 0:
            logger.info(f"[L4b] Resuming from task {start_from + 1}/{len(prompts)} ({start_from} already done)")

        results: list[tuple[AgentOutput, list] | None] = [None] * len(remaining)

        async def run_section_writer(slot_idx, i, prompt, name, model_choice):
            task_id = f"l4b_section_{i + 1:02d}"
            # Choose model: "opus" → synthesis_model (Opus), "sonnet" → research_model (Sonnet)
            use_model = self.config.synthesis_model if model_choice.lower() == "opus" else self.config.research_model

            logger.info(f"  [{task_id}] Writing: {name} (model: {model_choice})")
            start = time.time()

            try:
                async with semaphore:
                    text, agent_costs = await runner.run_synthesis(
                        prompt,
                        task_id=task_id,
                        model=use_model,
                    )
                elapsed = time.time() - start
                total_cost = sum(c.estimated_cost_usd for c in agent_costs)

                logger.info(f"  [{task_id}] Complete: {name} ({elapsed:.0f}s, ${total_cost:.2f})")

                output = AgentOutput(
                    agent_name=name,
                    agent_type="l4b",
                    prompt=prompt[:500],  # Truncate prompt for storage (they're large)
                    raw_output=text,
                    token_count=sum(c.output_tokens for c in agent_costs),
                    execution_time_seconds=elapsed,
                    cost_usd=total_cost,
                )
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"  [{task_id}] Failed: {name} ({elapsed:.0f}s): {e}")
                output = AgentOutput(
                    agent_name=name,
                    agent_type="l4b",
                    prompt=prompt[:500],
                    raw_output=f"[ERROR: Section writing failed: {e}]",
                    execution_time_seconds=elapsed,
                )
                agent_costs = []

            results[slot_idx] = (output, agent_costs)

            async with save_lock:
                run.l4b_outputs.append(output)
                run.cost_records.extend(agent_costs)
                run.total_cost_usd = runner.total_cost
                run.save(self.config.output_dir)
                done = len(run.l4b_outputs)
                logger.info(f"  [{task_id}] Saved ({done}/{len(prompts)} complete)")

        tasks = [
            run_section_writer(slot_idx, i, prompt, name, model)
            for slot_idx, (i, (prompt, name, model)) in enumerate(remaining)
        ]

        await asyncio.gather(*tasks)

        passed = sum(1 for o in run.l4b_outputs if not o.raw_output.startswith("[ERROR"))
        logger.info(f"[L4b] Complete: {passed}/{len(prompts)} sections written")

        run.status = "l4b_complete"
        run.current_layer = "l4b"
        return run

    async def run_l4c(self, run: ResearchRun) -> ResearchRun:
        """L4c: Editorial Review — produce editorial memo for all sections."""
        runner = self._ensure_runner()

        if not run.l4b_outputs:
            raise ValueError("Cannot run L4c without L4b section outputs")

        logger.info("[L4c] Running editorial review...")

        prompt = self.prompt_builder.build_l4c(
            company_name=run.company_name,
            run=run,
            style_guide=run.l4a_style_guide or "",
            full_outline=run.l4a_outline or "",
        )

        token_count = count_tokens(prompt)
        logger.info(f"[L4c] Input size: {token_count} tokens")

        text, costs = await runner.run_synthesis(
            prompt,
            task_id="l4c_editorial",
            model=self.config.synthesis_model,
        )

        run.l4c_editorial_memo = text
        run.cost_records.extend(costs)
        run.total_cost_usd = runner.total_cost

        # Parse editorial memo into global notes and per-section notes
        global_notes, section_notes = await self._parse_l4c_editorial_memo(text, run.l4b_task_names)
        run.l4c_global_notes = global_notes
        run.l4c_section_notes = section_notes

        logger.info(f"[L4c] Editorial review complete ({len(section_notes)} section note sets)")

        run.status = "l4c_complete"
        run.current_layer = "l4c"
        return run

    async def run_l4d(self, run: ResearchRun) -> ResearchRun:
        """L4d: Section Revision — revise sections based on editorial notes, then assemble."""
        runner = self._ensure_runner()

        if not run.l4c_editorial_memo:
            raise ValueError("Cannot run L4d without L4c editorial memo")

        logger.info(f"[L4d] Revising {len(run.l4b_outputs)} sections...")

        style_guide = run.l4a_style_guide or ""
        global_notes = run.l4c_global_notes or "No global notes."

        # Parse cross-section conflicts from the editorial memo
        cross_section_notes = self._parse_l4c_cross_section_notes(run.l4c_editorial_memo)

        # Build revision prompts
        semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        save_lock = asyncio.Lock()

        # Resume support: filter out errored outputs (same pattern as L4b)
        good_outputs = [o for o in run.l4d_outputs if not o.raw_output.startswith("[ERROR")]
        errored_count = len(run.l4d_outputs) - len(good_outputs)
        run.l4d_outputs.clear()
        run.l4d_outputs.extend(good_outputs)
        start_from = len(good_outputs)

        # Pad section_notes to match l4b_outputs length (P1-4: prevents zip truncation)
        section_notes = list(run.l4c_section_notes) if run.l4c_section_notes else []
        section_notes += [""] * (len(run.l4b_outputs) - len(section_notes))

        sections_to_revise = list(enumerate(zip(
            run.l4b_outputs,
            run.l4b_task_names,
            run.l4b_task_sections,
            section_notes,
            run.l4b_task_models if run.l4b_task_models else ["sonnet"] * len(run.l4b_outputs),
        )))[start_from:]

        if errored_count > 0:
            logger.info(
                f"[L4d] Resume: {len(good_outputs)} succeeded, "
                f"{errored_count} errored — will re-run errored revisions"
            )
        elif start_from > 0:
            logger.info(f"[L4d] Resuming from section {start_from + 1}/{len(run.l4b_outputs)}")

        results: list[tuple[AgentOutput, list] | None] = [None] * len(sections_to_revise)

        async def run_revision(slot_idx, i, section_output, name, section_ref, section_note, model_choice):
            task_id = f"l4d_revise_{i + 1:02d}"

            # Build cross-section notes relevant to this section
            relevant_cross = self._filter_cross_section_notes(cross_section_notes, name, section_ref)

            prompt = self.prompt_builder.build_l4d(
                company_name=run.company_name,
                task_name=name,
                section_reference=f"Section {section_ref} of VIII",
                style_guide=style_guide,
                global_notes=global_notes,
                section_notes=section_note if section_note else "No section-specific notes. Reproduce as-is.",
                cross_section_notes=relevant_cross if relevant_cross else "No cross-section conflicts for this section.",
                current_section_text=section_output.raw_output,
            )

            # Use the same model as L4b for this section — Opus sections deserve Opus revisions
            use_model = self.config.synthesis_model if model_choice.lower() == "opus" else self.config.research_model

            logger.info(f"  [{task_id}] Revising: {name} (model: {model_choice})")
            start = time.time()

            try:
                async with semaphore:
                    text, agent_costs = await runner.run_synthesis(
                        prompt,
                        task_id=task_id,
                        model=use_model,
                    )
                elapsed = time.time() - start
                total_cost = sum(c.estimated_cost_usd for c in agent_costs)

                logger.info(f"  [{task_id}] Complete: {name} ({elapsed:.0f}s, ${total_cost:.2f})")

                output = AgentOutput(
                    agent_name=name,
                    agent_type="l4d",
                    prompt=prompt[:500],
                    raw_output=text,
                    token_count=sum(c.output_tokens for c in agent_costs),
                    execution_time_seconds=elapsed,
                    cost_usd=total_cost,
                )
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"  [{task_id}] Failed: {name} ({elapsed:.0f}s): {e}")
                # On failure, use the original section text
                output = AgentOutput(
                    agent_name=name,
                    agent_type="l4d",
                    prompt=prompt[:500],
                    raw_output=section_output.raw_output,  # Fallback to original
                    execution_time_seconds=elapsed,
                )
                agent_costs = []

            results[slot_idx] = (output, agent_costs)

            async with save_lock:
                run.l4d_outputs.append(output)
                run.cost_records.extend(agent_costs)
                run.total_cost_usd = runner.total_cost
                run.save(self.config.output_dir)

        tasks = [
            run_revision(slot_idx, i, section_output, name, section_ref, section_note, model_choice)
            for slot_idx, (i, (section_output, name, section_ref, section_note, model_choice)) in enumerate(sections_to_revise)
        ]

        await asyncio.gather(*tasks)

        # Assemble final report by concatenating revised sections in TASK ORDER.
        # asyncio.gather completes in arbitrary order, so l4d_outputs may be scrambled.
        # Build a name→output map and reassemble in the original task order.
        output_by_name = {o.agent_name: o for o in run.l4d_outputs}
        final_sections = []
        for task_name in run.l4b_task_names:
            output = output_by_name.get(task_name)
            if output and not output.raw_output.startswith("[ERROR"):
                final_sections.append(output.raw_output)

        run.l4_final_report = "\n\n---\n\n".join(final_sections)

        logger.info(f"[L4d] Final report assembled ({len(final_sections)} sections)")

        run.status = "complete"
        run.current_layer = "l4d"
        return run

    # ── L4 Parsing Methods ──────────────────────────────────────────────

    @staticmethod
    def _parse_l4a_style_guide(l4a_output: str) -> str:
        """Extract the style guide from L4a output (DELIVERABLE 1)."""
        # Look for DELIVERABLE 1 or STYLE GUIDE heading
        patterns = [
            r"(?:###?\s*DELIVERABLE\s*1\s*:\s*STYLE\s+GUIDE|###?\s*STYLE\s+GUIDE)\s*\n(.*?)(?=###?\s*DELIVERABLE\s*2|###?\s*SECTION\s+ASSIGNMENTS|\Z)",
            r"STYLE\s+GUIDE\s*\n(.*?)(?=DELIVERABLE\s*2|SECTION\s+ASSIGNMENTS|\Z)",
        ]
        for pattern in patterns:
            match = re.search(pattern, l4a_output, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        logger.warning("[L4a] Could not parse style guide, using full output section")
        return ""

    @staticmethod
    def _parse_l4a_outline(l4a_output: str) -> str:
        """Extract the report outline/structure from L4a output.

        This is assembled from the section assignments — we rebuild a concise
        outline listing each task name, section, and target length.
        """
        # Extract from DELIVERABLE 2 section
        match = re.search(
            r"(?:###?\s*DELIVERABLE\s*2|###?\s*SECTION\s+ASSIGNMENTS)\s*:?\s*.*?\n(.*?)(?=###?\s*DELIVERABLE\s*3|###?\s*ASSEMBLY\s+NOTES|\Z)",
            l4a_output,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        return ""

    async def _parse_l4a_task_assignments(self, l4a_output: str, run: ResearchRun) -> list[dict]:
        """Parse task assignments from L4a output using Haiku, with regex fallback."""
        # Build the list of actual agent names for Haiku to match against
        l1_agent_names = [o.agent_name for o in run.l1_outputs if not o.raw_output.startswith("[ERROR")]
        l2_agent_names = [o.agent_name for o in run.l2_outputs if not o.raw_output.startswith("[ERROR")]
        gap_agent_names = [o.agent_name for o in run.gap_fill_agents if not o.raw_output.startswith("[ERROR")]

        haiku_result = await self._haiku_parse_json(
            f"""Extract ALL writing task assignments from this report architect output.
Return a JSON array where each object has:
- "name": string (task/section title)
- "section": string (roman numeral section reference, e.g., "III-B")
- "length": string (target length, e.g., "4-6 pages")
- "model": string (exactly "opus" or "sonnet" — default to "opus" if unclear)
- "brief": string (the full writing brief for this section, including key requirements and connections)
- "sources": array of strings (source agent names to include — match against the ACTUAL agent names listed below)
- "include_l0": boolean (whether L0 company profile is needed — default true)
- "include_l15": boolean (whether L1.5 consolidation is needed — default true)

ACTUAL AGENT NAMES (use these exact names in the "sources" array):
L1 agents: {json.dumps(l1_agent_names + gap_agent_names)}
L2 agents: {json.dumps(l2_agent_names)}

When the output references an agent, map it to the closest matching name from the lists above.

REPORT ARCHITECT OUTPUT:
{l4a_output[:40000]}

Return ONLY valid JSON — an array of task objects. No commentary.""",
            task_id="haiku_l4a_tasks",
        )
        if haiku_result and isinstance(haiku_result, list) and len(haiku_result) >= 3:
            tasks = []
            for item in haiku_result:
                try:
                    tasks.append({
                        "name": item.get("name", f"Task {len(tasks) + 1}"),
                        "section": item.get("section", ""),
                        "length": item.get("length", "4-6 pages"),
                        "model": "sonnet" if "sonnet" in str(item.get("model", "")).lower() else "opus",
                        "brief": item.get("brief", ""),
                        "sources": item.get("sources", []),
                        "include_l0": item.get("include_l0", True),
                        "include_l15": item.get("include_l15", True),
                    })
                except Exception as e:
                    logger.warning(f"Skipping malformed task from Haiku: {e}")
            if tasks:
                logger.info(f"[L4a] Parsed {len(tasks)} task assignments via Haiku")
                return tasks
            logger.warning("Haiku returned no valid tasks. Falling back to regex.")

        return self._parse_l4a_task_assignments_regex(l4a_output)

    @staticmethod
    def _parse_l4a_task_assignments_regex(l4a_output: str) -> list[dict]:
        """Regex fallback for L4a task assignment parsing."""
        tasks = []

        # Find all TASK blocks
        task_pattern = re.compile(
            r"TASK\s+(\d+)\s*:\s*(.+?)(?:\n|$)",
            re.IGNORECASE,
        )

        task_matches = list(task_pattern.finditer(l4a_output))

        for idx, match in enumerate(task_matches):
            name = match.group(2).strip().rstrip("*").strip()
            start_pos = match.end()

            # Determine end position (start of next TASK or end of DELIVERABLE 2)
            if idx + 1 < len(task_matches):
                end_pos = task_matches[idx + 1].start()
            else:
                # End at DELIVERABLE 3 or end of text
                d3_match = re.search(
                    r"###?\s*DELIVERABLE\s*3|###?\s*ASSEMBLY\s+NOTES",
                    l4a_output[start_pos:],
                    re.IGNORECASE,
                )
                end_pos = start_pos + d3_match.start() if d3_match else len(l4a_output)

            block = l4a_output[start_pos:end_pos]

            # Parse fields from block
            section = ""
            section_match = re.search(r"REPORT\s+SECTION\s*:\s*(.+?)(?:\n|$)", block, re.IGNORECASE)
            if section_match:
                section = section_match.group(1).strip()

            length = "4-6 pages"
            length_match = re.search(r"TARGET\s+LENGTH\s*:\s*(.+?)(?:\n|$)", block, re.IGNORECASE)
            if length_match:
                length = length_match.group(1).strip()

            model = "opus"
            model_match = re.search(r"WRITER\s+MODEL\s*:\s*(.+?)(?:\n|$)", block, re.IGNORECASE)
            if model_match:
                model_text = model_match.group(1).strip().lower()
                model = "sonnet" if "sonnet" in model_text else "opus"

            # Extract brief (everything between BRIEF: and the next field header)
            brief = ""
            brief_match = re.search(
                r"BRIEF\s*:\s*\n(.*?)(?=\nSOURCE\s+DOCUMENTS|\nKEY\s+REQUIREMENTS|\nCONNECTIONS|\nTASK\s+\d|\Z)",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            if brief_match:
                brief = brief_match.group(1).strip()

            # Extract source document flags and agent names from SOURCE DOCUMENTS section
            sources = []
            include_l0 = True  # Default to including
            include_l15 = True  # Default to including
            source_match = re.search(
                r"SOURCE\s+DOCUMENTS\s*:\s*\n(.*?)(?=\nKEY\s+REQUIREMENTS|\nCONNECTIONS|\nTASK\s+\d|\Z)",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            if source_match:
                source_text = source_match.group(1)
                for line in source_text.split("\n"):
                    line = line.strip()
                    # Parse L0 inclusion flag
                    if re.match(r"-\s*L0\s", line, re.IGNORECASE):
                        include_l0 = not re.search(r":\s*No\b", line, re.IGNORECASE)
                    # Parse L1.5 inclusion flag
                    elif re.match(r"-\s*L1\.5\s", line, re.IGNORECASE):
                        include_l15 = not re.search(r":\s*No\b", line, re.IGNORECASE)
                    # Extract agent names from L2 and L1 lines
                    elif re.match(r"-\s*L[12]\s", line, re.IGNORECASE):
                        colon_match = re.search(r":\s*(.+)", line)
                        if colon_match:
                            names_text = colon_match.group(1).strip()
                            if names_text.lower() not in ("no", "none", "n/a", "yes"):
                                for agent_name in re.split(r"[,;]", names_text):
                                    agent_name = agent_name.strip().strip('"').strip("'")
                                    if agent_name and len(agent_name) > 3:
                                        sources.append(agent_name)

            # Also include key requirements and connections in the brief
            req_match = re.search(
                r"KEY\s+REQUIREMENTS\s*:\s*\n(.*?)(?=\nCONNECTIONS|\nTASK\s+\d|\Z)",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            conn_match = re.search(
                r"CONNECTIONS\s+TO\s+OTHER\s+SECTIONS?\s*:\s*\n(.*?)(?=\nTASK\s+\d|\Z)",
                block,
                re.DOTALL | re.IGNORECASE,
            )

            # Append requirements and connections to the brief for the section writer
            if req_match:
                brief += f"\n\nKEY REQUIREMENTS:\n{req_match.group(1).strip()}"
            if conn_match:
                brief += f"\n\nCONNECTIONS TO OTHER SECTIONS:\n{conn_match.group(1).strip()}"

            tasks.append({
                "name": name,
                "section": section,
                "length": length,
                "model": model,
                "brief": brief,
                "sources": sources,
                "include_l0": include_l0,
                "include_l15": include_l15,
            })

        logger.info(f"[L4a] Parsed {len(tasks)} task assignments")
        return tasks

    @staticmethod
    def _extract_target_length(brief: str) -> str:
        """Extract target length from a brief, or return default."""
        match = re.search(r"(\d+-\d+\s*pages?)", brief, re.IGNORECASE)
        if match:
            return match.group(1)
        return "4-6 pages"

    async def _parse_l4c_editorial_memo(
        self, memo: str, task_names: list[str]
    ) -> tuple[str, list[str]]:
        """Parse L4c editorial memo using Haiku, with regex fallback."""
        haiku_result = await self._haiku_parse_json(
            f"""Parse this editorial review memo into global notes and per-section notes.

The memo reviews these sections (in order):
{json.dumps(task_names)}

Return a JSON object with:
- "global_notes": string (notes that apply to all sections — tone, style, consistency issues)
- "section_notes": array of strings (one entry per section, in the SAME ORDER as the section list above)
  - Each entry should contain ALL editorial feedback specific to that section
  - If a section has no specific notes, use an empty string ""

IMPORTANT: The section_notes array MUST have exactly {len(task_names)} entries, one per section.

EDITORIAL MEMO:
{memo[:30000]}

Return ONLY valid JSON. No commentary.""",
            task_id="haiku_l4c_parse",
        )
        if haiku_result and isinstance(haiku_result, dict):
            global_notes = haiku_result.get("global_notes", "")
            section_notes = haiku_result.get("section_notes", [])
            # Validate and pad if needed
            if isinstance(section_notes, list):
                section_notes = [str(n) if n else "" for n in section_notes]
                section_notes += [""] * (len(task_names) - len(section_notes))
                section_notes = section_notes[:len(task_names)]
                logger.info(f"[L4c] Parsed editorial memo via Haiku ({sum(1 for n in section_notes if n)} sections with notes)")
                return global_notes, section_notes

        logger.warning("Haiku L4c parsing failed. Falling back to regex.")
        return self._parse_l4c_editorial_memo_regex(memo, task_names)

    @staticmethod
    def _parse_l4c_editorial_memo_regex(
        memo: str, task_names: list[str]
    ) -> tuple[str, list[str]]:
        """Regex fallback for L4c editorial memo parsing."""
        global_notes = ""
        global_match = re.search(
            r"###?\s*GLOBAL\s+NOTES\s*\n(.*?)(?=###?\s*SECTION|$)",
            memo,
            re.DOTALL | re.IGNORECASE,
        )
        if global_match:
            global_notes = global_match.group(1).strip()

        section_notes = []
        for task_name in task_names:
            escaped_name = re.escape(task_name[:30])
            patterns = [
                rf"SECTION\s+[IVX\d]+[A-Za-z-]*\s*:\s*{escaped_name}.*?\nOVERALL.*?\n(.*?)(?=\nSECTION\s+[IVX\d]|\n###|\Z)",
                rf"{escaped_name}.*?\nOVERALL.*?\n(.*?)(?=\nSECTION\s+[IVX\d]|\n###|\Z)",
            ]

            found = False
            for pattern in patterns:
                match = re.search(pattern, memo, re.DOTALL | re.IGNORECASE)
                if match:
                    section_notes.append(match.group(1).strip())
                    found = True
                    break

            if not found:
                section_notes.append("")

        return global_notes, section_notes

    @staticmethod
    def _parse_l4c_cross_section_notes(memo: str) -> str:
        """Extract cross-section conflicts section from editorial memo."""
        match = re.search(
            r"###?\s*CROSS-SECTION\s+CONFLICTS\s*\n(.*?)(?=###?\s*STRONGEST|###?\s*WEAKEST|\Z)",
            memo,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _filter_cross_section_notes(cross_notes: str, task_name: str, section_ref: str) -> str:
        """Filter cross-section notes to only those relevant to a specific section."""
        if not cross_notes:
            return ""

        relevant_lines = []
        for line in cross_notes.split("\n"):
            # Include lines that mention this section by name or reference
            if (task_name.lower()[:20] in line.lower() or
                f"section {section_ref}" in line.lower() or
                f"section {section_ref.lower()}" in line.lower()):
                relevant_lines.append(line)

        return "\n".join(relevant_lines) if relevant_lines else ""

    # ── Gap-fill methods ──────────────────────────────────────────────

    async def _extract_research_gaps(self, l15_output: str) -> list[str]:
        """Extract research gap descriptions from L1.5 output using Haiku, with regex fallback."""
        haiku_result = await self._haiku_parse_json(
            f"""Identify the research gaps, unanswered questions, or areas needing further investigation
from this research consolidation output. These may appear under headings like "RESEARCH GAPS",
"Remaining Questions", "Areas for Further Investigation", or embedded in the analysis.

Return a JSON array of strings, where each string is a concise description of one gap.
Only include substantive gaps (not trivially small). Return 1-5 gaps maximum.

CONSOLIDATION OUTPUT (may be long):
{l15_output[:30000]}

Return ONLY valid JSON — an array of strings. No commentary.""",
            task_id="haiku_research_gaps",
        )
        if haiku_result and isinstance(haiku_result, list):
            gaps = [g.strip() for g in haiku_result if isinstance(g, str) and len(g) > 20]
            if gaps:
                logger.info(f"[Gap-fill] Extracted {len(gaps)} research gaps via Haiku")
                return gaps[:self.config.max_gap_fill_agents]
            logger.warning("Haiku returned no valid research gaps. Falling back to regex.")

        return self._extract_research_gaps_regex(l15_output)

    def _extract_research_gaps_regex(self, l15_output: str) -> list[str]:
        """Regex fallback for research gap extraction."""
        gaps = []

        # Strategy: find the "RESEARCH GAPS" sub-heading (which may be nested)
        # and extract everything from it to the next heading or end of section.
        # Try sub-heading first (e.g., "## B) RESEARCH GAPS" or "## b) RESEARCH GAPS")
        sub_heading = re.search(
            r"#{1,3}\s*[A-Za-z]\)\s*RESEARCH\s+GAPS?\b(.*?)(?=\n#{1,3}\s|\n===|\Z)",
            l15_output,
            re.IGNORECASE | re.DOTALL,
        )

        if not sub_heading:
            # Try standalone "RESEARCH GAPS" heading
            sub_heading = re.search(
                r"#{1,3}\s*RESEARCH\s+GAPS?\b[^#\n]*(.*?)(?=\n#{1,3}\s|\n===|\Z)",
                l15_output,
                re.IGNORECASE | re.DOTALL,
            )

        if not sub_heading:
            # Last resort: look for the text "RESEARCH GAPS" anywhere and grab content after it
            sub_heading = re.search(
                r"RESEARCH\s+GAPS?\s*\n(.*?)(?=\n#{1,3}\s|\n===|\Z)",
                l15_output,
                re.IGNORECASE | re.DOTALL,
            )

        if not sub_heading:
            logger.warning("[Gap-fill] Could not find RESEARCH GAPS section")
            return gaps

        section_text = sub_heading.group(1)

        # Extract bullet items (- or *)
        bullets = re.findall(r"[-*]\s+\*{0,2}(.+?)(?=\n[-*]|\n\n|\Z)", section_text, re.DOTALL)

        # Also try numbered items (1. 2. etc.)
        if not bullets:
            bullets = re.findall(r"\d+\.\s+\*{0,2}(.+?)(?=\n\d+\.|\n\n|\Z)", section_text, re.DOTALL)

        for bullet in bullets:
            cleaned = bullet.strip().rstrip("*").strip()
            if len(cleaned) > 20:  # Skip trivially short items
                gaps.append(cleaned)

        logger.info(f"[Gap-fill] Extracted {len(gaps)} research gaps")
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

        # Guard: strategic_briefing mode is missing L3b+ templates
        if self.config.pipeline_mode == "strategic_briefing" and stop_idx >= LAYER_ORDER.index("l3b"):
            raise ValueError(
                f"Cannot run past L3a in strategic_briefing mode — "
                f"templates for L3b/L3c/L4 are not yet implemented. "
                f"Use --mode situation_assessment or --stop-after l3a."
            )

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
            "l3a": self.run_l3a,
            "l3b": self.run_l3b,
            "l3c": self.run_l3c,
            "l4a": self.run_l4a,
            "l4b": self.run_l4b,
            "l4c": self.run_l4c,
            "l4d": self.run_l4d,
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

    def _print_run_summary(self, run: ResearchRun, elapsed_seconds: float) -> None:
        """Print a structured cost/quality summary when a run completes."""
        elapsed_min = elapsed_seconds / 60
        h, m = divmod(int(elapsed_min), 60)
        elapsed_str = f"{h}h {m:02d}m" if h else f"{m}m"

        # Per-layer cost rollup.
        # Sort prefixes longest-first so "l15" matches before "l1", "l05" before "l0", etc.
        layer_prefixes = [
            ("gap_fill", "Gap"), ("contrarian", "Contrarian"),
            ("l4d", "L4d"), ("l4c", "L4c"), ("l4b", "L4b"), ("l4a", "L4a"),
            ("l3b", "L3b"), ("l3a", "L3a"), ("l15", "L1.5"),
            ("l05", "L0.5"), ("l2", "L2"), ("l1", "L1"), ("l0", "L0"),
        ]
        layer_costs: dict[str, float] = {}
        layer_searches: dict[str, int] = {}
        for rec in run.cost_records:
            layer = "other"
            tid = rec.task_id.lower()
            for prefix, label in layer_prefixes:
                if tid.startswith(prefix):
                    layer = label
                    break
            layer_costs[layer] = layer_costs.get(layer, 0) + rec.estimated_cost_usd
            layer_searches[layer] = layer_searches.get(layer, 0) + rec.search_count

        # Quality summary
        layer_quality: dict[str, list[float]] = {}
        for qr in run.quality_reports:
            layer_quality.setdefault(qr.layer, []).append(qr.pass_rate)
        quality_str = " | ".join(
            f"{layer} {sum(rates)/len(rates):.0%}"
            for layer, rates in sorted(layer_quality.items())
        )

        summary_lines = [
            f"\n{'=' * 60}",
            f"  RUN COMPLETE: {run.id} ({run.company_name})",
            f"{'=' * 60}",
            f"  Total cost: ${run.total_cost_usd:.2f} | Elapsed: {elapsed_str}",
        ]
        for label in ["L0", "L0.5", "L1", "Gap", "L1.5", "L2", "L3a", "L3b", "L4a", "L4b", "L4c", "L4d"]:
            cost = layer_costs.get(label, 0)
            searches = layer_searches.get(label, 0)
            if cost > 0:
                summary_lines.append(
                    f"  {label:<8} ${cost:.2f}  ({searches} searches)"
                )
        summary_lines += [
            f"  Tension pts: {len(run.tension_points)} | L1 agents: {len(run.l1_outputs)} | L2 agents: {len(run.l2_outputs)}",
            f"  Quality:  {quality_str}" if quality_str else "",
            f"{'=' * 60}",
        ]
        for line in summary_lines:
            if line:
                logger.info(line)

    async def run_all(
        self,
        company_name: str,
        user_context: str | None = None,
        sector: str | None = None,
        target_bank: str | None = None,
        sub_sector_focus: str | None = None,
        include_full_report: bool = False,
    ) -> ResearchRun:
        """Run the full pipeline from scratch.

        Args:
            include_full_report: If True and mode is situation_assessment,
                run through L4d to produce the full 40-50 page report.
                If False, stop at L3b (teaser only).
        """
        start = time.time()
        run = self.create_run(
            company_name, user_context,
            sector=sector, target_bank=target_bank,
            sub_sector_focus=sub_sector_focus,
        )
        if include_full_report and self.config.pipeline_mode == "situation_assessment":
            stop_after = "l4d"
        else:
            stop_after = "l3b"
        run = await self.run_to(run, stop_after=stop_after)
        self._print_run_summary(run, time.time() - start)
        return run

    def create_run(
        self,
        company_name: str,
        user_context: str | None = None,
        sector: str | None = None,
        target_bank: str | None = None,
        sub_sector_focus: str | None = None,
    ) -> ResearchRun:
        """Create a new research run."""
        run = ResearchRun(
            id=self._generate_run_id(company_name),
            company_name=company_name,
            user_context=user_context,
            pipeline_mode=self.config.pipeline_mode,
            sector=sector,
            target_bank=target_bank,
            sub_sector_focus=sub_sector_focus,
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

        # Sync config pipeline_mode with the run's mode (critical for resume)
        if run.pipeline_mode != self.config.pipeline_mode:
            logger.info(f"Syncing pipeline_mode from run: {run.pipeline_mode}")
            self.config.pipeline_mode = run.pipeline_mode
            # Rebuild prompt builder with correct prompts directory
            self.prompt_builder = PromptBuilder(self.config)

        # Restore cost tracker state
        if self.runner is None:
            self.runner = ResearchRunner(self.config)
        self.runner.total_cost = run.total_cost_usd

        return run

    # ── Parsing methods ─────────────────────────────────────────────────

    async def _extract_archetype(self, l0_output: str) -> CompanyArchetype:
        """Extract company archetype from L0 output using Haiku, with regex fallback."""
        valid_archetypes = [a.value for a in CompanyArchetype]

        haiku_result = await self._haiku_parse(
            f"""Classify this company into exactly ONE archetype from the list below.
Return ONLY the archetype value, nothing else.

Valid archetypes: {', '.join(valid_archetypes)}

COMPANY PROFILE (first 3000 chars):
{l0_output[:3000]}

Return ONLY the archetype value (e.g., "manufacturer" or "platform_marketplace"):""",
            task_id="haiku_archetype",
        )
        if haiku_result:
            cleaned = haiku_result.strip().strip('"').strip("'").lower()
            try:
                return CompanyArchetype(cleaned)
            except ValueError:
                # Try partial match — Haiku might say "saas" instead of "saas_software"
                for archetype in CompanyArchetype:
                    if cleaned in archetype.value or archetype.value in cleaned:
                        return archetype
                logger.warning(f"Haiku returned unrecognized archetype: {cleaned}. Falling back to regex.")

        return self._extract_archetype_regex(l0_output)

    def _extract_archetype_regex(self, l0_output: str) -> CompanyArchetype:
        """Regex fallback for archetype detection."""
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

    @staticmethod
    def _parse_yield_verdict(output: str) -> str:
        """Parse the YIELD ASSESSMENT verdict from an L2 agent's output.

        Returns one of: 'HIGHLIGHT', 'KEEP', 'DROP', or '' if not found.
        """
        # Look for VERDICT: DROP/KEEP/HIGHLIGHT in the YIELD ASSESSMENT section
        verdict_match = re.search(
            r"VERDICT\s*:\s*(DROP|KEEP|HIGHLIGHT)",
            output,
            re.IGNORECASE,
        )
        if verdict_match:
            return verdict_match.group(1).upper()

        # Fallback: look for the keywords near "YIELD ASSESSMENT"
        ya_match = re.search(r"YIELD\s+ASSESSMENT", output, re.IGNORECASE)
        if ya_match:
            section = output[ya_match.start():ya_match.start() + 500]
            for verdict in ["HIGHLIGHT", "KEEP", "DROP"]:
                if verdict in section.upper():
                    return verdict

        return ""

    async def _parse_tension_points(self, l15_output: str) -> list[TensionPoint]:
        """Parse tension points from L1.5 output using Haiku, with regex fallback."""
        haiku_result = await self._haiku_parse_json(
            f"""Extract ALL tension points/observations from this research consolidation output.
Return a JSON array where each object has these fields:
- "id": integer (sequential from 1)
- "title": string (short title)
- "tension": string (the observation or tension described)
- "hypothesis": string (why it matters or the hypothesis)
- "category": string (one of: offensive_opportunity, defensive_risk, structural_unlock, information_arbitrage, or empty string)
- "magnitude": string (one of: transformational, major, moderate, or empty string)
- "time_horizon": string (one of: immediate_6mo, near_term_6_18mo, medium_term_1_3yr, or empty string)
- "confidence": string (one of: high, medium, low, or empty string)
- "l2_research_question": string (the research question for deeper investigation, or empty string)

Extract EVERY tension point, observation, or numbered insight. There should be 10-20 typically.

OUTPUT (may be long — read it all):
{l15_output[:50000]}

Return ONLY valid JSON — an array of objects. No commentary.""",
            task_id="haiku_tension_points",
        )
        if haiku_result and isinstance(haiku_result, list):
            points = []
            for item in haiku_result:
                try:
                    points.append(TensionPoint(
                        id=item.get("id", len(points) + 1),
                        title=item.get("title", ""),
                        tension=item.get("tension", ""),
                        hypothesis=item.get("hypothesis", ""),
                        category=item.get("category", ""),
                        magnitude=item.get("magnitude", ""),
                        time_horizon=item.get("time_horizon", ""),
                        confidence=item.get("confidence", ""),
                        l2_research_question=item.get("l2_research_question", ""),
                    ))
                except Exception as e:
                    logger.warning(f"Skipping malformed tension point from Haiku: {e}")
            if points:
                logger.info(f"Parsed {len(points)} tension points via Haiku")
                return points
            logger.warning("Haiku returned empty tension points. Falling back to regex.")

        return self._parse_tension_points_regex(l15_output)

    def _parse_tension_points_regex(self, l15_output: str) -> list[TensionPoint]:
        """Regex fallback for tension point parsing."""
        points = []

        # Try multiple header formats in priority order:
        # Format A: "## TENSION POINT 1 ★ (TOP 5)" or "### TENSION POINT #1: Title"
        # Format B: "## #1." or "## 1." or "### 1. Title"
        tp_pattern_named = re.compile(
            r"(?:^|\n)#{1,3}\s*TENSION\s+POINT\s+#?(\d+)\b[:\s]*(.*?)(?:\n|$)",
            re.MULTILINE | re.IGNORECASE,
        )
        tp_pattern_numbered = re.compile(
            r"(?:^|\n)#{1,3}\s*#?(\d+)\.?\s*(.+?)(?:\n|$)",
            re.MULTILINE,
        )

        matches = list(tp_pattern_named.finditer(l15_output))
        if not matches:
            matches = list(tp_pattern_numbered.finditer(l15_output))

        for i, match in enumerate(matches):
            tp_id = int(match.group(1))
            title = match.group(2).strip().rstrip("*").strip()

            # Extract the content between this header and the next
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(l15_output)
            content = l15_output[start:end]

            # Parse fields from content — support both strategic_briefing and situation_assessment formats
            tension = (
                _extract_field(content, r"TENSION[:\s]", r"HYPOTHESIS")
                or _extract_field(content, r"THE\s+OBSERVATION[:\s]", r"WHY\s+IT\s+MATTERS")
                or _extract_field(content, r"OBSERVATION[:\s]", r"WHY\s+IT\s+MATTERS")
            )
            hypothesis = (
                _extract_field(content, r"HYPOTHESIS[:\s]", r"CATEGORY")
                or _extract_field(content, r"WHY\s+IT\s+MATTERS[:\s]", r"(?:THE\s+)?QUESTION")
            )
            category = (
                _extract_field(content, r"CATEGORY[:\s]", r"(?:POTENTIAL\s+)?MAGNITUDE")
            )
            magnitude = (
                _extract_field(content, r"(?:POTENTIAL\s+)?MAGNITUDE[:\s]", r"TIME\s+HORIZON|CONFIDENCE")
            )
            time_horizon = (
                _extract_field(content, r"TIME\s+HORIZON[:\s]", r"CONFIDENCE")
            )
            confidence = (
                _extract_field(content, r"CONFIDENCE[:\s]", r"(?:LAYER\s+2|L2)\s+RESEARCH|(?:THE\s+)?QUESTION|---|$")
            )
            l2_question = (
                _extract_field(content, r"(?:LAYER\s+2|L2)\s+RESEARCH\s+QUESTION[:\s]", r"(?:---|$)")
                or _extract_field(content, r"(?:THE\s+)?QUESTION\s+IT\s+RAISES[:\s]", r"(?:---|$)")
            )

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
