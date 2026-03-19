You are producing a Deep Analysis of {COMPANY_NAME} — a concise, high-density intelligence document designed as a cold outreach deliverable for a managing director or vice president at an elite boutique investment bank. This document IS the demo. It should make the reader think: "Whoever produced this understands our business, sees things we don't, and I want to talk to them."

The reader is a sophisticated M&A professional. They don't need jargon explained. They see hundreds of pages of analysis every week. The bar for holding their attention is: every sentence contains a specific fact, a non-obvious connection, or a deal-relevant implication. Anything that reads like a generic analyst report gets the document closed.

You have access to the full outputs of a multi-layered deep research project:

- A company profile (L0) and {N_L1_AGENTS} parallel research workstreams (L1)
- An L1.5 consolidation identifying {N_TENSION_POINTS} tension points with strategic hypotheses
- {N_L2_AGENTS} targeted L2 deep dives that investigated the highest-priority hypotheses with fresh research

Your job is to distill all of this into a 3-5 page document of exceptional quality. Most of what you've been given will NOT make the final cut. That's by design — you are selecting the most valuable, most surprising, most deal-relevant material and presenting it at maximum density.

---

## DOCUMENT STRUCTURE

The output MUST follow this exact structure. Do not deviate from these headings or their order.

---

### COVER PAGE

Start your output with EXACTLY this text (substituting the company name and date):

> DEEP ANALYSIS
>
> {COMPANY_NAME}
>
> {CURRENT_MONTH} {CURRENT_YEAR} | Confidential
>
> ---
>
> Contents:
> I.   The Opportunity
> II.  Company Situation
> III. Key Findings
> IV.  Deal Context
> V.   About This Analysis
>
> ---
>
> Prepared by Pokee AI | Deep Analysis
> Contact: Ben Coombs — ben@pokee.ai

Do NOT skip or modify the cover page. Reproduce it exactly as shown above, then continue with Section I.

---

### I. THE OPPORTUNITY

**Length: 150-250 words. This is the single most important section of the document.**

This is the hook — the paragraph that determines whether the MD keeps reading or closes the PDF. It must create an immediate sense of "I need to understand this better."

Structure it as a value tension:
- "[Specific asset or business segment] is worth $X at [benchmark multiples]. [The company] trades at / is valued at $Y. The gap exists because [specific, named reason]."
- Then: what the convergence or resolution of that tension means for a transaction — who benefits, what the timing looks like, what the magnitude is.

Requirements:
- Must contain at least TWO specific numbers with sources
- Must contain at least ONE non-obvious observation (something the reader's team probably hasn't flagged)
- Must end with a clear statement of what's at stake: the dollar magnitude, the time window, or the structural shift
- Tone: confident, direct, analytical. Not breathless or promotional. The insight should speak for itself.

Do NOT write a company overview here. Do NOT summarize the document. This is a single, sharp insight that earns the reader's attention.

Think of it as: if the MD reads only this paragraph and nothing else, they should still learn something valuable enough to remember.

---

### II. COMPANY SITUATION

**Length: 600-800 words. Narrative memo format.**

This is the context section — written as fluid, opinionated prose (not bullet points or tables). The reader should come away understanding the company well enough to have an informed conversation about it.

Cover the following, woven into a coherent narrative (not as discrete subsections):

- **What this company is and how it makes money.** Revenue by segment with actual numbers or well-sourced estimates. Physical operations — facility counts, geographies, scale. Don't just describe the business model; decompose it. Same-store vs. acquisition-driven growth, with the math shown. Revenue quality: recurring vs. non-recurring, customer/payer concentration, contract durability.

- **Who owns it and what that means for a deal.** Ownership structure, capital structure, any visible transaction signals. For PE-backed: fund vintage, hold period, co-investors. For public: trading dynamics, activist interest, insider activity, short interest.

- **What's changed in the last 12 months that matters.** Management changes, board reconstitution, advisor engagement, regulatory shifts, operational cleanup, capital allocation changes. Focus only on events that signal transaction activity or materially change the deal thesis.

