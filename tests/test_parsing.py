"""Test orchestrator parsing logic."""

from deep_research.orchestrator import DeepResearchOrchestrator, _extract_field
from deep_research.config import Config


def test_archetype_extraction():
    orch = DeepResearchOrchestrator(Config())

    l0_conglomerate = """
## 1. COMPANY IDENTITY & CLASSIFICATION
- Company archetype: **CONGLOMERATE** (multiple distinct businesses)
- Market cap: 130M
"""
    arch = orch._extract_archetype(l0_conglomerate)
    assert arch.value == "conglomerate", f"Expected conglomerate, got {arch.value}"

    l0_extractor = """
## 1. COMPANY IDENTITY & CLASSIFICATION
- Company archetype — EXTRACTOR/GROWER (agriculture, mining)
"""
    arch2 = orch._extract_archetype(l0_extractor)
    assert arch2.value == "extractor_grower", f"Expected extractor_grower, got {arch2.value}"

    l0_saas = """
## 1. COMPANY IDENTITY
- archetype: SAAS/SOFTWARE (sells software or digital services)
"""
    arch3 = orch._extract_archetype(l0_saas)
    assert arch3.value == "saas_software", f"Expected saas_software, got {arch3.value}"
    print("Archetype extraction: PASSED")


def test_agent_prompt_parsing():
    orch = DeepResearchOrchestrator(Config())

    l05_output = (
        "AGENT 1: Core Business & Physical Assets\n"
        "JUSTIFICATION: Critical for understanding.\n"
        "PRIORITY: Critical\n"
        "\n"
        "```\n"
        "You are a senior equity research analyst conducting deep due diligence on Test Corp.\n"
        "Your mandate is to build a comprehensive map of the business model.\n"
        "\n"
        "RESEARCH THE FOLLOWING:\n"
        "1. Business segments\n"
        "2. Physical assets\n"
        "3. Key input costs\n"
        "This is substantial prompt content that should be parsed correctly.\n"
        "More details about research structure and output format requirements.\n"
        "End with NOTABLE ANOMALIES section.\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
        "AGENT 2: Governance & Stakeholder Dynamics\n"
        "JUSTIFICATION: Opacity is a red flag.\n"
        "PRIORITY: High\n"
        "\n"
        "```\n"
        "You are a senior corporate governance analyst conducting deep research on Test Corp.\n"
        "Your mandate is to understand the strategic direction and governance.\n"
        "\n"
        "RESEARCH THE FOLLOWING:\n"
        "1. Board composition\n"
        "2. Controlling interests\n"
        "3. Stakeholder tensions\n"
        "This is also substantial prompt content for governance research.\n"
        "More governance details and output format.\n"
        "End with GOVERNANCE TENSIONS section.\n"
        "```\n"
        "\n"
        "COVERAGE ASSESSMENT:\n"
        "- Well covered: operations, governance\n"
    )

    prompts, names = orch._parse_agent_prompts(l05_output)
    assert len(prompts) == 2, f"Expected 2 prompts, got {len(prompts)}"
    assert "Core Business" in names[0], f"Expected 'Core Business' in name, got {names[0]}"
    assert "Governance" in names[1], f"Expected 'Governance' in name, got {names[1]}"
    assert "senior equity research analyst" in prompts[0]
    assert "corporate governance analyst" in prompts[1]
    print("Agent prompt parsing: PASSED")


