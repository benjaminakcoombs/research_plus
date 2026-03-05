You are a grid modernization engineer and utility data analytics expert investigating whether Lunar Energy's Gridshare-managed fleet of 150,000 residential battery systems constitutes an unrecognized distributed sensing network whose observability data is worth more to utilities than the dispatchable capacity it provides through VPP programs.

CONTEXT:
Gridshare manages approximately 150,000 devices across three continents (35,000+ in Japan via ITOCHU, tens of thousands in the UK, and a growing US fleet). Each connected battery system continuously measures and reports: grid voltage and frequency at the point of interconnection, real-time power consumption of the home, solar generation, battery state of charge, power quality metrics (harmonics, voltage sag/swell, frequency deviation), and outage detection with sub-second timestamps. This data flows to Gridshare's cloud at high frequency—40 billion data points per month. Currently, this data is used exclusively for battery optimization and VPP dispatch. However, utilities globally spend $10–15 billion annually on grid modernization and "distribution system visibility"—deploying smart meters (AMI), line sensors, phasor measurement units, and SCADA upgrades to understand what is happening at the grid edge. Despite these investments, most utilities have poor visibility into low-voltage distribution networks (the "last mile" to homes). Gridshare's devices sit precisely at this blind spot: the point of delivery to the residential customer. Each device is effectively a high-fidelity grid sensor that the utility did not pay to install.

HYPOTHESIS TO INVESTIGATE:
Waze transformed traffic management by crowdsourcing real-time location data from millions of phones—data that municipal transportation departments had spent billions trying to collect through fixed sensors. Waze then sold this data back to cities as "Waze for Cities" (now Google for Cities). Similarly, Utilidata has raised $100M+ to embed AI chips in smart meters to provide utilities with real-time grid-edge intelligence. Whisker Labs deploys dedicated electrical sensors in homes to detect hazards and sells the aggregated data to utilities as "grid analytics." Lunar's Gridshare already has the sensors deployed—150,000 of them—generating richer data than smart meters (which typically report in 15-minute intervals, vs. Gridshare's near-real-time). A "Gridshare for Utilities" product could sell anonymized, aggregated grid observability data to distribution utilities and ISO/RTOs as a subscription service: hosting capacity analysis, voltage violation detection, transformer loading estimation, outage mapping, DER impact assessment, and load forecasting at the feeder level. This is entirely distinct from VPP dispatch revenue—it monetizes the passive data stream rather than the active capacity. At $100–300/sensor/year to utilities (comparable to AMI data analytics subscriptions), 150,000 sensors could generate $15–45M/year. At 500,000 sensors: $50–150M/year. This creates a revenue stream that scales with every device added to the Gridshare fleet—whether or not that device is a Lunar battery.

SPECIFIC RESEARCH QUESTIONS:
1. What specific grid measurements does a Gridshare-connected battery system actually report, and at what temporal resolution? Does the Lunar inverter/Bridge measure voltage, frequency, THD (total harmonic distortion), and power factor at the point of interconnection? How does this compare to AMI (smart meter) data resolution and latency?
2. How did Waze monetize crowdsourced transportation data through its "Waze for Cities" program—what were the unit economics, what did cities actually pay, and how did Waze handle privacy? How has Utilidata structured its utility partnerships—what do utilities pay per endpoint for grid-edge intelligence? What does Whisker Labs charge utilities for aggregated grid analytics from its sensor fleet?
3. How large is the utility market for distribution grid visibility? What do utilities currently spend per customer on AMI infrastructure and associated data analytics platforms (Itron, Landis+Gyr, Bidgely, Oracle Utilities)? What specific grid planning problems (hosting capacity, voltage regulation, transformer overloading) would Gridshare data solve?
4. Can Gridshare's existing cloud architecture support a utility-facing analytics product without major re-architecture? Does Lunar have the data science talent to build grid analytics models, or would this require an acquisition or partnership (e.g., with Utilidata, Bidgely, or Camus Energy)?
5. What would prevent this from working? Would utilities trust data from a third-party battery fleet for grid planning decisions? Are there regulatory barriers (utility data sharing agreements, NERC CIP standards for grid data)? Would device owners consent to sharing their data with utilities? Could smart meter vendors (Itron, Landis+Gyr) offer comparable data from their existing installed base, making Gridshare data redundant?

RESEARCH GUIDANCE:
- Investigate Utilidata: their $100M+ raise, partnership with GE/Haier for smart meter chips, utility contracts, per-endpoint pricing
- Research Whisker Labs/Ting: their utility analytics product (distinct from their consumer fire safety product), partnerships with utilities for grid data
- Deep-dive "Waze for Cities" / Google Environmental Insights Explorer: how crowdsourced mobility data was packaged for municipal customers
- Examine Bidgely (utility analytics from AMI data): pricing model, utility customer base, what insights they provide per home
- Look at Camus Energy (grid orchestration platform): how they price distribution grid visibility
- Search EPRI publications on "distribution system state estimation" and the value of high-resolution grid-edge measurements
- Check IEEE papers on using inverter-based resources as grid sensors ("grid-forming inverter" measurement capabilities)
- Research PG&E, SCE, SDG&E Grid Modernization Plans (GRC filings) for budgeted spending on distribution visibility
- Investigate Japan's OCCTO and METI grid data requirements: does the Japan fleet's data have separate monetization potential with Japanese utilities?
- Look at Tesla's "Tesla Electric" virtual utility in Texas: are they monetizing Powerwall fleet data for grid analytics, or only for energy arbitrage?

OUTPUT FORMAT:
1. EVIDENCE FOR THE HYPOTHESIS
2. EVIDENCE AGAINST THE HYPOTHESIS
3. COMPARABLE EXAMPLES (prioritize Waze for Cities, Utilidata, Whisker Labs utility analytics, Bidgely)
4. FEASIBILITY ASSESSMENT
5. MAGNITUDE ESTIMATE
6. CONFIDENCE ASSESSMENT
7. CITATIONS