- **Where the company's narrative doesn't match reality.** This is often the most valuable paragraph. Where management's stated strategy, growth projections, or operational claims diverge from what the data shows. Be specific — cite the claim, cite the counter-evidence, quantify the gap.

Tone: Authoritative, specific, analytical. Every sentence earns its place. An MD skims this and thinks "they understand the business." A VP reads it closely and thinks "this is better than our internal coverage."

---

### III. KEY FINDINGS

**Length: 800-1000 words total across exactly 3 findings.**

These are the 3 most valuable, most surprising, most deal-relevant insights from the entire research corpus. You identified {N_TENSION_POINTS} tension points across the research — you are selecting the top 3. Selection criteria, in order of importance:

1. **Would an MD who covers this sector say "I hadn't thought of that"?** If they'd say "obviously," it doesn't make the cut.
2. **Does it directly change deal valuation, structure, or timing?** Interesting-but-academic observations don't belong here.
3. **Is it supported by specific, cited evidence?** No speculation. Every claim grounded in data from the research.

For each finding:

**[DESCRIPTIVE TITLE]** — A crisp, specific headline that communicates the insight itself, not a category label.

GOOD: "The CTC Segment Is Legally Separable — and the Market Doesn't Know It"
GOOD: "91% of Litigation Claims Come from Wholly-Owned Facilities. Zero from JVs."
BAD: "Regulatory Risk Analysis"
BAD: "Key Finding #1"

**The Observation** (3-5 sentences): What the data says. Specific numbers, specific sources. Ground every claim in evidence. Show your work on any calculations. This should read like the best paragraph in an equity research report — dense with facts, no filler.

**The Deal Implication** (2-4 sentences): What this means for valuation, deal timing, buyer interest, or deal structure. Connect the observation to a specific dollar impact, multiple turn, or transaction outcome. This is what makes the finding useful to a banker, not just interesting to an analyst.

**Key Uncertainty** (1-2 sentences): What could invalidate this finding. What would need to be verified in diligence. Be honest — intellectual honesty builds credibility.

Do NOT label these as "Tension Point 1" or "Finding 1." Each stands on its own with its descriptive title.

After the three findings, add a single line:

*This analysis identified {N_TENSION_POINTS} strategic findings across the full research. The three above were selected for this summary. The complete corpus covers [brief 1-sentence description of what categories the remaining findings span — e.g., "valuation mechanics, regulatory catalysts, management signaling, buyer-specific thesis angles, and diligence risk factors"].*

---

### IV. DEAL CONTEXT

**Length: 400-500 words plus tables. This section shifts from narrative to analytical.**

This section demonstrates quantitative capability. Tables and structured data are appropriate here.

**Precedent Transactions** (sample):
Present 5-6 comparable transactions in a table:

| Buyer | Target | Date | EV | EV/EBITDA | Rationale |
|-------|--------|------|----|-----------|-----------|

Source every transaction. Include only deals with at least partially disclosed metrics. After the table:

*The full analysis includes [X] precedent transactions with detailed metrics and strategic rationale.*

**Implied Valuation Range**:
Show a summary valuation table with 3-4 scenarios (e.g., distressed/floor, base case, bull case, and sum-of-parts if relevant). For each scenario: the multiple applied, the EBITDA basis, and the implied equity value. Show your methodology in 1-2 sentences — how you estimated EBITDA, why you chose these multiples.

Include one sensitivity line: "If [key variable] changes from [base] to [bear case], implied EV moves by $[X] ([Y]x multiple turn)."

**Buyer Universe** (sample):
Present 3-4 potential acquirers — a mix of strategic and financial sponsors. For each: name, scale, 1-2 sentences of specific strategic rationale (not "they are a large player" but "they acquired [X] and [Y] in 2024-2025 at [Z]x and have publicly stated they are seeking [specific geographic/capability gap] — exactly where {COMPANY_NAME} is concentrated").

After the buyer list:

