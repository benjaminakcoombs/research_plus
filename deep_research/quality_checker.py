"""Quality checker — validates output quality at each layer."""

from __future__ import annotations

import re
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .research_runner import ResearchRunner

from .models import QualityReport

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

    async def check_l1_semantic(
        self,
        output: str,
        agent_name: str,
        runner: "ResearchRunner",
    ) -> QualityReport:
        """LLM-based quality check using Haiku for speed and cost (~$0.01/check).

        Evaluates research output on 5 dimensions using a fast, cheap model.
        Falls back to regex check if Haiku call fails.
        """
        prompt = f"""Rate this research agent output 1-5 on each dimension. Be harsh — a 3 means "acceptable for a first-year analyst," a 5 means "a senior banker would cite this in a client meeting."

AGENT: {agent_name}
OUTPUT (first 3000 chars):
{output[:3000]}

Rate each dimension (1-5) and give a one-sentence justification:

1. SPECIFICITY: Does it contain specific numbers, dates, company names, and dollar amounts — not generalities?
2. NOVELTY: Would a sector specialist learn something they didn't already know?
3. SOURCE_QUALITY: Are claims attributed to specific, verifiable sources (SEC filings, state databases, named publications)?
4. ACTIONABILITY: Could a deal team use this in a pitch book or diligence checklist?
5. ANOMALY_VALUE: Did it surface surprising contradictions, gaps, or non-obvious patterns?

Output EXACTLY in this format (one per line):
SPECIFICITY: [1-5] — [justification]
NOVELTY: [1-5] — [justification]
SOURCE_QUALITY: [1-5] — [justification]
ACTIONABILITY: [1-5] — [justification]
ANOMALY_VALUE: [1-5] — [justification]
OVERALL: PASS or FAIL (PASS requires average >= 3.0 and no dimension below 2)"""

        try:
            text, costs = await runner.run_synthesis(
                prompt,
                task_id=f"quality_check_{agent_name[:20]}",
                model="claude-haiku-4-5-20251001",
            )

            # Parse scores
            scores = {}
            dimensions = ["SPECIFICITY", "NOVELTY", "SOURCE_QUALITY", "ACTIONABILITY", "ANOMALY_VALUE"]
            for dim in dimensions:
                score_match = re.search(rf"{dim}\s*:\s*(\d)", text)
                if score_match:
                    scores[dim] = int(score_match.group(1))

            if not scores:
                logger.warning(f"Could not parse Haiku quality scores for {agent_name}, falling back to regex")
                return self.check_l1(output, agent_name)

            # Treat missing dimensions as score 1 (worst) to avoid inflating the average
            missing_dims = set(dimensions) - set(scores.keys())
            if missing_dims:
                logger.warning(f"Haiku output missing dimensions for {agent_name}: {missing_dims}. Treating as 1.")
                for dim in missing_dims:
                    scores[dim] = 1

            avg_score = sum(scores.values()) / len(scores)
            min_score = min(scores.values())
            passed = avg_score >= 3.0 and min_score >= 2

            # Convert scores to check-style dict for QualityReport
            checks = {f"{dim.lower()}_gte_2": score >= 2 for dim, score in scores.items()}
            checks["avg_gte_3"] = avg_score >= 3.0

            overall_match = re.search(r"OVERALL\s*:\s*(PASS|FAIL)", text, re.IGNORECASE)
            if overall_match:
                passed = overall_match.group(1).upper() == "PASS"

            pass_rate = sum(checks.values()) / len(checks) if checks else 0

            score_str = ", ".join(f"{d}={s}" for d, s in scores.items())
            details = f"Agent '{agent_name}': avg={avg_score:.1f}, min={min_score} [{score_str}]"

            report = QualityReport(
                layer="l1_semantic",
                checks=checks,
                pass_rate=pass_rate,
                passed=passed,
                details=details,
            )

            if passed:
                logger.info(f"  Semantic quality PASSED: {details}")
            else:
                logger.warning(f"  Semantic quality FAILED: {details}")

            return report

        except Exception as e:
            logger.warning(f"Haiku quality check failed for {agent_name}: {e}. Falling back to regex.")
            return self.check_l1(output, agent_name)

    async def check_l2_semantic(
        self,
        output: str,
        agent_name: str,
        runner: "ResearchRunner",
    ) -> QualityReport:
        """LLM-based quality check for L2 deep dive outputs."""
        prompt = f"""Rate this deep research investigation output 1-5 on each dimension. Be harsh.

AGENT: {agent_name}
OUTPUT (first 3000 chars):
{output[:3000]}

Rate each dimension (1-5):

1. EVIDENCE_DEPTH: Does it present specific, verifiable evidence (not just claims)?
2. QUANTITATIVE_RIGOR: Does it show its work on financial calculations with stated assumptions?
3. PRECEDENT_QUALITY: Does it cite specific, relevant comparable transactions with disclosed metrics?
4. COUNTER_EVIDENCE: Does it seriously investigate what would disprove the hypothesis?
5. DEAL_RELEVANCE: Would this change a buyer's willingness to pay or a banker's timing advice?

Output EXACTLY in this format (one per line):
EVIDENCE_DEPTH: [1-5] — [justification]
QUANTITATIVE_RIGOR: [1-5] — [justification]
PRECEDENT_QUALITY: [1-5] — [justification]
COUNTER_EVIDENCE: [1-5] — [justification]
DEAL_RELEVANCE: [1-5] — [justification]
OVERALL: PASS or FAIL (PASS requires average >= 3.0 and no dimension below 2)"""

        try:
            text, costs = await runner.run_synthesis(
                prompt,
                task_id=f"quality_check_l2_{agent_name[:20]}",
                model="claude-haiku-4-5-20251001",
            )

            scores = {}
            dimensions = ["EVIDENCE_DEPTH", "QUANTITATIVE_RIGOR", "PRECEDENT_QUALITY", "COUNTER_EVIDENCE", "DEAL_RELEVANCE"]
            for dim in dimensions:
                score_match = re.search(rf"{dim}\s*:\s*(\d)", text)
                if score_match:
                    scores[dim] = int(score_match.group(1))

            if not scores:
                logger.warning(f"Could not parse Haiku L2 quality scores for {agent_name}, falling back to regex")
                return self.check_l2(output, agent_name)

            # Treat missing dimensions as score 1 (worst) to avoid inflating the average
            missing_dims = set(dimensions) - set(scores.keys())
            if missing_dims:
                logger.warning(f"Haiku L2 output missing dimensions for {agent_name}: {missing_dims}. Treating as 1.")
                for dim in missing_dims:
                    scores[dim] = 1

            avg_score = sum(scores.values()) / len(scores)
            min_score = min(scores.values())
            passed = avg_score >= 3.0 and min_score >= 2

            checks = {f"{dim.lower()}_gte_2": score >= 2 for dim, score in scores.items()}
            checks["avg_gte_3"] = avg_score >= 3.0

            overall_match = re.search(r"OVERALL\s*:\s*(PASS|FAIL)", text, re.IGNORECASE)
            if overall_match:
                passed = overall_match.group(1).upper() == "PASS"

            pass_rate = sum(checks.values()) / len(checks) if checks else 0
            score_str = ", ".join(f"{d}={s}" for d, s in scores.items())
            details = f"Agent '{agent_name}': avg={avg_score:.1f}, min={min_score} [{score_str}]"

            report = QualityReport(
                layer="l2_semantic",
                checks=checks,
                pass_rate=pass_rate,
                passed=passed,
                details=details,
            )

            if passed:
                logger.info(f"  L2 semantic quality PASSED: {details}")
            else:
                logger.warning(f"  L2 semantic quality FAILED: {details}")

            return report

        except Exception as e:
            logger.warning(f"Haiku L2 quality check failed for {agent_name}: {e}. Falling back to regex.")
            return self.check_l2(output, agent_name)

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
