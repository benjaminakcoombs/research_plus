# DELIVERABLE 2: FULL RESEARCH COMPENDIUM

## 1. COMPANY PROFILE SUMMARY

**Lunar Energy Inc.** — Incorporated in Delaware, August 2020. HQ: Mountain View, CA (35,000 sq ft). ~226 employees.

**Product:** Integrated home energy system comprising modular LFP battery (10–30 kWh, 5 kWh blocks), 9.6 kW hybrid DC-coupled inverter, "Bridge" smart electrical panel, and "Maximizer" panel-level solar optimizers. Claimed 3-hour installation time. $12,000–$16,000 estimated wholesale ASP, ~10% premium to Tesla Powerwall 3.

**Manufacturing:** Three assembly sites: Suwanee, GA (inverter, Bridge, Maximizers); Mexico (battery module assembly); Washington State (role undisclosed). Mountain View (engineering/pilot line, ~20% utilization). Claimed 10,000 units/year capacity; ~2,000 cumulative deployed.

**Software:** Gridshare — cloud-based VPP/DERMS platform acquired via 2022 Moixa purchase. Manages ~650 MW / 150,000 devices across US, Japan, UK, Europe. Processes 40B data points/month. Key customers: Sunrun (130,000 batteries), ITOCHU/GSJ (35,000+ Japan), Peninsula Clean Energy, Ava Community Energy, Honda UK.

**Funding:** $532M total raised. Series A/B: $300M from Sunrun/SK Group (2020–2022). Series C: $130M led by Activate Capital (late 2023, unannounced until Feb 2026). Series D: $102M led by B Capital/Prelude Ventures (Feb 2026). Estimated post-money: ~$900M–$1B.

**IP:** 58 patents including Moixa's 2008-vintage smart home patents cited by ~200 companies.

**Distribution:** ~40 certified installer partners, primarily in California. Greentech Renewables (100+ locations) as wholesale distributor. Sunrun as primary TPO/lease channel.

---

## 2. RESEARCH WORKSTREAM SUMMARIES

### L1 Workstream 1: Competitive Landscape
Tesla Powerwall 3 holds ~47–59% market share. FranklinWH grew from zero to third nationally in ~3 years with 3,000+ installers. Base Power raised $1.3B for a battery-as-a-service model in Texas. Enphase struggling but maintains ~25% share. Sonnen expanding through Rocky Mountain Power Wattsmart (4,000+ units). Key finding: Lunar does not appear on major installer surveys as a Powerwall alternative, despite the Tesla backlash creating unprecedented switching activity.

### L1 Workstream 2: Regulatory/Tax Credit Analysis
Section 25D homeowner credit eliminated Jan 1, 2026. Section 48E for solar expires end-2027; for battery storage extends through 2033. Section 45X provides $0.065/watt for residential inverters, $10/kWh for battery modules (US production only). Domestic content threshold rising from 40% to 55% post-2026. FEOC/PFE rules tightening annually. Key finding: Lunar's Mexico module assembly forfeits both 45X credits and domestic content qualification — a combined loss of $3,324/unit at scale.

### L1 Workstream 3: Financial/Capital Structure Analysis
$532M raised, estimated $85–115M cash mid-2026. Burn $8–12M/month. Runway ~11 months post-Series D close. Hardware gross margins estimated 15–22% at current volumes. Manufacturing cost per unit (~$12,100 at 2,000 units) likely equals or exceeds wholesale ASP. Series C was a down round (Sunrun $58.7M impairment in Q4 2023). "Never raise again" claim not supported by runway math.

