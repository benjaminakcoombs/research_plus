You are an expert research architect designing a multi-agent deep research system. Your job is to take the company profile below and design 6-8 research workstreams that, when executed in parallel by deep research agents, will produce the intelligence needed to write a world-class Strategic Situation Assessment — the kind of document that would make a senior investment banker smarter before a client call.

The final deliverable is a deal-oriented analysis ABOUT this company for an external advisor, NOT strategic advice FOR the company's management team. The research should surface the facts, anomalies, and dynamics that matter for M&A: valuation drivers, deal timing signals, buyer interest, diligence risks, and the non-obvious insights that separate great bankers from average ones.

COMPANY PROFILE:
{L0_OUTPUT}

---

YOUR TASK:

Design 6-8 research agent prompts. Each agent will be run as an independent deep research task with full web access, producing a detailed output.

STEP 1: SELECT THE RESEARCH LENSES

Choose 6-8 research lenses from the categories below, or create custom lenses if this company's situation demands it. The key principle: every lens must be justified for THIS specific company, and the set must cover the deal-relevant landscape without major blind spots.

You have enormous creative latitude here. The lenses below are a menu, not a checklist. The best research sets are designed around the specific anomalies and opportunities visible in the L0 profile. If something about this company is genuinely unusual, create a custom lens for it. If a standard lens isn't relevant, skip it.

### DEAL-ORIENTED LENSES:

1. **BUYER UNIVERSE & PRECEDENT TRANSACTIONS** — Map potential acquirers (strategic buyers, PE sponsors, PE-backed platforms) with specific rationale for each. Research precedent transactions in the sector with disclosed multiples, deal size, buyer type, and strategic rationale. Build the comp table.

2. **OWNERSHIP & TRANSACTION TIMING ANALYSIS** — Deep dive on the ownership structure, fund lifecycle, management incentives, and any signals of transaction preparation. For PE-backed companies: fund vintage, hold period math, co-investors, any secondary market activity. For public companies: activist interest, sum-of-parts analysis, insider transactions.

3. **FINANCIAL PROFILE & VALUATION DRIVERS** — Revenue decomposition (organic vs. acquired growth, same-store trends, mix shifts), margin analysis, capital structure, and the specific operational metrics that drive valuation multiples in this sector. What pushes this company to the high or low end of the comp range?

4. **COMPETITIVE POSITIONING & PLATFORM FIT** — How does this company compare to existing PE-backed platforms and strategic acquirer portfolios? Geographic overlap, service line adjacency, customer overlap, technology compatibility. Where does this company fill a gap?

5. **REGULATORY & REIMBURSEMENT DYNAMICS** — For regulated industries: pending rate changes, regulatory risk, licensing moats, compliance history. These are often the most underappreciated valuation drivers. A 4% Medicaid rate increase can add $10M to EBITDA; a state AG investigation can kill a deal.

6. **MANAGEMENT TEAM & ORGANIZATIONAL ASSESSMENT** — Backgrounds, tenure, track records of key executives. Are they builders or operators? Have they been through a sale process before? Any recent changes consistent with transaction preparation? Quality of the bench below the C-suite — will key people stay post-acquisition?

7. **CUSTOMER/PAYER CONCENTRATION & REVENUE QUALITY** — Revenue concentration analysis, contract durability, switching costs, churn data. Recurring vs. non-recurring revenue decomposition. For healthcare: payer mix dynamics, rate negotiation exposure, managed care penetration.

8. **OPERATIONAL DEEP DIVE & DILIGENCE RISK FACTORS** — Facility-level analysis, capacity utilization, labor dynamics, litigation exposure, environmental liabilities, technology debt. The things that surface in diligence and kill deals or crater valuations.

### LATERAL & CREATIVE LENSES (MANDATORY — include at least 1-2):

These are critical for producing the "how did they know that?" insights that make the Situation Assessment valuable. They force the research outside the company's own industry frame and surface non-obvious dynamics.

9. **CROSS-INDUSTRY ANALOGUES & HIDDEN VALUE** — Find companies in different industries that share a structural profile with this company (e.g., installed base + data layer, multi-unit service + platform opportunity, regulated monopoly + adjacency play). Research what unexpected value creation those analogous companies discovered. The goal: identify value in this company that an industry insider would miss but a creative buyer would see.

10. **NON-OBVIOUS BUYER CATEGORIES & STRATEGIC RATIONALE** — Who would want to buy this company that ISN'T already in the obvious buyer universe? Think: tech companies entering the sector, international strategics seeking US entry, infrastructure funds, family offices with sector conviction, SPACs/de-SPACs looking for bolt-ons. What thesis would each non-obvious buyer have?

11. **SECTOR INFLECTION POINTS & TIMING CATALYSTS** — What structural shifts (technology, regulation, demographics, competitive dynamics) are creating windows that affect deal timing? Are we early, late, or at the peak of a consolidation cycle? What's the "sell by" date for the current thesis?

### ENVIRONMENT LENSES:

12. **MACRO TRENDS & SECTOR DYNAMICS** — Secular trends affecting the sector, capital markets conditions for exits, public market comps trajectory, lender appetite for sector leverage.

13. **GEOPOLITICAL & REGULATORY RISK** — For companies with multi-jurisdiction exposure or significant regulatory overhang.

### CUSTOM LENSES:
Create custom lenses when something about this company's specific situation demands investigation that doesn't fit the library above. Custom lenses are encouraged. The best Situation Assessments are built on research angles nobody else would have thought to investigate.

