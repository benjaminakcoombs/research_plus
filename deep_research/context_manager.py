"""Context window management — token counting and compression."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import AgentOutput, ResearchRun

logger = logging.getLogger(__name__)


def count_tokens(text: str) -> int:
    """Estimate token count using tiktoken (cl100k_base, similar to Claude's tokenizer)."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Fallback: rough estimate of ~4 chars per token
        return len(text) // 4


def assemble_l1_outputs(l1_outputs: list[AgentOutput]) -> str:
    """Concatenate all L1 outputs with agent labels."""
    sections = []
    for i, output in enumerate(l1_outputs, 1):
        sections.append(
            f"=== RESEARCH WORKSTREAM {i}: {output.agent_name.upper()} ===\n\n"
            f"{output.raw_output}\n"
        )
    return "\n---\n\n".join(sections)


def assemble_l3_input(run: ResearchRun, max_tokens: int = 150000) -> str:
    """Assemble L1.5 + L2 outputs for L3 synthesis.

    Only includes L1.5 consolidation and L2 deep dives. L0 and raw L1 outputs
    are excluded — L1.5 already consolidates both, and L2 validates the key
    findings in depth. This avoids redundancy and keeps the prompt well within
    the 200k context window.

    If the combined L1.5 + L2 content still exceeds max_tokens (e.g. with many
    large L2 agents), L2 outputs are truncated proportionally.
    """
    sections = []

    # L1.5 consolidation — the synthesized view of all L1 + L0 research
    if run.l15_output:
        sections.append(
            "=== L1.5 CONSOLIDATION: SITUATION MAP & TENSION POINTS ===\n\n"
            f"{run.l15_output}\n"
        )

    # L2 deep dives — targeted investigation of highest-priority hypotheses
    if run.l2_outputs:
        for i, output in enumerate(run.l2_outputs, 1):
            sections.append(
                f"=== L2 DEEP DIVE {i}: {output.agent_name.upper()} ===\n\n"
                f"{output.raw_output}\n"
            )

    assembled = "\n---\n\n".join(sections)
    token_count = count_tokens(assembled)

    if token_count <= max_tokens:
        return assembled

    # Over budget — truncate L2 outputs proportionally to fit
    logger.warning(
        f"L3 input ({token_count} tokens) exceeds max ({max_tokens}). "
        "Truncating L2 outputs to fit."
    )
    l15_tokens = count_tokens(run.l15_output or "")
    target_per_l2 = (max_tokens - l15_tokens - 1000) // max(len(run.l2_outputs), 1)
    target_chars = target_per_l2 * 4  # rough token-to-char ratio

    sections = []
    if run.l15_output:
        sections.append(
            "=== L1.5 CONSOLIDATION: SITUATION MAP & TENSION POINTS ===\n\n"
            f"{run.l15_output}\n"
        )
    for i, output in enumerate(run.l2_outputs, 1):
        text = output.raw_output
        if count_tokens(text) > target_per_l2:
            text = text[:target_chars] + "\n\n[... truncated for context window ...]"
        sections.append(
            f"=== L2 DEEP DIVE {i}: {output.agent_name.upper()} ===\n\n"
            f"{text}\n"
        )
    return "\n---\n\n".join(sections)
