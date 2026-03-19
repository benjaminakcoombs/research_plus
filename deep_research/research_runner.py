"""Research runner — executes API calls with iterative search and synthesis."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime

import re

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
                     output_tokens: int, search_count: int = 0,
                     thinking_tokens: int = 0, stop_reason: str = "") -> CostRecord:
        """Record the cost of an API call."""
        cost = self.config.estimate_cost(model, input_tokens, output_tokens, search_count)

        record = CostRecord(
            task_id=task_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
            search_count=search_count,
            estimated_cost_usd=cost,
            timestamp=datetime.now(),
        )

        self.total_cost += cost
        self.cost_records.append(record)

        stop_info = f" | stop: {stop_reason}" if stop_reason else ""
        think_info = ""  # thinking tokens are included in output_tokens; no separate tracking available
        logger.info(
            f"  [{task_id}] Cost: ${cost:.3f} | Tokens: {input_tokens}in/{output_tokens}out"
            f"{think_info} | Searches: {search_count}{stop_info} | Running total: ${self.total_cost:.2f}"
        )

        return record

    async def _stream_to_response(self, stream_cm):
        """Consume a streaming response and return the final Message object."""
        async with stream_cm as stream:
            response = await stream.get_final_message()
        return response

    def _extract_text(self, response) -> str:
        """Extract text content from an API response, stripping model preamble."""
        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        text = "\n".join(text_parts)

        # Strip known model preamble patterns that appear before the actual analysis.
        # These are conversational lead-ins that add no value to the research output.
        preamble_patterns = [
            # "Now I have sufficient information to..." / "Based on my research..."
            r"^(?:Now I (?:have|can|will)|Based on (?:my|the) research|After (?:reviewing|analyzing|examining)|Let me (?:now |)(?:provide|present|compile|summarize)).*?\n\n",
            # "Here is the comprehensive..." / "Below is my analysis..."
            r"^(?:Here is|Below is|The following is).*?\n\n",
            # "I'll now compile..." / "I've completed my research..."
            r"^(?:I'(?:ll|ve)|I (?:have|will)).*?\n\n",
            # Round transition commentary: "Looking critically at my Round 2..."
            r"^(?:Looking (?:critically|carefully)|Excellent|Good|Great|Perfect)[.,!].*?\n\n",
            # Gap identification from continuation rounds: "Three critical new findings..."
            r"^(?:Three |Two |The |These |This )(?:critical|key|important|remaining).*?\n\n",
        ]
        # Apply preamble stripping repeatedly until text starts with
        # real content (heading, horizontal rule, or structured output)
        for _ in range(5):  # Max 5 rounds of stripping
            stripped = text
            for pattern in preamble_patterns:
                stripped = re.sub(pattern, "", stripped, count=1, flags=re.DOTALL)
            if stripped == text:
                break  # Nothing more to strip
            text = stripped

        return text.strip()

    def _count_searches(self, response) -> int:
        """Count web search tool uses in a response."""
        count = 0
        for block in response.content:
            if getattr(block, "type", None) == "server_tool_use":
                count += 1
        return count

    @staticmethod
    def _is_retryable(e: Exception) -> bool:
        """Return True if the error is a transient error worth retrying."""
        status = getattr(e, "status_code", None)
        if status is None:
            # No status code: connection/timeout/streaming errors — always retry
            return isinstance(e, anthropic.APIError)
        if status == 429 or status >= 500:
            return True
        return False  # 4xx client errors are not retryable

    async def _call_with_retry(self, task_id: str, make_stream):
        """Call the API with retry + exponential backoff on transient server errors."""
        for attempt in range(MAX_RETRIES + 1):
            try:
                return await self._stream_to_response(make_stream())
            except anthropic.APIError as e:
                if not self._is_retryable(e):
                    raise
                error_type = "Rate limited" if isinstance(e, anthropic.RateLimitError) else "Server error"
                if attempt == MAX_RETRIES:
                    logger.error(f"  [{task_id}] {error_type}: max retries exhausted")
                    raise
                backoff = min(
                    BASE_BACKOFF_SECONDS * (2 ** attempt) + random.uniform(0, 10),
                    MAX_BACKOFF_SECONDS,
                )
                logger.warning(
                    f"  [{task_id}] {error_type}, waiting {backoff:.0f}s "
                    f"(attempt {attempt + 1}/{MAX_RETRIES})..."
                )
                await asyncio.sleep(backoff)

    # Alias — synthesis calls use the same retry logic
    _call_synthesis_with_retry = _call_with_retry

    async def run_research(
        self,
        prompt: str,
        task_id: str = "research",
        max_rounds: int | None = None,
        round_callback=None,
    ) -> tuple[str, list[CostRecord]]:
        """Run an iterative deep research task with web search.

        Args:
            round_callback: Optional async callback invoked after each round
                (except the last). Signature: async (round_num, round_text) -> str | None
                - Return None to use the default continuation prompt.
                - Return a string to use it as a custom continuation prompt.
                - Return "__STOP__" to stop early (output is sufficient).
                The orchestrator uses this to inject Opus critique feedback
                between rounds, replacing the generic gap-identification prompt.

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
                # Capture messages by value (not reference) so that if _call_with_retry
                # retries the lambda, it sends the same message list that was current at
                # the time of the call — not the mutated list from a later continuation round.
                response = await self._call_with_retry(
                    task_id,
                    lambda msgs=list(messages): self.async_client.messages.stream(
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
                        messages=msgs,
                    ),
                )
            except anthropic.APIError as e:
                logger.error(f"  [{task_id}] API error in round {round_num + 1}: {e}")
                if round_num == 0:
                    raise  # Round 1 failure is fatal — no prior output to fall back to

                # Rounds 2+: retry the failed round once before falling back
                logger.warning(f"  [{task_id}] Retrying round {round_num + 1} after error...")
                try:
                    response = await self._call_with_retry(
                        task_id,
                        lambda msgs=list(messages): self.async_client.messages.stream(
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
                            messages=msgs,
                        ),
                    )
                except anthropic.APIError:
                    logger.warning(
                        f"  [{task_id}] Round {round_num + 1} retry also failed. "
                        f"Using output from round {round_num} (last successful)."
                    )
                    break
                # Retry succeeded — continue with the response below

            search_count = self._count_searches(response)
            # Note: The Anthropic API does not expose a separate thinking_tokens field.
            # Thinking tokens are included in output_tokens and billed at the same rate.
            # We leave thinking_tokens=0 in cost records; output_tokens is the accurate total.
            thinking_tokens = 0
            cost = self._record_cost(
                f"{task_id}_r{round_num + 1}", model,
                response.usage.input_tokens, response.usage.output_tokens,
                search_count, thinking_tokens=thinking_tokens,
                stop_reason=response.stop_reason or "",
            )
            round_costs.append(cost)

            text = self._extract_text(response)
            all_text.append(text)

            if round_num == max_rounds - 1:
                break

            # ── Round callback hook ──────────────────────────────────────
            # If a callback is provided (e.g. Opus critique), invoke it to
            # decide whether to continue and what continuation prompt to use.
            custom_continuation = None
            if round_callback is not None:
                callback_result = await round_callback(round_num, text)
                if callback_result == "__STOP__":
                    logger.info(
                        f"  [{task_id}] Round callback signaled early stop "
                        f"after round {round_num + 1} (output sufficient)"
                    )
                    break
                elif callback_result is not None:
                    custom_continuation = callback_result

            # Always continue to the next round for iterative deepening,
            # regardless of stop_reason. The model may have hit max_tokens
            # (truncated output) or end_turn (clean finish) — in both cases,
            # a follow-up round to find gaps and consolidate improves quality.
            # Only carry forward the model's text output, not the raw web
            # search result content (which can be 200-300K tokens per round).
            # The model already synthesized those pages into its text output.
            # Convert text blocks to plain dicts to strip citations — citations
            # reference server_tool_result blocks that are not carried forward,
            # which causes a 400 "Could not find search result for citation index".
            slim_content = []
            for block in response.content:
                block_type = getattr(block, "type", None)
                if block_type == "thinking":
                    # Convert to plain dict to avoid mixing Pydantic response objects
                    # with dict content blocks — the SDK handles it today but it's fragile.
                    slim_content.append({
                        "type": "thinking",
                        "thinking": block.thinking,
                        "signature": block.signature,
                    })
                elif block_type == "text":
                    slim_content.append({"type": "text", "text": block.text})

            if not slim_content:
                logger.warning(f"  [{task_id}] No text content in round {round_num + 1}, stopping")
                break

            messages.append({"role": "assistant", "content": slim_content})

            # ── Continuation prompt ──────────────────────────────────────
            # Priority: custom_continuation (from callback) > max_tokens > default
            if custom_continuation is not None:
                messages.append({
                    "role": "user",
                    "content": custom_continuation,
                })
            elif response.stop_reason == "max_tokens":
                # Model was truncated — ask it to continue and fill gaps
                messages.append({
                    "role": "user",
                    "content": (
                        "Your previous response was cut off. Continue your analysis, "
                        "then identify the 2-3 most critical unanswered questions or "
                        "missing data points — facts that would materially change the "
                        "analysis if found. Search for those specific items. "
                        "Then produce your complete, consolidated output incorporating "
                        "everything you've found across all rounds."
                    ),
                })
            else:
                messages.append({
                    "role": "user",
                    "content": (
                        "Review your analysis above. Identify the 2-3 most critical "
                        "unanswered questions or missing data points — facts that would "
                        "materially change the analysis if found. Search ONLY for those "
                        "specific items. Do not re-research topics you've already covered. "
                        "Then produce your complete, consolidated output incorporating "
                        "everything you've found across all rounds."
                    ),
                })

        # If multiple rounds ran, the final round contains the consolidated output
        # (the continuation prompt asks for a complete consolidated version).
        # Use only the last round's text to avoid duplication.
        final_text = all_text[-1] if all_text else ""
        return final_text, round_costs

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
            response = await self._call_synthesis_with_retry(
                task_id,
                lambda: self.async_client.messages.stream(
                    model=model,
                    max_tokens=self.config.synthesis_max_tokens,
                    thinking=thinking_config,
                    messages=[{"role": "user", "content": prompt}],
                ),
            )
        except anthropic.APIError as e:
            logger.error(f"  [{task_id}] API error: {e}")
            raise

        search_count = self._count_searches(response)
        # Note: The Anthropic API does not expose a separate thinking_tokens field.
        # Thinking tokens are included in output_tokens and billed at the same rate.
        # We leave thinking_tokens=0 in cost records; output_tokens is the accurate total.
        thinking_tokens = 0
        cost = self._record_cost(
            task_id, model,
            response.usage.input_tokens, response.usage.output_tokens,
            search_count, thinking_tokens=thinking_tokens,
            stop_reason=response.stop_reason or "",
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
