"""Quality checker — validates output quality at each layer."""

from __future__ import annotations

import re
import logging

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

    def check_l15(self, output: str) -> QualityReport:
        """Verify consolidation has required tension points."""
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
            "has_time_horizons": bool(re.search(r"IMMEDIATE|NEAR.TERM|MEDIUM.TERM|TIME HORIZON", output, re.I)),
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
        passed = pass_rate >= 0.4

        return QualityReport(
            layer="l2",
            checks=checks,
            pass_rate=pass_rate,
            passed=passed,
            details=f"Agent '{agent_name}': {_format_check_details(checks)}",
        )

    def check_l3(self, output: str) -> QualityReport:
        """Verify final synthesis output."""
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
            layer="l3",
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