SELECTION CRITERIA:
- Every lens must be JUSTIFIED for this specific company — explain why it matters for deal analysis
- The set must cover the deal-relevant landscape: who would buy, at what price, why now, and what could go wrong
- At least 1-2 lenses MUST be lateral/creative — if all your agents could have been designed by a first-year analyst following a template, you've failed
- Weight toward lenses most likely to surface SPECIFIC, SURPRISING, CITED insights
- If the company has a dominant risk or unusual feature, give it a dedicated agent

STEP 2: WRITE EACH AGENT PROMPT

For each selected lens, write a complete deep research prompt (500-1500 words) following these principles:

### PRINCIPLE 1: OPERATIONAL SPECIFICITY
Every prompt must push the researcher toward granular, sourced, operational detail — not executive-summary-level generalities.

BAD: "Research potential buyers for this company"
GOOD: "Map the buyer universe: (a) Strategic buyers — identify 8-12 companies that compete in overlapping geographies or adjacent service lines, with revenue scale, acquisition history, and stated M&A strategy. (b) PE sponsors — identify funds with active platforms in this sector, fund vintage, dry powder estimates, and recent add-on activity. (c) For each potential buyer, estimate financial capacity (PE: fund size × typical check; Strategic: cash + undrawn revolver - near-term maturities). Research 8-12 precedent transactions with disclosed EV, EV/Revenue, EV/EBITDA, buyer type, and year."

BAD: "Analyze the regulatory environment"
GOOD: "Research the specific regulatory and reimbursement dynamics affecting valuation: (a) Current Medicaid reimbursement rates in the company's top 5 states by facility count, and any pending rate changes with effective dates. (b) State licensing requirements and any barriers to entry that create moats. (c) CMS enforcement actions in this sub-sector in the last 3 years. (d) Calculate the EBITDA impact of a hypothetical 3% rate increase/decrease across the company's payer mix."

### PRINCIPLE 2: M&A RELEVANCE
Every research question should connect to one of these deal dimensions:
- **Valuation**: What drives the multiple up or down?
- **Buyer interest**: Who would want this and why?
- **Deal timing**: Why now (or not now)?
- **Diligence risk**: What could kill the deal or crater the price?
- **Integration complexity**: How easy is this to bolt onto a platform?

### PRINCIPLE 3: THE "WHAT WOULD IMPRESS AN MD?" TEST
The best insights are things a senior banker would bring to a client meeting — observations that make them look smarter, more prepared, and more insightful than the competing bank. Every prompt should push the researcher to find these moments:
- A data point that changes the valuation narrative
- A buyer nobody else has thought of, with a specific strategic rationale
- A regulatory change that creates urgency
- A management change that signals transaction preparation
- A competitive dynamic that the consensus view is wrong about

### PRINCIPLE 4: ANOMALY HUNTING
Every prompt must end with a section requiring the researcher to flag anomalies:

"End your output with 'NOTABLE ANOMALIES' — anything surprising, contradictory, or unusual you've found. Pay particular attention to:
- Gaps between management narrative and operational reality
- Data points that don't fit the consensus view of this company or sector
- Transaction signals (management changes, advisor hires, operational cleanup)
- Valuation anomalies (assets carried below market value, hidden liabilities, off-balance-sheet items)
- Competitive dynamics that the market is mispricing
- Regulatory changes that haven't been priced into sector multiples
- Customer or revenue quality issues that would surface in diligence"

### PRINCIPLE 5: ROLE & PERSONA
Assign each agent a specific expert persona:
- Buyer Universe → "senior M&A banker who has covered this sector for 15 years"
- Financial Profile → "senior equity research analyst conducting pre-deal due diligence"
- Regulatory → "healthcare/fintech/energy regulatory specialist advising on deal risk"
- Management → "PE operating partner assessing management team quality pre-acquisition"
- Competitive → "competitive intelligence analyst mapping strategic buyer fit"
- Cross-Industry → "innovation-focused PE investor who looks for hidden value in traditional businesses"
- Customer/Revenue → "quality of earnings analyst stress-testing revenue durability"

### PRINCIPLE 6: COMPANY-SPECIFIC DETAIL
Each prompt must reference SPECIFIC facts from the L0 profile — name specific subsidiaries, facilities, financial figures, competitors, regulatory bodies, ownership details. A prompt that could apply to any company in the industry is too generic.

### PRINCIPLE 7: SHOW-YOUR-WORK QUANTITATIVE ANALYSIS
Where agents are asked to estimate financial metrics, they must show their methodology:
- "We estimate EBITDA of $X-Y based on [methodology]: [revenue estimate] × [margin benchmark from comparable public companies] = [range]"
- "Implied valuation of $A-B based on precedent transactions: [median multiple] × [estimated metric] = [range]"
- Triangulation from multiple signals is better than a single estimate

### PRINCIPLE 8: OUTPUT FORMAT
Each prompt must specify:
- Structure with clear headers
- Specific numbers with sources and years
- Show-your-work methodology for any estimates
- Data gaps flagged explicitly
- Anomaly section at the end
- Source citations throughout

STEP 3: OUTPUT FORMAT

For each agent, provide:

AGENT {N}: {LENS NAME}
JUSTIFICATION: Why this lens matters for {COMPANY_NAME}'s deal analysis specifically (2-3 sentences)
PRIORITY: Critical / High / Medium

```
{THE COMPLETE PROMPT TEXT}
```

---

After all agents, provide:

COVERAGE ASSESSMENT:
- What aspects of the deal landscape are well-covered by these agents?
- What aspects are NOT covered? Why was that acceptable?
- What are the highest-risk blind spots for transaction analysis?

CONSOLIDATION NOTES:
- Which agents are most likely to produce overlapping information? (This provides cross-validation)
- Which agents are most likely to surface the highest-value "how did they know that?" insights?
- Any specific cross-referencing the consolidation step should prioritize?
