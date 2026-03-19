# Situation Assessment Pipeline

## The business context

We sell an AI workspace platform (Pokee AI) to enterprise knowledge workers. Our #1 target segment is boutique investment banks — firms like Perella Weinberg Partners, Moelis, PJT Partners, Centerview, and Guggenheim.

Our cold outreach strategy is **"show, don't tell."** Instead of sending a pitch email explaining what our product does, we send a deliverable that demonstrates it. The deliverable itself is the pitch.

## What the deliverable is

A **Strategic Situation Assessment** of a mid-market company in a sector the target bank covers. It's written as if an analyst at the bank produced it — the kind of strategic intelligence that would make a managing director smarter before a client call.

The goal is for the MD to read it and think: "Whoever produced this understands our business, sees things we don't, and I want to talk to them."

## What makes it valuable

The Situation Assessment surfaces things a banker would actually use:

**Tension points** — the "how did they know that?" moments. Not generic observations ("the healthcare sector is consolidating") but specific, cited, interlocking insights with deal implications. Examples:

- "Same-store revenue growth of 12% masks a geographic divergence: the 8 clinics acquired in 2023 are growing at 22% while the legacy 15 are flat. This means the growth story is entirely M&A-driven, which changes the multiple a buyer should pay."

- "The CEO was replaced 6 months ago by a former PE operating partner. Within 60 days, the new CEO hired Deloitte for a 'financial process improvement project.' Combined with the sponsor's fund being in year 7, this is textbook pre-sale preparation."

- "The company's payer mix is 68% Medicaid in a state where the governor just proposed a 4.2% rate increase effective July 2026. At their margin structure, this alone adds $8M to EBITDA — but no sell-side analyst has modeled it because the rate change hasn't been finalized."

**Valuation context** — a precedent transaction table with 8-12 comparable deals (buyer, target, date, EV, multiples), an implied valuation range for the target company with transparent methodology ("we estimate EBITDA of $X based on Y facilities × $Z per facility"), and key drivers that push to the high or low end.

**Buyer universe** — 12-18 potential acquirers mapped by type (strategic buyers, PE sponsors with existing platforms, PE sponsors looking for new platforms), each with specific strategic rationale, estimated financial capacity, and recent sector activity. Not a list of names — a demonstration that the system can synthesize across company profiles, deal histories, and fund data.

**Deal catalyst analysis** — what would trigger a transaction in the next 12-18 months, with specific dates and probability-weighted scenarios. Fund hold period math, management change timelines, regulatory deadlines, refinancing windows.

## What it demonstrates to the bank

The Situation Assessment proves several things simultaneously:

1. **The AI can do real research.** Not summaries of Wikipedia — deep, multi-source investigation that triangulates across SEC filings, state regulatory databases, job postings, court records, press releases, and industry publications.

2. **It understands the IB context.** Every insight connects to a deal outcome: valuation, timing, buyer interest, or diligence risk. It's not a strategy deck — it's deal intelligence.

3. **It works on low-information targets.** Most interesting M&A targets are private companies with limited public data. The system triangulates aggressively ("estimated revenue of $200-250M based on 45 facilities × $4.5-5.5M per facility, consistent with industry benchmarks").

4. **It's specific, not generic.** The quality bar is: would an MD who covers this sector say "I hadn't thought of that" rather than "obviously"?

5. **Imagine what it could do with your data.** The final page makes the product pitch: "This was produced using only public data. Deployed inside your infrastructure, the same system could ingest your data rooms, internal models, and client financials."

## How it's produced

The system runs a multi-layered AI research pipeline. It starts with a company name, sector, and target bank. Over ~2 hours, it deploys 15-20 research agents that conduct iterative web research, then synthesizes everything into the final document. Total cost is ~$40-70 per run.

The pipeline has 6 layers: initial company profiling → dynamic research agent design → parallel deep research → consolidation into tension points → targeted deep dives to validate hypotheses → final synthesis into the Situation Assessment format.

The intellectual property is in the prompts at each layer — they encode what "good" looks like for an IB audience, how to find non-obvious insights, and how to connect observations to deal outcomes. The code is straightforward orchestration.

## Current status

We have a working pipeline (`--mode situation_assessment`) and are running our first test case: **Acadia Healthcare** (NASDAQ: ACHC), a $3.3B behavioral health company with active activist campaigns, a CEO departure, ongoing DOJ investigation, and a board explicitly "evaluating all paths to enhance shareholder value." The target bank is **Perella Weinberg Partners**, which just hired a partner (Ben Port) specifically covering behavioral health.

The existing pipeline also has a `strategic_briefing` mode that produces strategic advice FOR a company's management team (the original use case). Same architecture, different prompts and output format.

## The quality bar

The benchmark is the Lunar Energy report in `outputs/run_7070d661/l3_executive_briefing.md`. That report produced 12 deeply specific strategic ideas — including a $332M/year tax credit opportunity the company was missing, an FTC violation hiding in their marketing claims, and a detailed analysis of why their "proudly domestic" manufacturing claim was actually a regulatory liability. All from public data about a private company most people have never heard of.

The Situation Assessment should match that density but oriented for bankers: every observation connects to a deal outcome, every number has a source, and the document reads like it was written by someone who understands M&A mechanics, not someone who Googled the company.
