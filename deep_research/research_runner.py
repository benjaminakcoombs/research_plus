"""Research runner — executes API calls with iterative search and synthesis."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime

import anthropic

from .config import Config, SEARCH_COST_ESTIMATE
from .models import AgentOutput, CostRecord

logger = logging.getLogger(__name__)

# Retry settings for rate limit errors
MAX_RETRIES = 8
BASE_BACKOFF_SECONDS = 60
MAX_BACKOFF_SECONDS = 180


class BudgetExceededError(Exception):
    """Raised when the cost budget is exceeded."""
    pass


class ResearchRunner:
    """Runs research and synthesis tasks against the Anthropic API."""

    def __init__(self, config: Config):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self.async_client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)
        self.total_cost = 0.0
        self.cost_records: list[CostRecord] = []
        self._semaphore = asyncio.Semaphore(config.max_concurrent_tasks)

    def _check_budget(self) -> None:
        """Check if we're within budget."""
        if self.total_cost >= self.config.max_total_cost_usd:
            raise BudgetExceededError(
                f"Budget exceeded: ${self.total_cost:.2f} >= ${self.config.max_total_cost_usd:.2f}"
            )
        if self.total_cost >= self.config.warn_cost_usd:
            logger.warning(
                f"Approaching budget limit: ${self.total_cost:.2f} / ${self.config.max_total_cost_usd:.2f}"
            )

    def _record_cost(self, task_id: str, model: str, input_tokens: int,
                     output_tokens: int, search_count: int = 0) -> CostRecord:
        """Record the cost of an API call."""
        cost = self.config.estimate_cost(model, input_tokens, output_tokens, search_count)

        record = CostRecord(
            task_id=task_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            search_count=search_count,
            estimated_cost_usd=cost,
            timestamp=datetime.now(),
        )

        self.total_cost += cost
        self.cost_records.append(record)

        logger.info(
            f"  [{task_id}] Cost: ${cost:.3f} | Tokens: {input_tokens}in/{output_tokens}out | "
            f"Searches: {search_count} | Running total: ${self.total_cost:.2f}"
        )

        return record

    async def _stream_to_response(self, stream_cm):
        """Consume a streaming response and return the final Message object."""
        async with stream_cm as stream:
            response = await stream.get_final_message()
        return response

    def _extract_text(self, response) -> str:
        """Extract text content from an API response."""
        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        return "\n".join(text_parts)

    def _count_searches(self, response) -> int:
        """Count web search tool uses in a response."""
        count = 0
        for block in response.content:
            if getattr(block, "type", None) == "server_tool_use":
                count += 1
        return count

    async def _call_with_retry(self, task_id: str, make_stream):
        """Call the API with retry + exponential backoff on rate limit errors."""
        for attempt in range(MAX_RETRIES + 1):
            try:
                return await self._stream_to_response(make_stream())
            except anthropic.RateLimitError as e:
                if attempt == MAX_RETRIES:
                    logger.error(f"  [{task_id}] Rate limit: max retries exhausted")
                    raise
                backoff = min(
                    BASE_BACKOFF_SECONDS * (2 ** attempt) + random.uniform(0, 10),
                    MAX_BACKOFF_SECONDS,
                )
                logger.warning(
                    f"  [{task_id}] Rate limited, waiting {backoff:.0f}s "
                    f"(attempt {attempt + 1}/{MAX_RETRIES})..."
                )
                await asyncio.sleep(backoff)

    async def run_research(
        self,
        prompt: str,
        task_id: str = "research",
        max_rounds: int | None = None,
    ) -> tuple[str, list[CostRecord]]:
        """Run an iterative deep research task with web search.

        Returns (output_text, cost_records).
        """
        if max_rounds is None:
            max_rounds = self.config.max_search_rounds

        self._check_budget()

        model = self.config.research_model
        messages = [{"role": "user", "content": prompt}]
        all_text = []
        round_costs = []

        for round_num in range(max_rounds):
            self._check_budget()

            logger.info(f"  [{task_id}] Research round {round_num + 1}/{max_rounds}")

            try:
                response = await self._call_with_retry(
                    task_id,
                    lambda: self.async_client.messages.stream(
                        model=model,
                        max_tokens=self.config.research_max_tokens,
                        thinking={
                            "type": "enabled",
                            "budget_tokens": self.config.research_thinking_budget,
                        },
                        tools=[
                            {
                                "type": "web_search_20250305",
                                "name": "web_search",
                                "max_uses": self.config.searches_per_round,
                            }
                        ],
                        messages=messages,
                    ),
                )
            except anthropic.APIError as e:
                logger.error(f"  [{task_id}] API error in round {round_num + 1}: {e}")
                if round_num > 0 and all_text:
                    break
                raise

            search_count = self._count_searches(response)
            cost = self._record_cost(
                f"{task_id}_r{round_num + 1}", model,
                response.usage.input_tokens, response.usage.output_tokens,
                search_count,
            )
            round_costs.append(cost)

            text = self._extract_text(response)
            all_text.append(text)

            if round_num == max_rounds - 1:
                break

            if response.stop_reason == "end_turn" and round_num < max_rounds - 1:
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": (
                        "Continue your research. What gaps remain in your analysis? "
                        "Search for additional information to fill them. Focus on "
                        "operational specifics, concrete numbers, and named entities. "
                        "Then produce your complete, consolidated output incorporating "
                        "everything you've found across all rounds."
                    ),
                })
            else:
                break

        return "\n\n".join(all_text), round_costs

    async def run_synthesis(
        self,
        prompt: str,
        task_id: str = "synthesis",
        model: str | None = None,
    ) -> tuple[str, list[CostRecord]]:
        """Run a synthesis/reasoning task (no web search).

        Uses streaming to avoid timeout on long Opus requests.
        Returns (output_text, cost_records).
        """
        if model is None:
            model = self.config.synthesis_model

        self._check_budget()

        logger.info(f"  [{task_id}] Running synthesis ({model})")

        # Use adaptive thinking for Opus (no budget_tokens), enabled for others
        if "opus" in model:
            thinking_config = {"type": "adaptive"}
        else:
            thinking_config = {
                "type": "enabled",
                "budget_tokens": self.config.synthesis_thinking_budget,
            }

        try:
            response = await self._stream_to_response(
                self.async_client.messages.stream(
                    model=model,
                    max_tokens=self.config.synthesis_max_tokens,
                    thinking=thinking_config,
                    messages=[{"role": "user", "content": prompt}],
                )
            )
        except anthropic.APIError as e:
            logger.error(f"  [{task_id}] API error: {e}")
            raise

        search_count = self._count_searches(response)
        cost = self._record_cost(
            task_id, model,
            response.usage.input_tokens, response.usage.output_tokens,
            search_count,
        )
        text = self._extract_text(response)

        return text, [cost]

    async def run_parallel_research(
        self,
        prompts: list[str],
        names: list[str],
        agent_type: str = "l1",
    ) -> list[AgentOutput]:
        """Run research tasks sequentially, one at a time.

        Waits for each agent to complete before starting the next.
        Includes a cooldown between agents to respect rate limits.
        Returns list of AgentOutput.
        """
        cooldown_seconds = 10  # pause between agents for rate limit headroom
        results = []

        for i, (prompt, name) in enumerate(zip(prompts, names)):
            task_id = f"{agent_type}_agent_{i + 1:02d}"

            # Cooldown between agents (skip before the first)
            if i > 0:
                logger.info(f"  [{task_id}] Cooling down {cooldown_seconds}s before starting...")
                await asyncio.sleep(cooldown_seconds)

            logger.info(f"  [{task_id}] Starting: {name} ({i + 1}/{len(prompts)})")
            start = time.time()

            try:
                text, costs = await self.run_research(
                    prompt=prompt,
                    task_id=task_id,
                )
                elapsed = time.time() - start
                total_cost = sum(c.estimated_cost_usd for c in costs)
                search_count = sum(c.search_count for c in costs)

                logger.info(
                    f"  [{task_id}] Complete: {name} "
                    f"({elapsed:.0f}s, ${total_cost:.2f}, {search_count} searches)"
                )

                results.append(AgentOutput(
                    agent_name=name,
                    agent_type=agent_type,
                    prompt=prompt,
                    raw_output=text,
                    token_count=sum(c.output_tokens for c in costs),
                    search_count=search_count,
                    execution_time_seconds=elapsed,
                    cost_usd=total_cost,
                ))
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"  [{task_id}] Failed: {name} ({elapsed:.0f}s): {e}")
                results.append(AgentOutput(
                    agent_name=name,
                    agent_type=agent_type,
                    prompt=prompt,
                    raw_output=f"[ERROR: Research task failed: {e}]",
                    execution_time_seconds=elapsed,
                ))

        return results
