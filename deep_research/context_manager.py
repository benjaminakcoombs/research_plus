"""Context window management — token counting and compression."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .models import AgentOutput

if TYPE_CHECKING:
    from .models import ResearchRun

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
    """Assemble L0 + L1.5 + filtered L2 outputs for L3 synthesis.

    Includes:
    - L0 company profile (baseline facts that L1.5 may have abstracted away)
    - L1.5 consolidation (synthesized view of all L1 + L0 research)
    - L2 deep dives, filtered by yield verdict:
      - DROP agents are excluded (found nothing new)
      - KEEP agents are included at standard allocation
      - HIGHLIGHT agents get 1.5x token budget when truncating

    If the combined content exceeds max_tokens, L2 outputs are truncated
    proportionally (with HIGHLIGHT agents getting more space).
    """
    sections = []

    # L0 company profile — baseline facts for grounding
    if run.l0_output:
        sections.append(
            "=== L0 COMPANY PROFILE ===\n\n"
            f"{run.l0_output}\n"
        )

    # L1.5 consolidation — the synthesized view of all L1 + L0 research
    if run.l15_output:
        sections.append(
            "=== L1.5 CONSOLIDATION: SITUATION MAP & TENSION POINTS ===\n\n"
            f"{run.l15_output}\n"
        )

    # L2 deep dives — filter out DROPs and errored outputs
    kept_l2: list[AgentOutput] = []
    dropped_count = 0
    errored_count = 0
    if run.l2_outputs:
        for output in run.l2_outputs:
            # Skip errored outputs entirely — they contain no usable research
            if output.raw_output.startswith("[ERROR"):
                errored_count += 1
                logger.info(
                    f"  Excluding L2 agent '{output.agent_name}' from L3 input (errored)"
                )
                continue
            verdict = getattr(output, "yield_verdict", "") or ""
            if verdict.upper() == "DROP":
                dropped_count += 1
                logger.info(
                    f"  Excluding L2 agent '{output.agent_name}' from L3 input (verdict: DROP)"
                )
            else:
                kept_l2.append(output)

        if dropped_count or errored_count:
            logger.info(
                f"  L3 input: {len(kept_l2)} L2 agents included, "
                f"{dropped_count} dropped by yield verdict, {errored_count} errored"
            )

    for i, output in enumerate(kept_l2, 1):
        verdict = getattr(output, "yield_verdict", "") or ""
        verdict_tag = f" [{verdict}]" if verdict else ""
        sections.append(
            f"=== L2 DEEP DIVE {i}: {output.agent_name.upper()}{verdict_tag} ===\n\n"
            f"{output.raw_output}\n"
        )

    assembled = "\n---\n\n".join(sections)
    token_count = count_tokens(assembled)

    if token_count <= max_tokens:
        return assembled

    # Over budget — truncate L2 outputs proportionally to fit
    # HIGHLIGHT agents get 1.5x the budget of KEEP agents
    logger.warning(
        f"L3 input ({token_count} tokens) exceeds max ({max_tokens}). "
        "Truncating L2 outputs to fit."
    )
    l0_tokens = count_tokens(run.l0_output or "")
    l15_tokens = count_tokens(run.l15_output or "")
    overhead = 1000  # for separators and labels
    available_for_l2 = max_tokens - l0_tokens - l15_tokens - overhead

    # Guard against negative budget — if L0 + L1.5 already exceed the limit,
    # ensure L2 agents still get a minimum allocation rather than being silently
    # truncated to empty strings (Python negative slice → "").
    if available_for_l2 <= 0:
        logger.error(
            f"L0+L1.5 ({l0_tokens + l15_tokens} tokens) exceeds context limit "
            f"({max_tokens} tokens). Allocating minimum budget for L2 outputs."
        )
        available_for_l2 = max(2000, int(max_tokens * 0.1))  # At least 10% or 2K tokens

    # Calculate weighted allocation
    total_weight = sum(
        1.5 if (getattr(o, "yield_verdict", "") or "").upper() == "HIGHLIGHT" else 1.0
        for o in kept_l2
    )
    base_budget = available_for_l2 / max(total_weight, 1)

    sections = []
    if run.l0_output:
        sections.append(
            "=== L0 COMPANY PROFILE ===\n\n"
            f"{run.l0_output}\n"
        )
    if run.l15_output:
        sections.append(
            "=== L1.5 CONSOLIDATION: SITUATION MAP & TENSION POINTS ===\n\n"
            f"{run.l15_output}\n"
        )

    for i, output in enumerate(kept_l2, 1):
        text = output.raw_output
        verdict = getattr(output, "yield_verdict", "") or ""
        verdict_tag = f" [{verdict}]" if verdict else ""
        weight = 1.5 if verdict.upper() == "HIGHLIGHT" else 1.0
        target_tokens = int(base_budget * weight)
        target_chars = target_tokens * 4

        original_tokens = count_tokens(text)
        if original_tokens > target_tokens:
            text = text[:target_chars] + "\n\n[... truncated for context window ...]"
            logger.warning(
                f"  L2 agent '{output.agent_name}' truncated from "
                f"{original_tokens} to ~{target_tokens} tokens"
            )

        sections.append(
            f"=== L2 DEEP DIVE {i}: {output.agent_name.upper()}{verdict_tag} ===\n\n"
            f"{text}\n"
        )

    return "\n---\n\n".join(sections)


def assemble_l1_manifest(l1_outputs: list[AgentOutput]) -> str:
    """Build a compact manifest of L1 agent names and first ~100 words.

    This gives L4a enough context to assign L1 agents to section writers
    without sending the full L1 outputs (~500 tokens total vs ~50K+).
    """
    lines = []
    for i, output in enumerate(l1_outputs, 1):
        if output.raw_output.startswith("[ERROR"):
            continue
        # First ~100 words as a summary
        words = output.raw_output.split()
        snippet = " ".join(words[:100]).replace("\n", " ")
        lines.append(f"L1 AGENT {i}: {output.agent_name}\n  {snippet}...")
    return "\n\n".join(lines)


def assemble_l2_summaries(l2_outputs: list[AgentOutput], max_words_per_summary: int = 600) -> str:
    """Assemble truncated L2 summaries for L4a report architect.

    Returns the first ~600 words of each L2 output, enough for the architect
    to understand what each investigation found without the full evidentiary detail.
    """
    sections = []
    for i, output in enumerate(l2_outputs, 1):
        if output.raw_output.startswith("[ERROR"):
            continue
        verdict = getattr(output, "yield_verdict", "") or ""
        verdict_tag = f" [{verdict}]" if verdict else ""

        # Truncate to approximate word count
        words = output.raw_output.split()
        if len(words) > max_words_per_summary:
            summary_text = " ".join(words[:max_words_per_summary]) + "\n\n[... truncated for planning ...]"
        else:
            summary_text = output.raw_output

        sections.append(
            f"=== L2 DEEP DIVE {i}: {output.agent_name.upper()}{verdict_tag} ===\n\n"
            f"{summary_text}\n"
        )
    return "\n---\n\n".join(sections)


def assemble_l4b_sources(
    run: ResearchRun,
    source_agent_names: list[str],
    include_l0: bool = True,
    include_l15: bool = True,
    include_l3b: bool = False,
) -> str:
    """Assemble source documents for a single L4b section writer.

    Selects specific L1/L2 outputs by agent name, plus always-included L1.5 and optionally L0/L3b.
    """
    sections = []

    if include_l3b and run.l3b_final:
        sections.append(
            "=== L3b TEASER (DEEP ANALYSIS) ===\n\n"
            f"{run.l3b_final}\n"
        )

    if include_l0 and run.l0_output:
        sections.append(
            "=== L0 COMPANY PROFILE ===\n\n"
            f"{run.l0_output}\n"
        )

    if include_l15 and run.l15_output:
        sections.append(
            "=== L1.5 CONSOLIDATION ===\n\n"
            f"{run.l15_output}\n"
        )

    # Build lookup maps for agent outputs by name (case-insensitive)
    # Include gap-fill agents in the L1 map so L4b can reference them as sources
    all_l1 = list(run.l1_outputs) + list(run.gap_fill_agents)
    l1_by_name = {o.agent_name.lower(): o for o in all_l1}
    l2_by_name = {o.agent_name.lower(): o for o in run.l2_outputs}

    for name in source_agent_names:
        name_lower = name.lower()
        # Check L2 first (more likely to be referenced), then L1
        if name_lower in l2_by_name:
            output = l2_by_name[name_lower]
            if not output.raw_output.startswith("[ERROR"):
                sections.append(
                    f"=== L2 DEEP DIVE: {output.agent_name.upper()} ===\n\n"
                    f"{output.raw_output}\n"
                )
        elif name_lower in l1_by_name:
            output = l1_by_name[name_lower]
            if not output.raw_output.startswith("[ERROR"):
                sections.append(
                    f"=== L1 RESEARCH: {output.agent_name.upper()} ===\n\n"
                    f"{output.raw_output}\n"
                )
        else:
            # Fuzzy match — use difflib for best semantic match instead of brittle substring
            import difflib
            all_names = {**l2_by_name, **l1_by_name}
            matches = difflib.get_close_matches(name_lower, all_names.keys(), n=1, cutoff=0.4)
            if matches:
                best_match = matches[0]
                output = all_names[best_match]
                if not output.raw_output.startswith("[ERROR"):
                    label = "L2 DEEP DIVE" if output.agent_type == "l2" else "L1 RESEARCH"
                    sections.append(
                        f"=== {label}: {output.agent_name.upper()} ===\n\n"
                        f"{output.raw_output}\n"
                    )
                    logger.info(f"  L4b fuzzy matched '{name}' → '{output.agent_name}'")
                else:
                    logger.warning(f"  L4b source '{name}' matched '{output.agent_name}' but it errored")
            else:
                logger.warning(f"  L4b source not found: '{name}' (no close match in {len(all_names)} agents)")

    return "\n---\n\n".join(sections)


def assemble_l4b_all_outputs(l4b_outputs: list[AgentOutput]) -> str:
    """Concatenate all L4b section outputs for L4c editorial review."""
    sections = []
    for output in l4b_outputs:
        sections.append(
            f"=== {output.agent_name.upper()} ===\n\n"
            f"{output.raw_output}\n"
        )
    return "\n---\n\n".join(sections)
