"""Quality checker — validates output quality at each layer."""

from __future__ import annotations

import re
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .research_runner import ResearchRunner

from .models import Critique, QualityReport

OPUS_MODEL = "claude-opus-4-6"

# ── Opus critic prompt templates ─────────────────────────────────────────

_L1_CRITIQUE_PROMPT = """You are a senior investment banking MD reviewing a junior analyst's \
first-pass research output. Your job is to identify specific gaps and weak points — \
NOT to score or grade the output.

RESEARCH AGENT: {agent_name}

FULL OUTPUT:
{output}

─────────────────────────────────────────────────────────────────────────

Answer each section. Be concrete and specific — never say "needs more detail." \
Say exactly WHAT detail is missing and WHY it matters for a deal team.

## SUFFICIENT
Is this output usable as a working first draft? Say YES if it contains at least 3 \
specific, evidence-backed findings relevant to the agent's mandate. Say NO only if \
the output is substantially vague, off-topic, or makes major claims with zero \
supporting evidence.
A missing angle or unexplored follow-up does NOT make it insufficient — that's \
what the next research round is for.
Answer: YES or NO

## GAPS
What specific questions does this research leave unanswered that a deal team \
would need answered? Be concrete: "What is the customer concentration among top \
5 accounts?" not "needs more customer detail."
List 0-5 items (one per line, prefixed with "- "). If SUFFICIENT=YES and gaps \
are minor, list 0-2.

## WEAK_CLAIMS
Which specific claims in the output are stated confidently but lack cited evidence? \
Quote the claim verbatim, then state what evidence would support it.
List 0-3 items (one per line, prefixed with "- ").

## MISSING_CONTEXT
What market, competitive, or regulatory context is absent that would change the \
interpretation of the findings?
List 0-3 items (one per line, prefixed with "- ").

## FOLLOW_UP_QUERIES
If you listed gaps or weak claims above, what specific web search queries would \
find the answers? Write these as actual search strings someone would type.
List 0-5 items (one per line, prefixed with "- ").

## SUMMARY
One sentence: what is the single most important thing this research is missing?"""

_L2_CRITIQUE_PROMPT = """You are a senior investment banking MD reviewing a deep-dive \
investigation output. Your job is to identify specific gaps — NOT to score it.

RESEARCH AGENT: {agent_name}

FULL OUTPUT:
{output}

─────────────────────────────────────────────────────────────────────────

Answer each section concretely.

## SUFFICIENT
Is this investigation usable as a working draft? Say YES if it presents specific \
evidence (for and against the hypothesis), shows quantitative reasoning, and \
cites at least one relevant precedent or comparable. Say NO only if it's \
substantially vague, lacks any supporting evidence, or doesn't address the \
core question.
Answer: YES or NO

## GAPS
What specific questions remain unanswered that would materially change a buyer's \
willingness to pay or a banker's timing advice?
List 0-5 items (one per line, prefixed with "- ").

## WEAK_CLAIMS
Which specific claims lack evidence? Quote the claim, state what's needed.
List 0-3 items (one per line, prefixed with "- ").

## MISSING_CONTEXT
What precedent transactions, regulatory developments, or market data is missing?
List 0-3 items (one per line, prefixed with "- ").

## FOLLOW_UP_QUERIES
Specific web search queries to fill the gaps above.
List 0-5 items (one per line, prefixed with "- ").

## SUMMARY
One sentence: what is the single most important gap in this investigation?"""

logger = logging.getLogger(__name__)


