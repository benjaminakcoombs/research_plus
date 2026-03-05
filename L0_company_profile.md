# L0: Company Profiling Prompt

## Purpose
This prompt is run as a single deep research task. It takes a company name (and optional user-provided context) and produces a structured profile that L0.5 uses to generate customized L1 research prompts.

## Why L0 Matters
The quality of the entire system depends on L0 producing a rich enough profile that L0.5 can generate operationally specific prompts — prompts that ask about specific facilities, specific waste streams, specific data assets, specific customer behaviors. A shallow L0 produces generic L1 prompts which produce generic ideas. L0 must go deep on OPERATIONAL SPECIFICS — and adapt its depth to where the value actually lives for each company type.

---

## PROMPT

```
You are a senior research analyst conducting a rapid but comprehensive profiling of {COMPANY_NAME} to support a multi-layered strategic research project. Your output will be used by another AI system to design targeted, operationally specific research workstreams.

{OPTIONAL_USER_CONTEXT}

Your job is NOT to analyze the company strategically — that comes later. Your job is to BUILD THE MAP. You need to understand what this company is, what it does, how it makes money, what it owns (tangible and intangible), who runs it, and what its environment looks like. Be exhaustive on facts. Be specific on operations.

RESEARCH THE FOLLOWING:

## 1. IDENTITY, SCALE & OWNERSHIP

- Full legal name, ticker, listing exchange, market cap, enterprise value
- Industry classification (GICS, SIC, or equivalent)
- One-paragraph plain-language description of what the company actually does
- Company archetype — classify as ONE of: [13 archetypes]
- Scale indicators: Revenue, employees, facilities/locations, geographic footprint
- Key financial metrics: Revenue by segment (last 3 years), margins, balance sheet, FCF, capex, dividends
- Ownership: public/private, shareholders, governance, board composition

## 2. WHAT THE COMPANY ACTUALLY DOES

Maps ALL forms of value — physical assets, IP, data, brand equity, customer relationships,
workforce expertise, regulatory positions, digital infrastructure. Adapts depth to company type.

For each segment: operations, revenue model, inputs/procurement, physical assets,
waste streams, capacity/utilization, workforce.

## 3. CONTEXT & ENVIRONMENT

5-10 most important facts: competitors, regulations, geographies, recent events, macro trends.
Focused on what would change how a strategic advisor thinks about the company.

## 4. STRATEGY, NARRATIVE & SELF-IMAGE

Management's stated direction, how company describes itself to different audiences,
tensions between narrative and operational reality, market perception accuracy.

## 5. WHAT MAKES THIS COMPANY INTERESTING

5-10 most interesting/unusual/strategically significant observations.
What's hiding in plain sight? What does the company undervalue?
These drive targeted research workstream design.
```

See `/prompts/l0_company_profile.md` for the full prompt template.

---

## VARIABLES

| Variable | Source | Required |
|----------|--------|----------|
| `{COMPANY_NAME}` | User input | Yes |
| `{OPTIONAL_USER_CONTEXT}` | User input | No — if provided, insert as: "Additional context from the requester: {context}" |

## EXPECTED OUTPUT SIZE
3,000-8,000 words depending on company complexity.

## KEY CHANGES FROM PREVIOUS VERSION
- Consolidated 10 sections → 5 sections (~90 lines vs ~145)
- Added "all forms of value" framing — maps intangible assets (data, brand, community) not just physical
- Section 3 merges geographic/competitive/regulatory/recent events into focused context
- Section 4 adds narrative awareness (how company describes itself, perception gaps)
- Section 5 replaces fixed lens recommendations with open-ended "what's interesting" observations
- Adaptive: produces facility-level detail for manufacturers, data/brand detail for software/luxury

## SUCCESS CRITERIA
The L0 output is good enough if L0.5 can generate prompts that ask about SPECIFIC:
- Facilities by name and location
- Input costs and procurement categories
- Waste streams and byproducts
- Data assets, brand equity, or community value (where relevant)
- Local ecosystem features (nearby towns, companies, infrastructure)
- Regulatory specifics for each operating jurisdiction
- Named competitors per segment
- Narrative/perception gaps worth investigating