### L1 Workstream 4: VPP Market Analysis
37.5 GW of flexible capacity in North America. DOE targeting 80–160 GW by 2030. DSGS (California's largest VPP program) defunded by Newsom. Replacement programs pay materially less ($100–250 vs. marketed $464). ERCOT RTC+B went live December 2025. Japan's residential DERs eligible for capacity/balancing markets starting April 2026. Key finding: post-DSGS VPP earnings are 25–68% below Lunar's marketed figure.

### L1 Workstream 5: Manufacturing/Supply Chain Analysis
SK On Georgia produces NMC pouch cells for EVs, not LFP prismatic cells. LFP production begins H2 2026, committed primarily to Flatiron (7.2 GWh). No formal Lunar-SK On cell supply agreement publicly disclosed. Lunar's "Europe" cell sourcing reference is inconsistent with CEO's "only U.S. manufacturers" claim. Key finding: current cell source is genuinely unknown and creates FEOC compliance risk.

### L1 Workstream 6: Distribution/Channel Analysis
40 certified partners cannot deliver 20,000 units. FranklinWH scaled to 3,000+ via online certification, fast commissioning, volume pricing, multi-distributor presence, and financing AVL listings. Greentech Renewables already carries Lunar nationally (100+ locations) but no activation infrastructure deployed. Sunrun's affiliate installer channel being reduced 40% in 2026. Key finding: the installer channel — not manufacturing — is the binding constraint.

### L1 Workstream 7: Governance/Investor Relations
Lynn Jurich chairs Lunar board while serving as Sunrun Co-Executive Chair. No recusal protocol publicly disclosed. Hidden Series C ($130M, 2+ years unannounced) signals unfavorable terms. Sunrun's $58.7M Q4 2023 impairment confirms down round. Activate Capital's $130M commitment is 4–13x their typical check size, suggesting protective terms. Wilson Sonsini advised on financing.

### L1 Workstream 8: Technology/IP Analysis
Moixa's 2008 patents predate most VPP/DERMS platforms. 58 total patents with multi-jurisdictional coverage. Bridge smart panel occupies the physical "commanding position" between utility meter and home circuits. Eaton AbleEdge partnership provides open-API smart breaker integration. Matter 1.4 energy management standard could enable Bridge as a controller. Key finding: Bridge + Gridshare combination has platform potential exceeding any competitor in VPP co-optimization, but hardware capabilities for multi-circuit sensing are unconfirmed.

### L1 Workstream 9: Market Expansion/Geography Analysis
Texas announced as primary expansion market but zero disclosed installer partnerships, ADER registrations, or REP relationships. ERCOT ADER pilot expanded to 200 MW. NRG/Reliant building 1 GW VPP. Base Power scaling fast (40 MWh/month). Illinois CRGA mandates VPP tariffs by June 2026. Virginia Community Energy Act requires 450 MW VPP pilot. Dominion, ComEd, Entergy New Orleans all have near-term battery procurement activity. Key finding: the utility white-label opportunity is real but smaller near-term than hypothesized (5,000–12,000 units over 3 years, not 10,000–30,000/year).

---

## 3. TENSION POINT TRACKER

| # | Tension Point | L2 Status | Confidence | Disposition |
|---|---|---|---|---|
| 1 | Gridshare manages 16x more capacity than Lunar hardware — mispriced as hardware co. | ✅ Investigated | Medium | **Included** (Idea 6) — ARR range $3.1–17.7M; mid-case supports $75–94M standalone value |
| 2 | Section 45X credits worth $20M+/year unmonetized | ✅ Investigated | High | **Included** (Idea 1) — Confirmed: inverter credit $624/unit (not $1,056); module credit requires Georgia relocation |
| 3 | Mexico assembly contradicts domestic content marketing | ✅ Investigated | High | **Included** (Ideas 1, 12) — Confirmed: Mexico = non-domestic, no USMCA exception; 55% threshold likely fails |
| 4 | 40 installer partners cannot deliver 20,000 units | ✅ Investigated | High | **Included** (Idea 2) — FranklinWH playbook documented; $10–15M investment for 150–250 new partners |
| 5 | DOE LPO financing unpursued | ✅ Investigated | High | **Invalidated** — ATVM repealed; Title XVII gutted; probability ≤10% |
| 6 | DSGS defunding invalidates $464 VPP earnings claim | ✅ Investigated | Very High | **Included** (Idea 4) — Gap confirmed at 25–68%; FTC/CLRA exposure real |
| 7 | SK On doesn't commercially produce LFP in Georgia | ✅ Investigated | Very High | **Included** (Idea 12) — SK On LFP = H2 2026; Flatiron is "first" LFP ESS customer |
| 8 | Sunrun promotes Tesla while chairing Lunar board | ✅ Investigated | High | **Included** (Idea 7) — CalReady = 75,000 Tesla units; Gridshare addressable market shrinking |
| 9 | Mountain View facility at ~20% utilization | Not investigated at L2 | Medium | **Deferred** — Lower priority; $1–3M/year opportunity |
| 10 | 1M+ solar orphan customers unaddressed | Partially investigated | Medium-High | **Included** (Idea 8) — Retrofit opportunity confirmed; technical integration needs validation |
| 11 | 3-hour installation time buried in spec sheets | Partially investigated | High | **Included** (within Idea 2) — Integrated into installer recruitment strategy |
| 12 | Japan 2026 VPP market opening | ✅ Investigated | Medium | **Included** (Idea 11) — $1–5M/year near-term licensing; $5–15M by FY2028–2030 |
| 13 | Eaton partnership underleveraged | Partially investigated | Medium | **Included** (Idea 10) — 50,000+ contractor relationships untapped |
| 14 | Battery storage ITC extends through 2033 | ✅ Investigated | Very High | **Included** (Idea 3) — Confirmed by statute; standalone battery qualifies for 48E via TPO |
| 15 | Sunrun financial distress (Z-Score -0.47) | ✅ Investigated | High (risk); Medium (probability) | **Included** (Idea 7) — Bankruptcy unlikely before 2028; slow-bleed Tesla displacement is greater risk |
| 16 | SGIP low-income ($1,000/kWh rebate) | Not investigated at L2 | Medium | **Deferred** — Requires further investigation of RSSE budget availability |
| 17 | Texas ERCOT absence | ✅ Investigated | High | **Included** (Idea 5) — Detailed 6-month roadmap developed |
| 18 | Moixa patent portfolio licensing value | Not investigated at L2 | Medium | **Deferred** — Requires professional IP claim analysis |
| 19 | Hidden Series C valuation | ✅ Investigated | High | **Included** (Idea 12 context) — Sunrun $58.7M impairment confirms down round; ~$550–700M post-money |
| 20 | White-label utility battery program | ✅ Investigated | Medium | **Included** (within Ideas 5, 10) — 5,000–12,000 units over 3 years realistic; Entergy NOLA and Dominion VA near-term |
| — | Insurance premium play (Gridshare × insurers) | ✅ Investigated | Medium | **Included** (Idea 9) — Novel; Whisker Labs validates model; $7.5–60M/year |
| — | Bridge as home electrification OS (Alarm.com trajectory) | ✅ Investigated | Medium | **Referenced** in Idea 10 — Requires hardware validation; 36–48 month execution window |
| — | Gridshare as distributed grid sensor network | ✅ Investigated | Medium-Low | **Deferred** — Technically real but commercial pathway unclear; insurance route easier than utility data sales |

---

## 4. SOURCE BIBLIOGRAPHY

### Legislative/Regulatory Sources
- Public Law 119-21 (One Big Beautiful Bill Act), July 4, 2025
- IRC §45X(b)(2)(B), §45X(d)(2) — Advanced Manufacturing Production Credits
- Treasury Notice 2025-08 — BESS Domestic Content Safe Harbor Tables
- Treasury Notice 2026-15 — FEOC Material Assistance Rules (February 2026)
- Federal Register, Final 45X Regulations (October 2024)
- IRS Newsroom FAQ on Clean Energy Credits (2025)
- CPUC Decision D.16-01-044 (NEM 2.0 Grandfathering)
- CPUC DSGS Program FAQ (October 2025)
- ERCOT ADER Pilot Phase 3 Governing Document (June 2025)
- ERCOT RTC+B Go-Live Announcement (December 5, 2025)
- Virginia Community Energy Act (HB 2346/SB 1100)
- Illinois Clean and Reliable Grid Affordability Act (CRGA, January 2026)
- FERC Order No. 2222

### Company Filings and Press Releases
- Lunar Energy Series D Press Release (GlobeNewswire, February 4, 2026)
- Sunrun 2023 10-K ($58.7M Lunar impairment disclosure)
- Sunrun Q4/FY2025 Earnings Release
- Sunrun DEF 14A (2024 Proxy)
- SK On Newsroom (Flatiron LFP deal; Georgia LFP production timeline)
- ITOCHU Press Release (GSJ restructuring, December 2025)
- Enphase Q4 2024 Earnings Release
- FranklinWH Milestone Press Releases (May 2022, 2023, 2024, 2025)
- Eaton/Lunar Partnership Announcement (October 2024)

### Trade and Industry Media
- Heatmap News (Lunar Series D coverage, February 2026)
- Canary Media (Lunar $232M, February 2026; DSGS defunding, September 2025; Newsom VPP vetoes, October 2025)
- PV Magazine USA (Lunar raises $232M, February 2026; California VPP funding cuts, September 2025)
- Latitude Media (Lunar manufacturing, February 2026; "Unpacking the Software Layer" — Gridshare as VPP SaaS)
- Energy Storage News (Lunar Year in Review, January 2026; CalReady Tesla data)
- Corporate Knights (Base Power $1B, October 2025)
- Utility Dive (Clean energy project cancellations Q1 2025; Sunrun VPP growth)
- Electrek (Tesla brand deterioration; Sunrun/NRG Texas VPP)

### Market Research and Analysis
- EnergySage 18th Annual Report (Tesla alternative demand data)
- Roth Capital Partners Installer Survey (Q1 2025)
- Congressional Research Service (45X credit transfer pricing; 25D repeal)
- Consumer Federation of America (Homeowner insurance premiums, April 2025)
- Insurance Information Institute (Claims data, underwriting ratios)
- Argus Media (Japan capacity market clearing prices)
- Greenberg Traurig LLP (Japan balancing market price cap analysis, January 2026)
- Volue (Japan balancing market reform analysis, December 2025)

### Legal and Tax Analyses
- McGuireWoods (45X US production requirement)
- Paul Hastings (Final 45X Regulations analysis)
- Hogan Lovells (45X substantial transformation)
- RSM (Notice 2025-08 domestic content thresholds)
- Baker Botts (Notice 2026-15 FEOC material assistance)
- Sidley Austin (48E/45Y wind and solar termination; storage carve-out)
- Kirkland & Ellis (48E ITC phasedown for storage 2034–2036)
- Holland & Knight (OBBBA impact on DOE LPO)
- ML Strategies/Mondaq (ATVM repeal)

### Technology and Product Documentation
- Lunar Energy product specifications (lunarenergy.com)
- Gridshare case studies (Sunrun, ITOCHU, PCE/SVCE)
- Eaton AbleEdge specification sheet (TD003020en)
- SPAN Panel product documentation (span.io)
- Whisker Labs/Ting program documentation
- AWS/Lunar Energy case study (Gridshare architecture)

### Comparable Company Data
- Voltus SPAC Investor Materials (2021)
- Virtual Peaker revenue (Latka Data, 2024)
- Alarm.com 10-K and earnings (2024–2025)
- EnergyHub/Alarm.com subsidiary metrics
- Utilidata funding and deployment data
- Bidgely utility customer data
- GMP/Tesla Powerwall program documentation

---

## 5. DATA GAPS & CAVEATS

### Critical Unknowns (High-Impact, Unresolved)

1. **Lunar's actual battery cell chemistry, manufacturer, and country of origin.** This is the single most important undisclosed fact. UL 9540 certification filings, US Customs import records (ImportGenius/Panjiva), and California building department permits could resolve this. [L2 Deep Dive: Cell Supply Chain]

2. **Gridshare ARR by customer segment.** No public disclosure exists. The Ava Community Energy contract (a public agency subject to California Public Records Act) is the most accessible data point. Sunrun's 10-K does not visibly disclose Gridshare fees. [L2 Deep Dive: Gridshare Valuation]

3. **Series C valuation and term sheet.** Delaware Certificate of Incorporation (orderable from Division of Corporations), SEC EDGAR Form D filing date, and Sunrun 10-K footnotes on Lunar equity accounting treatment would narrow the range. [L2 Deep Dive: Series C Forensics]

4. **GSJ licensing terms (Lunar UK → GridShare Japan).** Moixa Energy Holdings FY2024 accounts (UK Companies House, company 04941671) should contain related-party transaction disclosures. Not retrieved during research. [L2 Deep Dive: Japan VPP]

5. **Sunrun-Lunar payment terms and revenue concentration.** Neither company discloses the commercial terms. Sunrun's 10-K related-party note should address this under ASC 850, but the relevant sections were not fully accessible. [L2 Deep Dive: Sunrun Dependency]

6. **Bridge hardware architecture.** Whether Bridge has per-circuit current sensing, individual circuit relay control, or multi-protocol communication interfaces (Modbus, OpenADR, IEEE 2030.5) is not confirmed in public documentation. This determines feasibility of the platform strategy. [L2 Deep Dive: Bridge Platform]

### What We're Least Confident About

- **Gridshare standalone valuation range:** The ARR estimate spans $3.1M–$17.7M, creating a valuation range of $15M–$177M. Without contract data, the midpoint is an educated guess. (Confidence: Low-Medium)
- **Texas market share by 2028:** Depends on simultaneous execution across installer recruitment, QSE partnership, REP alignment, and ADER registration — any one of which could delay the timeline by 12+ months. (Confidence: Low-Medium)
- **Insurance premium play feasibility:** No battery company has executed this model. The Whisker Labs analogy is strong but not identical. (Confidence: Medium)
- **Japan licensing revenue uplift:** Without knowing whether the GSJ fee is fixed or variable, the revenue model is speculative. (Confidence: Low-Medium)

### What Additional Research Would Most Improve the Analysis

1. **Order Lunar Energy's Delaware Certificate of Incorporation** — resolves Series C valuation, anti-dilution terms, option pool size. Cost: ~$50. Timeline: 5–10 business days.
2. **File CPRA request to Ava Community Energy for Gridshare contract** — first public data point on Gridshare per-device or per-program pricing. Cost: free. Timeline: 10 business days.
3. **Query UL Product iQ (FTBW category) for Lunar Energy** — resolves cell chemistry and manufacturer. Cost: subscription access. Timeline: same day.
4. **Search ImportGenius/Panjiva for Lunar Energy import records** — identifies cell origin country and HS code. Cost: subscription. Timeline: same day.
5. **Download Moixa Energy Holdings FY2024 accounts from UK Companies House** — reveals GSJ licensing terms and Lunar UK revenue. Cost: free. Timeline: immediate.
6. **Review Sunrun 10-K footnotes on equity method investments** — details on Lunar carrying value, impairment trigger, and accounting treatment. Cost: free (EDGAR). Timeline: 1 day.

### Honest Disclosure of Analytical Limitations

This research was conducted entirely from publicly available sources. Lunar Energy is a private company with no SEC disclosure obligations. All revenue, margin, and valuation estimates are analytical constructions based on triangulation from public evidence — not confirmed financial data. The analysis may contain errors arising from source inaccuracies, incomplete web access, or incorrect inferences from circumstantial evidence. Any decision based on these findings should be validated through direct engagement with the company and its advisors.

---

*End of Research Compendium*