class QualityChecker:
    """Automated quality checks for each layer's output."""

    def check_l0(self, output: str) -> QualityReport:
        """Verify L0 profile has required sections and specificity."""
        checks = {
            "has_identity": bool(re.search(r"company identity|classification|ticker|exchange", output, re.I)),
            "has_business_model": bool(re.search(r"business model|segment|product line|operations", output, re.I)),
            "has_financials": bool(re.search(r"revenue|profit|margin|balance sheet|financial", output, re.I)),
            "has_numbers": bool(re.search(r'\$[\d,]+|£[\d,]+|\d+[,.]?\d*\s*(million|billion|M|B|m|bn)', output, re.I)),
            "has_geographies": bool(re.search(r"geographic|country|countries|region|operations in", output, re.I)),
            "has_competitors": bool(re.search(r"competi", output, re.I)),
            "has_governance": bool(re.search(r"board|chairman|CEO|shareholder|governance", output, re.I)),
            "has_facilities": bool(re.search(
                r"facilit|plant|factory|office|warehouse|estate|processing|data center",
                output, re.I,
            )),
            "min_length": len(output.split()) > 2000,
            "has_recommendations": bool(re.search(r"recommend|research.*lens|agent", output, re.I)),
            "has_archetype": bool(re.search(
                r"MANUFACTURER|EXTRACTOR|GROWER|RETAILER|DISTRIBUTOR|PLATFORM|MARKETPLACE|"
                r"SAAS|SOFTWARE|FINANCIAL|INFRASTRUCTURE|UTILITIES|PROFESSIONAL|"
                r"CONGLOMERATE|HEALTHCARE|PHARMA|MEDIA|ENTERTAINMENT|REAL ESTATE",
                output, re.I,
            )),
        }

        pass_rate = sum(checks.values()) / len(checks) if checks else 0
        passed = pass_rate >= 0.6

        report = QualityReport(
            layer="l0",
            checks=checks,
            pass_rate=pass_rate,
            passed=passed,
            details=_format_check_details(checks),
        )

        if not passed:
            logger.warning(f"L0 quality check FAILED ({pass_rate:.0%}): {report.details}")
        else:
            logger.info(f"L0 quality check passed ({pass_rate:.0%})")

        return report

    def check_l05(self, output: str) -> QualityReport:
        """Verify L0.5 agent design output."""
        checks = {
            "has_agents": bool(re.search(r"AGENT\s+\d", output, re.I)),
            "has_prompts": output.count("```") >= 2,  # At least one code block
            "has_justification": bool(re.search(r"JUSTIFICATION", output, re.I)),
            "has_priority": bool(re.search(r"PRIORITY", output, re.I)),
            "has_coverage": bool(re.search(r"COVERAGE", output, re.I)),
            "min_agents": len(re.findall(r"AGENT\s+\d", output, re.I)) >= 4,
            "has_anomaly_section": bool(re.search(r"ANOMAL|NOTABLE", output, re.I)),
            "min_length": len(output.split()) > 2000,
        }

        pass_rate = sum(checks.values()) / len(checks) if checks else 0
        passed = pass_rate >= 0.5

        report = QualityReport(
            layer="l05",
            checks=checks,
            pass_rate=pass_rate,
            passed=passed,
            details=_format_check_details(checks),
        )

        if not passed:
            logger.warning(f"L0.5 quality check FAILED ({pass_rate:.0%}): {report.details}")
        else:
            logger.info(f"L0.5 quality check passed ({pass_rate:.0%})")

        return report

    def check_l1(self, output: str, agent_name: str = "") -> QualityReport:
        """Verify a single L1 output has required depth."""
        checks = {
            "min_length": len(output.split()) > 1000,
            "has_specifics": bool(re.search(r'\d+', output)),
            "has_anomalies": bool(re.search(r"ANOMAL|NOTABLE|surprising|unusual", output, re.I)),
            "has_sources": bool(re.search(r"source|report|filing|according|cited", output, re.I)),
            "has_structure": output.count("#") >= 3 or output.count("**") >= 5,
        }

        pass_rate = sum(checks.values()) / len(checks) if checks else 0
        passed = pass_rate >= 0.5

        return QualityReport(
            layer="l1",
            checks=checks,
            pass_rate=pass_rate,
            passed=passed,
            details=f"Agent '{agent_name}': {_format_check_details(checks)}",
        )

    def check_l15(self, output: str, pipeline_mode: str = "strategic_briefing") -> QualityReport:
        """Verify consolidation has required tension points."""
        if pipeline_mode == "situation_assessment":
            checks = {
                "has_situation_map": bool(re.search(
                    r"SITUATION|COMPANY MAP|What.*IS|OWNS|MAKES MONEY|ENVIRONMENT",
                    output, re.I,
                )),
                "has_tension_points": bool(re.search(r"TENSION|OBSERVATION", output, re.I)),
                "has_why_it_matters": bool(re.search(r"WHY IT MATTERS|MATTERS|implication", output, re.I)),
                "min_tension_count": len(re.findall(r"(?:TENSION|OBSERVATION|^##\s*#?\d)", output, re.MULTILINE | re.I)) >= 8,
                "has_categories": bool(re.search(
                    r"VALUATION|DEAL TIMING|BUYER|DILIGENCE|HIDDEN VALUE|INFORMATION",
                    output, re.I,
                )),
                "has_l2_questions": bool(re.search(r"LAYER 2|L2|RESEARCH QUESTION|QUESTION.*RAISES", output, re.I)),
                "has_magnitudes": bool(re.search(r"TRANSFORMATIONAL|MAJOR|MODERATE|MAGNITUDE", output, re.I)),
                "has_classification_challenge": bool(re.search(
                    r"ARCHETYPE CHALLENGE|CLASSIFICATION|RESEARCH GAP", output, re.I
                )),
                "has_pre_mortem": bool(re.search(
                    r"PRE.MORTEM|pre-mortem|turned out to be wrong", output, re.I
                )),
                "min_length": len(output.split()) > 3000,
            }
        else:
            checks = {
                "has_situation_map": bool(re.search(
                    r"SITUATION|COMPANY MAP|What.*IS|What.*SAYS|ENVIRONMENT",
                    output, re.I,
                )),
                "has_tension_points": bool(re.search(r"TENSION", output, re.I)),
                "has_hypotheses": bool(re.search(r"HYPOTHESIS", output, re.I)),
                "min_tension_count": len(re.findall(r"(?:TENSION POINT|^##\s*#?\d)", output, re.MULTILINE | re.I)) >= 8,
                "has_categories": bool(re.search(
                    r"OFFENSIVE|DEFENSIVE|STRUCTURAL|INFORMATION.*ARBITRAGE",
                    output, re.I,
                )),
                "has_l2_questions": bool(re.search(r"LAYER 2|L2|RESEARCH QUESTION", output, re.I)),
                "has_magnitudes": bool(re.search(r"TRANSFORMATIONAL|MAJOR|MODERATE|MAGNITUDE", output, re.I)),
                "has_time_horizons": bool(re.search(r"IMMEDIATE|NEAR[\s\-]TERM|MEDIUM[\s\-]TERM|TIME HORIZON", output, re.I)),
                "has_classification_challenge": bool(re.search(
                    r"ARCHETYPE CHALLENGE|CLASSIFICATION|RESEARCH GAP", output, re.I
                )),
                "has_pre_mortem": bool(re.search(
                    r"PRE.MORTEM|pre-mortem|assume.*failed", output, re.I
                )),
                "min_length": len(output.split()) > 3000,
            }

        pass_rate = sum(checks.values()) / len(checks) if checks else 0
        passed = pass_rate >= 0.5

        report = QualityReport(
            layer="l15",
            checks=checks,
            pass_rate=pass_rate,
            passed=passed,
            details=_format_check_details(checks),
        )

        if not passed:
            logger.warning(f"L1.5 quality check FAILED ({pass_rate:.0%}): {report.details}")
        else:
            logger.info(f"L1.5 quality check passed ({pass_rate:.0%})")

        return report

    def check_l2(self, output: str, agent_name: str = "") -> QualityReport:
        """Verify L2 deep dive output."""
        checks = {
            "min_length": len(output.split()) > 800,
            "has_evidence_for": bool(re.search(r"EVIDENCE FOR|supports", output, re.I)),
            "has_evidence_against": bool(re.search(r"EVIDENCE AGAINST|challenges|contradicts", output, re.I)),
            "has_comparables": bool(re.search(r"COMPARABLE|PRECEDENT|similar", output, re.I)),
            "has_feasibility": bool(re.search(r"FEASIBILITY|capital required|timeline", output, re.I)),
            "has_confidence": bool(re.search(r"CONFIDENCE|confidence", output, re.I)),
        }

        pass_rate = sum(checks.values()) / len(checks) if checks else 0
        passed = pass_rate >= 0.6

        return QualityReport(
            layer="l2",
            checks=checks,
            pass_rate=pass_rate,
            passed=passed,
            details=f"Agent '{agent_name}': {_format_check_details(checks)}",
        )

    async def critique_l1(
        self,
        output: str,
        agent_name: str,
        runner: "ResearchRunner",
    ) -> Critique:
        """Opus critique of L1 research output.

        Replaces the old Haiku scoring system. Instead of rating 1-5 on abstract
        dimensions, Opus identifies specific gaps, weak claims, and follow-up
        queries. The critique is fed back to the research agent's next round
        as a directed continuation prompt.

        Cost: ~$0.15-0.30 per call (12K input, ~2K output).
        Falls back to a default "not sufficient" critique on API failure.
        """
        # Cap at ~12K chars (~3K tokens) — enough to see substance, not just intro
        truncated = output[:12000]
        prompt = _L1_CRITIQUE_PROMPT.format(agent_name=agent_name, output=truncated)

        try:
            text, costs = await runner.run_synthesis(
                prompt,
                task_id=f"critique_l1_{agent_name[:20]}",
                model=OPUS_MODEL,
            )
            critique = _parse_critique(text, agent_name)
            if critique.sufficient:
                logger.info(f"  Opus critique SUFFICIENT: '{agent_name}' — {critique.summary}")
            else:
                gap_count = len(critique.gaps)
                logger.info(
                    f"  Opus critique NOT SUFFICIENT: '{agent_name}' — "
                    f"{gap_count} gaps identified — {critique.summary}"
                )
            return critique

        except Exception as e:
            logger.warning(
                f"Opus L1 critique failed for {agent_name}: {e}. "
                f"Returning default not-sufficient critique."
            )
            return Critique(
                agent_name=agent_name,
                sufficient=False,
                summary=f"Critique failed: {e}",
            )

    async def critique_l2(
        self,
        output: str,
        agent_name: str,
        runner: "ResearchRunner",
    ) -> Critique:
        """Opus critique of L2 deep dive output.

        Same pattern as critique_l1 but with investigation-specific prompt.
        Cost: ~$0.15-0.30 per call.
        """
        truncated = output[:12000]
        prompt = _L2_CRITIQUE_PROMPT.format(agent_name=agent_name, output=truncated)

        try:
            text, costs = await runner.run_synthesis(
                prompt,
                task_id=f"critique_l2_{agent_name[:20]}",
                model=OPUS_MODEL,
            )
            critique = _parse_critique(text, agent_name)
            if critique.sufficient:
                logger.info(f"  Opus L2 critique SUFFICIENT: '{agent_name}' — {critique.summary}")
            else:
                gap_count = len(critique.gaps)
                logger.info(
                    f"  Opus L2 critique NOT SUFFICIENT: '{agent_name}' — "
                    f"{gap_count} gaps — {critique.summary}"
                )
            return critique

        except Exception as e:
            logger.warning(
                f"Opus L2 critique failed for {agent_name}: {e}. "
                f"Returning default not-sufficient critique."
            )
            return Critique(
                agent_name=agent_name,
                sufficient=False,
                summary=f"Critique failed: {e}",
            )

    def check_l3(self, output: str, pipeline_mode: str = "strategic_briefing") -> QualityReport:
        """Verify final synthesis output."""
        if pipeline_mode == "situation_assessment":
            checks = {
                "has_situation_map": bool(re.search(r"SITUATION MAP|situation map", output, re.I)),
                "has_tension_points": bool(re.search(r"TENSION POINT|tension point|OBSERVATION", output, re.I)),
                "has_valuation": bool(re.search(r"VALUATION|valuation|precedent.*transaction", output, re.I)),
                "has_buyer_universe": bool(re.search(r"BUYER UNIVERSE|buyer|acquirer", output, re.I)),
                "has_deal_catalyst": bool(re.search(r"DEAL CATALYST|catalyst|timing|trigger", output, re.I)),
                "has_citations": bool(re.search(r"\[Source|citation", output, re.I)),
                "has_financials": bool(re.search(r"EBITDA|revenue|multiple|\$\d", output, re.I)),
                "has_precedent_table": bool(re.search(r"EV/EBITDA|EV/Revenue|precedent", output, re.I)),
                "has_attribution": bool(re.search(r"Pokee|methodology|research agent", output, re.I)),
                "min_length": len(output.split()) > 3000,
            }
        else:
            checks = {
                "has_situation": bool(re.search(r"SITUATION OVERVIEW|situation", output, re.I)),
                "has_ideas": bool(re.search(r"STRATEGIC IDEAS|TOP.*IDEAS|IDEA", output, re.I)),
                "has_evidence": bool(re.search(r"EVIDENCE|evidence", output, re.I)),
                "has_risk": bool(re.search(r"RISK LANDSCAPE|risk", output, re.I)),
                "has_next_steps": bool(re.search(r"WHAT TO DO NEXT|next steps|90.day", output, re.I)),
                "has_citations": bool(re.search(r"\[Source|citation", output, re.I)),
                "has_magnitude": bool(re.search(r"MAGNITUDE|\$\d", output, re.I)),
                "has_blind_spots": bool(re.search(r"BLIND SPOT|LIMITATION", output, re.I)),
                "has_execution": bool(re.search(
                    r"EXECUTION.*REQUIRE|execution requirement", output, re.I
                )),
                "min_length": len(output.split()) > 3000,
            }

        pass_rate = sum(checks.values()) / len(checks) if checks else 0
        passed = pass_rate >= 0.5

        report = QualityReport(
            layer="l3b",
            checks=checks,
            pass_rate=pass_rate,
            passed=passed,
            details=_format_check_details(checks),
        )

        if not passed:
            logger.warning(f"L3 quality check FAILED ({pass_rate:.0%}): {report.details}")
        else:
            logger.info(f"L3 quality check passed ({pass_rate:.0%})")

        return report