def test_tension_point_parsing():
    orch = DeepResearchOrchestrator(Config())

    l15_output = """
# DELIVERABLE 2: TENSION POINTS

## #1. The Land Value Problem
**TENSION:** Company owns 10,000 hectares near a growing city but carries it at historical cost.
**HYPOTHESIS:** Real estate value exceeds market cap. A phased development could unlock massive value.
**CATEGORY:** STRUCTURAL UNLOCK
**POTENTIAL MAGNITUDE:** Transformational
**TIME HORIZON:** Near-term (6-18 months)
**CONFIDENCE:** High — based on comparable land sales in the area
**LAYER 2 RESEARCH QUESTION:** What are recent land sale prices per acre within 20km?

## #2. Waste Stream Monetization
**TENSION:** Processing generates 5,000 tonnes of shell waste annually, currently discarded.
**HYPOTHESIS:** Shell waste can be converted to activated carbon at 10x the disposal cost.
**CATEGORY:** OFFENSIVE OPPORTUNITY
**POTENTIAL MAGNITUDE:** Major
**TIME HORIZON:** Medium-term (1-3 years)
**CONFIDENCE:** Medium — need to verify processing economics
**LAYER 2 RESEARCH QUESTION:** What is the capital cost of a pyrolysis unit?

## #3. Competitive Blind Spot
**TENSION:** Peers have moved downstream but this company has not.
**HYPOTHESIS:** Forward integration could capture 3-5x the current margin.
**CATEGORY:** INFORMATION ARBITRAGE
**POTENTIAL MAGNITUDE:** Major
**TIME HORIZON:** Near-term (6-18 months)
**CONFIDENCE:** Medium
**LAYER 2 RESEARCH QUESTION:** Who has successfully integrated forward?
"""

    points = orch._parse_tension_points(l15_output)
    assert len(points) == 3, f"Expected 3 tension points, got {len(points)}"
    assert points[0].title == "The Land Value Problem"
    assert "STRUCTURAL" in points[0].category.upper()
    assert "Transformational" in points[0].magnitude
    assert points[1].title == "Waste Stream Monetization"
    assert "activated carbon" in points[1].hypothesis
    assert points[2].id == 3
    print("Tension point parsing: PASSED")


def test_extract_field():
    content = "**TENSION:** Some tension here.\n**HYPOTHESIS:** Some hypothesis."
    result = _extract_field(content, r"TENSION[:\s]", r"HYPOTHESIS")
    assert "Some tension here" in result, f"Expected tension text, got: {result}"

    content2 = "**CATEGORY:** OFFENSIVE OPPORTUNITY\n**POTENTIAL MAGNITUDE:** Major"
    result2 = _extract_field(content2, r"CATEGORY[:\s]", r"(?:POTENTIAL\s+)?MAGNITUDE")
    assert "OFFENSIVE" in result2.upper(), f"Expected OFFENSIVE, got: {result2}"
    print("Extract field: PASSED")


def test_l2_prompt_parsing():
    orch = DeepResearchOrchestrator(Config())

    gen_output = (
        "L2 AGENT 1: Carbon Credit Feasibility\n"
        "SOURCE TENSION POINT(S): #2\n"
        "PRIORITY: Critical\n"
        "\n"
        "```\n"
        "You are an environmental markets analyst investigating carbon credit potential.\n"
        "CONTEXT: The company owns 12,000 hectares of forestry in East Africa.\n"
        "HYPOTHESIS: Carbon credits could generate $1-3M annually.\n"
        "SPECIFIC RESEARCH QUESTIONS:\n"
        "1. What are current Verra VCS credit prices?\n"
        "2. What comparable projects exist?\n"
        "3. What is the registration cost?\n"
        "This is a substantial enough prompt to be parsed.\n"
        "```\n"
        "\n"
        "L2 AGENT 2: Tea Extract Economics\n"
        "SOURCE TENSION POINT(S): #1\n"
        "PRIORITY: High\n"
        "\n"
        "```\n"
        "You are an agricultural processing analyst investigating tea extraction.\n"
        "CONTEXT: The company produces 76M kg of tea at auction prices of $2/kg.\n"
        "HYPOTHESIS: An extraction facility could multiply value 4-12x.\n"
        "SPECIFIC RESEARCH QUESTIONS:\n"
        "1. What is the capital cost of extraction equipment?\n"
        "2. Who are the major buyers of tea extract?\n"
        "3. What are comparable facility economics?\n"
        "This is also substantial enough to be parsed.\n"
        "```\n"
        "\n"
        "L2 COVERAGE NOTE:\n"
        "- All high-priority points covered\n"
    )

    prompts, names = orch._parse_l2_prompts(gen_output)
    assert len(prompts) == 2, f"Expected 2 L2 prompts, got {len(prompts)}"
    assert "Carbon Credit" in names[0]
    assert "Tea Extract" in names[1]
    assert "environmental markets analyst" in prompts[0]
    assert "agricultural processing analyst" in prompts[1]
    print("L2 prompt parsing: PASSED")


if __name__ == "__main__":
    test_archetype_extraction()
    test_agent_prompt_parsing()
    test_tension_point_parsing()
    test_extract_field()
    test_l2_prompt_parsing()
    print("\n=== ALL PARSING TESTS PASSED ===")
