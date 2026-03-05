# L0.5: Agent Design Meta-Prompt

## Purpose
This is NOT a deep research prompt. It's a synthesis/generation prompt run against a reasoning model (Claude Opus with extended thinking, or equivalent). It takes the L0 company profile as input and generates 6-8 customized L1 deep research prompts.

This is the most important prompt in the system. The quality of the final ideas depends almost entirely on whether L0.5 generates L1 prompts with sufficient specificity and breadth.

---

## PROMPT SUMMARY

The full prompt is at `/prompts/l05_agent_design.md`. Key structural elements:

**Step 1: Select Research Lenses** — Choose 6-8 from three categories:
- CONVENTIONAL LENSES (3-5): Core business, governance, competitive, value chains, supply chain, regulatory, customer/demand, financial engineering, technology/IP/data
- LATERAL LENSES (1-2 mandatory): Cross-industry analogues, weird plays / non-obvious applications
- ENVIRONMENT LENSES (1-2): Macro/adjacent/local ecosystem, geopolitical, ESG, platform dynamics
- CUSTOM LENSES: Encouraged when the company has genuinely unusual characteristics

**Step 2: Write Each Agent Prompt** following 7 mandatory principles:

1. **Operational Specificity** — Granular, not executive-summary-level
2. **"Always Ask About" Framework** — Two-tier structure:
   - *Tier 1 (mandatory for every prompt)*: Five generative questions:
     1. What is this company's most undervalued asset?
     2. Who outside their current market would pay for what they already have?
     3. What would a completely different type of owner do with this company?
     4. What would break if this company disappeared tomorrow?
     5. What is the real binding constraint — and is it the one management thinks it is?
   - *Tier 2 (apply where relevant)*: Operational patterns (waste streams, idle capacity, procurement scale, local ecosystem gaps, infrastructure-as-service, capability transfer, relationship arbitrage, seasonal slack)
3. **Anomaly Hunting** — Flag surprises including: customer behavior mismatches, perception gaps, data/network assets more valuable than products, org constraints blocking strategy
4. **Role & Persona** — Expert persona per lens (includes customer insights researcher, brand strategist)
5. **Output Format** — Headers, numbers, data gaps, anomaly section, citations
6. **Company-Specific Detail** — Reference specific L0 facts
7. **Lateral Prompt Quality** — Specific structural features to match on

**Step 3: Output Format** — Agent headers with justification, priority, and complete prompt in code blocks, followed by coverage assessment and consolidation notes.

---

## VARIABLES

| Variable | Source | Required |
|----------|--------|----------|
| `{L0_OUTPUT}` | Output from L0 prompt | Yes |

## EXPECTED OUTPUT SIZE
5,000-15,000 words (the prompts themselves are the bulk of the output).

## KEY CHANGES FROM PREVIOUS VERSION
- Principle 2 restructured into two tiers: generative questions (mandatory) + operational patterns (where relevant)
- Generative questions work for any company type — intangible-asset companies get probed on data, brand, community, not just physical assets
- Anomaly hunting expanded: customer behavior mismatches, perception gaps, data assets > products, org constraints
- Two new personas added: customer insights researcher, brand strategist

## SUCCESS CRITERIA
Each generated L1 prompt should:
1. Be immediately runnable as a standalone deep research task
2. Reference specific facts from the L0 profile (facility names, geographies, financial figures, or data assets/brand/community where relevant)
3. Address Tier 1 generative questions where applicable
4. Include relevant Tier 2 operational patterns
5. End with an anomaly-hunting section
6. Be 500-1500 words (long enough to be specific, short enough for the research agent to follow)