def _format_check_details(checks: dict[str, bool]) -> str:
    """Format check results for logging."""
    failed = [k for k, v in checks.items() if not v]
    if not failed:
        return "All checks passed"
    return f"Failed: {', '.join(failed)}"


def _parse_critique(text: str, agent_name: str) -> Critique:
    """Parse Opus critique response into a Critique object.

    Extracts structured sections from the freeform Opus output.
    Designed to be robust to minor formatting variations.
    """
    # Parse SUFFICIENT
    sufficient_match = re.search(
        r"##\s*SUFFICIENT.*?Answer:\s*(YES|NO)", text, re.DOTALL | re.IGNORECASE
    )
    if not sufficient_match:
        # Fallback: look for YES/NO right after the section header
        sufficient_match = re.search(
            r"SUFFICIENT.*?\b(YES|NO)\b", text, re.IGNORECASE
        )
    sufficient = sufficient_match.group(1).upper() == "YES" if sufficient_match else False

    # Parse bullet lists from each section
    gaps = _extract_bullets(text, "GAPS")
    weak_claims = _extract_bullets(text, "WEAK_CLAIMS")
    missing_context = _extract_bullets(text, "MISSING_CONTEXT")
    follow_up_queries = _extract_bullets(text, "FOLLOW_UP_QUERIES")

    # Parse SUMMARY
    summary_match = re.search(
        r"##\s*SUMMARY\s*\n+(.*?)(?:\n##|\Z)", text, re.DOTALL
    )
    summary = summary_match.group(1).strip() if summary_match else ""
    # Take just the first line/sentence of the summary
    summary = summary.split("\n")[0].strip()

    return Critique(
        agent_name=agent_name,
        sufficient=sufficient,
        gaps=gaps,
        weak_claims=weak_claims,
        missing_context=missing_context,
        follow_up_queries=follow_up_queries,
        summary=summary,
    )


