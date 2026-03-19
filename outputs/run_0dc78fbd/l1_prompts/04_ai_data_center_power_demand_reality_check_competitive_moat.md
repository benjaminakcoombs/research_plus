ROLE: You are a data center infrastructure analyst and energy markets specialist who advises both hyperscale operators and power generation companies. You are conducting an independent assessment of the AI data center power demand thesis as it relates to Bloom Energy's value proposition. Your job is to be rigorous, skeptical, and evidence-based — neither bullish nor bearish, but analytical.

CONTEXT: Bloom Energy claims it can deploy 100 MW of on-site power in 90 days, compared to 2-5 year grid interconnection queues. This speed-to-power argument is the core of Bloom's data center value proposition and has driven its stock from ~$10 to ~$170 in 18 months. Key relationships: Brookfield ($5B AI factory partnership), AEP (1 GW supply agreement), Equinix (19 data centers across 6 states), Oracle, CoreWeave, and Quanta as emerging customers.

RESEARCH TASKS:

**A. AI DATA CENTER POWER DEMAND — QUANTIFICATION & REALITY CHECK**

1. Research and compile the most credible estimates of US data center power demand growth:
   - Current total US data center power consumption (2025 actual, in GW)
   - Projected growth: 2026, 2027, 2028, 2030, 2035 (from McKinsey, Goldman Sachs, IEA, EPRI, EIA)
   - How much of this is AI-specific vs. traditional cloud/enterprise?
   - What is the implied annual incremental power capacity needed (in GW/year)?

2. Critically assess these projections:
   - What assumptions about AI training vs. inference power consumption underpin each estimate?
   - How do efficiency improvements in chips (e.g., Nvidia's power efficiency gains generation-over-generation) affect power demand projections?
   - Research any credible bearish cases on data center power demand. Has anyone made a rigorous argument that power demand will be lower than consensus?
   - What happened with previous "exponential demand" forecasts (e.g., 2000s internet buildout, 5G infrastructure)? Were they realized?

3. Geographic analysis: Where is data center construction happening?
   - Top 10 US markets for data center construction (by MW under development)
   - Grid interconnection queue length by market
   - Which markets have the most severe power constraints?
   - Does Bloom's on-site generation solve a real problem, or is it overkill for markets with adequate grid capacity?

**B. BLOOM'S COMPETITIVE POSITION IN DATA CENTER POWER**

1. Validate the "100 MW in 90 days" claim:
   - Has Bloom actually delivered 100 MW to a single site in 90 days? Or is this a theoretical capability?
   - What is the typical site preparation, permitting, and installation timeline for a Bloom deployment?
   - What are the gas infrastructure requirements? Does the customer need a new gas pipeline? If so, what is the timeline for gas interconnection?
   - Research any specific case studies or customer testimonials validating this speed claim

2. Map ALL competitive alternatives for data center power:
   - **Grid interconnection acceleration**: Are utilities offering expedited interconnection for data centers? Research AEP, Dominion, Duke, and other major utility programs
   - **Natural gas turbines / reciprocating engines**: Companies like Generac, Caterpillar, Wartsila, and Enchanted Rock offer gas-fired on-site generation. How do they compare to Bloom on speed, cost per MW, efficiency, and emissions?
   - **Small modular nuclear reactors (SMRs)**: Research NuScale, Oklo, Kairos Power, TerraPower. Timeline to commercial deployment? Cost per MW? Have any hyperscalers committed to SMR power?
   - **Battery + solar/wind**: Research on-site renewable + storage configurations for data centers. Are any hyperscalers pursuing this model? Cost and reliability comparison?
   - **Behind-the-meter natural gas peaker plants**: Simple cycle gas turbines deployed on-site. How do these compare to Bloom's SOFCs?
   - **Diesel/HFO backup generation**: Already standard at every data center. At what point does expanding backup generation become a substitute for Bloom?

3. For each competitive alternative, build a comparison matrix:
   - Cost per MW (capex)
   - Levelized cost of electricity (LCOE)
   - Speed to deploy (months from order to operation)
   - Reliability (% uptime)
   - Emissions profile (lbs CO2/MWh)
   - Space requirement (MW per acre)
   - Fuel supply requirements
   - Permitting complexity

4. Research the specific economics of a Bloom deployment for a data center:
   - What does a 10 MW Bloom installation cost the customer (before ITC)?
   - What does it cost after the 30% ITC?
   - What is the all-in cost of electricity from a Bloom system vs. grid power vs. alternatives? ($/MWh)
   - At what grid electricity price does Bloom become economically advantageous even without the ITC?

**C. CUSTOMER COMMITMENT DEPTH**

1. Research each of Bloom's major data center relationships in detail:
   - **Brookfield**: What specific projects have been announced? How many MW are under construction vs. in planning? What is the deployment timeline?
   - **AEP**: The 1 GW agreement is described as "up to" 1 GW. How firm is this? What are the order milestones? Only 100 MW has been ordered so far — what triggers the next tranches?
   - **Equinix**: 19 data centers across 6 states — what is the total deployed MW? Is Equinix expanding with Bloom or maintaining existing installations?
   - **Oracle**: What is the scope and status of Oracle's relationship with Bloom?
   - **CoreWeave**: Any disclosed MW commitments?

2. Research whether any data center customers have CANCELLED or REDUCED Bloom orders. Any evidence of customer dissatisfaction?

3. Research whether data center customers are diversifying their power sources (i.e., using Bloom AND other solutions simultaneously). This would limit Bloom's total addressable opportunity per customer.

**D. THE NATURAL GAS TENSION**

1. Hyperscaler sustainability commitments:
   - Microsoft: 100% renewable by when?
   - Google: 24/7 carbon-free energy by when?
   - Amazon: Net-zero carbon by when?
   - Meta: Similar commitments?

2. Can hyperscalers reconcile natural gas fuel cell deployments with these commitments?
   - Are hyperscalers using renewable energy credits (RECs) to offset Bloom's gas consumption?
   - Is biogas a realistic fuel alternative at data center scale?
   - How do Bloom's emissions (679-833 lbs CO2/MWh) compare to average grid emissions in data center markets?

3. Research any pushback from sustainability advocates or ESG-focused investors on hyperscaler use of natural gas fuel cells.

**E. MARKET SIZE FOR BLOOM SPECIFICALLY**

1. Of the total projected data center power demand growth, what percentage is realistically addressable by on-site fuel cells (vs. grid, vs. nuclear, vs. renewables)?
2. What is Bloom's realistic market share of the addressable segment?
3. Model Bloom's data center revenue opportunity: 2026, 2027, 2028, 2030 — with bull, base, and bear cases.

OUTPUT FORMAT: Use comparison tables wherever possible. Cite specific sources for all demand projections. The competitive comparison matrix should be comprehensive and visually clear. Flag any claims by Bloom that could not be independently verified.

End your output with "NOTABLE ANOMALIES" — particularly:
- Any evidence that data center power demand projections are being revised downward
- Competitive threats that the market is underestimating
- Customer commitments that are less firm than they appear
- The gas pipeline/interconnection bottleneck that nobody is discussing
- Any technical limitations of solid oxide fuel cells for data center applications (e.g., ramp rate, load following, heat management)
- Evidence that Bloom's speed-to-power advantage is being eroded by utility fast-track programs