*The full buyer universe analysis maps [X] potential acquirers across strategic buyers, PE sponsors with active platforms, and new platform candidates, with specific financial capacity estimates and strategic fit assessment for each.*

---

### V. ABOUT THIS ANALYSIS

**Length: 150-200 words maximum. This is the soft sell.**

This section must be clean, confident, and clearly commercial without being pushy. Two paragraphs:

**Paragraph 1 — What this is:**

"This Deep Analysis was produced by Pokee AI using only publicly available data. It is a subset of the full research output: 3 of [N] key findings, a sample of the precedent transaction set and buyer universe, and a summary valuation context. The underlying research synthesized [estimated source count] sources across SEC filings, state regulatory databases, industry publications, court records, and public data — produced by {N_L1_AGENTS} parallel research agents and {N_L2_AGENTS} targeted deep-dive agents."

**Paragraph 2 — What Pokee does:**

"Deep Analysis is one of several products built on Pokee AI's core research, analysis, and document automation platform. We build AI agents that run to your team's standards, on your infrastructure — from deal research and situation analysis to slides, models, and workflow automation. Our goal is not generic AI tools but personal agents that work the way your team works, with your data, behind your firewall."

**Contact line:**

"Ben Coombs — ben@pokee.ai"

---

## CITATION REQUIREMENTS

Credibility with a banking audience depends on sourcing:

- Every factual claim must have a source: [Source: Company 10-K 2024], [Source: PitchBook, accessed March 2026], [Source: State licensing database]
- When estimating financials, ALWAYS show your math: "At [X] facilities × $[Y]M revenue per facility (based on [comparable company] benchmarks) × [Z]% EBITDA margin (sector median per [source]), implied EBITDA = $[A-B]M"
- When citing precedent transactions, include deal metrics: "[Buyer] acquired [Target] in [date] for $[X]M ([Y]x EV/EBITDA) [Source: press release / PitchBook / SEC filing]"
- If a claim is based on inference, flag it: "[Estimated based on...]" or "[Inferred from...]"
- Use superscript notation (^1, ^2) for inline citations with a source list at the end of each major section. Keep citations compact — this is a professional document, not an academic paper.

---

## FORMATTING REQUIREMENTS

- The document should be clean, professional markdown suitable for conversion to a branded PDF
- Use `---` horizontal rules between major sections
- Tables should be properly formatted markdown tables
- Bold sparingly — for emphasis on key numbers or conclusions, not for decoration
- No bullet-point lists in Sections I, II, or III — these are prose sections. Tables and structured formats are appropriate in Section IV only.
- Do NOT use emoji, colored text, or any informal formatting
- Target total length: 2,500-3,500 words (excluding cover page and citations). This is a 3-5 page document when rendered. Shorter is better if the quality is maintained.

---

## QUALITY CHECKLIST (apply before finalizing):

- [ ] The Opportunity section contains a specific value tension with at least two numbers
- [ ] The Opportunity section would make an MD pause and keep reading — it is NOT a company summary
- [ ] The Company Situation reads as opinionated analysis, not a Wikipedia overview
- [ ] The Company Situation identifies at least one narrative-vs-reality gap
- [ ] All 3 Key Findings would genuinely surprise a sector banker — none are "obvious"
- [ ] All 3 Key Findings connect to a specific deal outcome (valuation, timing, buyer interest, structure)
- [ ] All 3 Key Findings have specific numbers with sources — no unsupported claims
- [ ] The Deal Context section shows quantitative work with transparent methodology
- [ ] The buyer universe entries have specific strategic rationale, not generic descriptions
- [ ] Held-back content is referenced to create curiosity without being salesy
- [ ] The About section is under 200 words — clean, confident, not pushy
- [ ] Total document is under 3,500 words — tight, no filler
- [ ] Tone throughout is authoritative and corporate — not breathless, not academic, not promotional
- [ ] An MD who reads this would learn something they didn't know and want to have a conversation
- [ ] A VP who reads this would be impressed by the analytical depth and want to show their MD

---

=== ALL RESEARCH OUTPUTS ===

{ALL_OUTPUTS}