def _extract_bullets(text: str, section_name: str) -> list[str]:
    """Extract bullet-point items from a named section in Opus output."""
    # Match from "## SECTION_NAME" to the next "##" or end of text
    pattern = rf"##\s*{section_name}\s*\n+(.*?)(?:\n##|\Z)"
    section_match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not section_match:
        return []

    section_text = section_match.group(1)
    # Extract lines starting with "- " (standard bullet format)
    items = []
    for line in section_text.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif line.startswith("* "):
            items.append(line[2:].strip())
    return items


def format_critique_as_continuation(critique: Critique) -> str:
    """Format an Opus critique as a continuation prompt for the research agent.

    This replaces the generic "identify 2-3 most critical unanswered questions"
    continuation prompt with directed feedback from the Opus critic.
    """
    parts = [
        "A senior reviewer has identified specific gaps in your research so far. "
        "Focus your next round on addressing these gaps. Do NOT repeat research "
        "you've already done — build on your existing findings.\n"
    ]

    if critique.gaps:
        parts.append("GAPS TO ADDRESS:")
        for gap in critique.gaps:
            parts.append(f"- {gap}")
        parts.append("")

    if critique.weak_claims:
        parts.append("CLAIMS NEEDING EVIDENCE:")
        for claim in critique.weak_claims:
            parts.append(f"- {claim}")
        parts.append("")

    if critique.missing_context:
        parts.append("MISSING CONTEXT:")
        for ctx in critique.missing_context:
            parts.append(f"- {ctx}")
        parts.append("")

    if critique.follow_up_queries:
        parts.append("SUGGESTED SEARCHES (use these as starting points):")
        for query in critique.follow_up_queries:
            parts.append(f"- {query}")
        parts.append("")

    parts.append(
        "Search for the items above, then produce your complete, consolidated "
        "output incorporating everything you've found across all rounds."
    )

    return "\n".join(parts)
