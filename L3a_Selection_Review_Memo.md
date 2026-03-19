# L3a Finding-Selection Review Memo

**Subject:** Evaluation of v4 finding selections for Brimstone Energy Deep Analysis
**Date:** March 19, 2026
**Scope:** Read-only review — no file modifications

---

## Part 1: Evaluation of Each Selected Finding

### Finding 1: The Alumina Binary — "$245M in Platform Value Rests on Alumina No Third Party Has Tested"

**Was this the right choice?** Yes, unambiguously. This is the strongest finding in the entire corpus and it holds up across both versions. The selection brief scored it 17/20 (tied for highest) and it earns every point. The compound mechanism — geological characterization of the GMLC as "Fe-rich, Ti-rich" anorthositic gabbro → published ilmenite dissolution rates of 93–97% → no dedicated titanium removal step in the patent → zero published SGA specification data across all 13 parameters — is a genuine chain of inference that no individual tension point conveys. The financial quantification ($49M at Plant 1, $245M at platform scale) gives an MD a concrete number to anchor on.

**Did the brief's reasoning hold up in execution?** Largely yes. The v4 writer delivered a clean evidence chain with sourced footnotes (Sources 16–19, 27–30). The decontamination factor math (738–5,905×) lands effectively. The key uncertainty caveat — "Brimstone may have achieved full SGA specification at pilot scale and is withholding data as trade secret" — is appropriately positioned at the end in italics rather than buried in the middle where it would dilute the finding's force.

One execution concern: the brief flagged writability at 3/5 (the lowest score among its attributes), noting the compound mechanism's complexity. In v4, the writer handled this by splitting observation from deal implication with bold headers ("The Observation" / "The Deal Implication"), which works well structurally. But the finding still runs dense — the crystal-phase risk from TP13 (eta-Al₂O₃ vs. gamma/theta-Al₂O₃) is included as a secondary technical point and may lose a non-technical MD. v1 handled roughly the same material without the crystal-phase detail and was arguably more scannable, though less technically complete.

**Comparison to v1's equivalent slot:** v1's Finding 1 covers nearly identical ground. The selection is the same; the difference is execution. v4 adds the crystal-phase risk (TP13) and states the decontamination factors explicitly (738–5,905×). v1 omits the crystal-phase detail and uses a slightly simpler framing. Both versions land the core insight. v4 is more technically rigorous; v1 is more accessible. For the intended audience (a materials/cement MD who likely has some technical literacy), v4's additional specificity is the better call — it signals depth of research that a simplified version would not.

**Verdict: Correct selection, strong execution.**

---

### Finding 2: Kajima EPC as Financing Key — "The $400M Financing Problem Has a Single Key — and It's Already on the Cap Table"

**Was this the right choice?** This is the most genuinely non-obvious finding in either version. The selection brief's Thread A reasoning is the most sophisticated piece of analytical synthesis in the entire brief — linking the OSC creditworthy-sponsor requirement (TP11) to Kajima's A+ credit rating and CVC-to-EPC corporate pattern (TP8), then using the Dolese elimination (university foundation fiduciary constraints) to narrow the solution space to a single entity. The insight that "the financing complexity everyone is modeling as a multi-party syndication problem actually has a single-key solution" is exactly the kind of finding that makes an MD want to pick up the phone — it suggests the advisor has seen something the market hasn't.

**Did the brief's reasoning hold up in execution?** Yes, and this is where v4 most clearly outperforms v1. The v4 writer maintains the brief's logical chain: OSC requirement → Dolese elimination → Kajima as sole qualifying entity → EPC contract as the instrument that simultaneously satisfies creditworthiness, risk transfer, construction capability, and equity relationship requirements. The deal implication is concrete: "$5–6M in bond premiums" to transfer scale-up risk and compress financing timeline by 18–24 months. The confidence hedge is present ("though no Brimstone-specific EPC disclosure has been made").

The brief rated evidence quality at 3/5 (the key limitation — the EPC mandate is inferred from corporate behavior). The v4 writer handled this correctly by leading with documented facts (OSC terms, Kajima credit rating, Dolese ownership structure) and positioning the inferential leap ("Kajima's documented pattern of linking CVC investments to parent-company EPC mandates is consistent with a linked construction role") as explicitly inferential. This is the right epistemic framing for a 60–70% confidence hypothesis.

**Comparison to v1's equivalent slot:** v1 has no equivalent finding. v1's Finding 2 is the CRH buyer thesis / Sublime legal limbo — a completely different selection. This is the single biggest divergence between the two versions and, in my assessment, the single biggest improvement v4 makes. The Kajima-OSC finding is genuinely novel — it connects dots across financing policy, corporate venture behavior, and process plant construction in a way no public analyst has done. v1's CRH finding, while useful, is more readily derivable: "Sublime is failing, CRH needs a replacement, Brimstone is the only ASTM C150 option" is a chain of observations that an attentive industry participant could construct independently. The Kajima thesis requires cross-referencing DOD financing instruments, Japanese construction conglomerate CVC patterns, and Oklahoma quarry partner ownership structures — which is exactly the kind of "I hadn't thought of that" density this document should deliver.

What v4 lost by cutting the CRH standalone: the CRH buyer thesis is the most intuitive "who buys this" answer for the intended audience. v1's Finding 2 gives an MD a specific buyer name (CRH), a specific constraint (Sublime non-compete), a specific workaround (CRH Ventures preferred equity, $75–125M anchor), and a specific catalyst (Amrize investor day March 25, 2026 — one week from publication). That's a high-density, immediately actionable finding. v4 absorbs the CRH analysis into Finding 3's first window, which preserves the legal-constraint insight but necessarily compresses the CRH-specific deal structuring (the Ventures workaround, the dry powder estimate of $130–170M) into the Deal Context section rather than elevating it as a key finding. This is the right trade-off: the Kajima finding is more differentiated. But it comes at a cost to the document's cold-outreach immediacy for a CRH-focused banker.

**Verdict: Correct selection. The strongest improvement over v1.**

---

### Finding 3: "Three Clocks, One Window: Any Strategic Position Must Be Secured by Q3 2026"

**Was this the right choice?** This is where I have the most reservations. The selection brief scored it 16/20 — one point behind A and B — and the brief's own reasoning acknowledges that the compound insight depends on the interaction between three deadlines, two of which (Sublime collapse and Series B imminence) are surface-level observations that any attentive follower of the space already knows. The third (FEED infrastructure lock-in) is the genuinely non-obvious element, but it carries the weakest evidence: the 6–12 month timeline is "estimated from standard Bechtel FEED duration for industrial projects," not confirmed for the Inola project specifically.

The brief's self-assessment — "the urgency created by their simultaneous convergence is invisible from any single TP" — is correct but incomplete. The convergence is invisible from any single TP, but the individual deadlines are not invisible from the research corpus as a whole. An MD reading the Company Situation section of either v1 or v4 already absorbs the Sublime collapse, the FEED timeline, and the Series B signals. Finding 3 synthesizes these into a "you must act by Q3 2026" conclusion — but the question is whether that synthesis, standing alone, clears the non-obvious threshold.

**Did the brief's reasoning hold up in execution?** Partially. The v4 writer follows the brief's guidance and presents the three windows as independently sourced, then reveals the convergence. The CRH legal constraint (non-compete provisions remaining in force while Sublime exists as a going concern) is the finding's strongest specific insight and is appropriately emphasized with bold text ("most legally constrained"). But the FEED window — which the brief flagged as "the least obvious of the three and should receive the most explanatory emphasis" — receives roughly equal treatment with the other two windows in the final text, rather than being foregrounded. The result reads more as a well-organized catalyst timeline than as a discovery.

Comparison to v1's equivalent slot is where the concern sharpens. v1's Finding 3 — the EGA/Century standalone — has a fundamentally different character. It establishes:

- Hard numbers: $5B smelter, 750K t/yr aluminum, 1.5M t/yr alumina demand
- Geographic specificity: 180 miles from Brimstone's plant by truck
- Infrastructure confirmation: PSO's $3.2B+ in committed utility infrastructure (the "a regulated utility does not make $3B+ in capital commitments for a project that might not be built" observation is one of the most powerful evidentiary anchors in either document)
- Policy incoherence: the federal government simultaneously funds the smelter ($500M Century OCED grant maintained) and cancels the alumina supply ($189M Brimstone OCED grant terminated)
- Cost economics: co-production at $125–225/t vs. imported at $460–500/t, generating $589M NPV at platform scale

v1's Finding 3 is a demand-side thesis with hard infrastructure evidence. v4's Finding 3 is a timing-convergence argument with inferred deadlines. For a cold outreach document, the demand thesis is arguably more powerful because it answers "why does anyone care about the alumina at all" with concrete, independently verifiable numbers. The timing argument assumes the reader already cares and tells them when to act — which is useful but secondary.

**Verdict: Defensible but not optimal. See Part 3 for the full alternative analysis.**

---

## Part 2: Evaluation of the Cuts

### Candidate D — Amazon Dual Consent Event (Score: 15/20)

The brief's cut rationale: "narrower in scope... addresses deal structuring rather than deal thesis or timing... specific dollar figures ($33–48M) depend heavily on assumptions about Amazon's terms that are entirely private."

**Was the cut justified?** Yes. The dual consent event is a clever structural insight, but the brief correctly identifies that it's a deal-structuring mechanism rather than a standalone finding. In v1, this material appears in the Deal Context / Buyer Universe section (under "Infrastructure Funds"), where it generates the $33–48M net positive EV estimate. v4 handles it identically — the infrastructure funds entry in the buyer universe references the dual consent structure. The insight is preserved at the right altitude. Elevating it to a full finding would have required explaining Amazon's four blocking positions, the ACPF consent architecture, the Rivian S-1 template, and the specific buyer-category consent probabilities — all within ~350 words. The evidence chain is too long for the payoff.

**Verdict: Correct cut.**

### Candidate E — EGA/Inola Standalone (Score: 16/20)

The brief's cut rationale: "absorbed its core content into Finding 1 (where EGA demand makes the alumina binary consequential) and Finding 3 (where the FEED infrastructure lock-in is one of the three converging deadlines). As a standalone finding, it would have restated material already covered in Section II."

**Was the cut justified?** This is the most consequential call in the entire selection, and I believe the brief got it wrong.

The brief's "absorption" argument has a structural flaw: by distributing the EGA thesis across two other findings and the Company Situation section, the total information is technically preserved, but the *impact density* is not. In v1, Finding 3 (EGA/Inola standalone) functions as a self-contained demand thesis. Within ~400 words, the reader absorbs: the smelter exists ($5B, JDA signed, Bechtel FEED), it requires 1.5M t/yr of alumina, the U.S. has only 400K t/yr of domestic supply (structural 1.05M t/yr deficit), Brimstone is 180 miles away by truck, PSO has committed $3.2B+ in utility infrastructure (proving the smelter is real), and the policy incoherence is acute ($500M Century grant maintained, $189M Brimstone grant cancelled). The reader finishes that finding thinking: "The demand is real, the proximity is unique, and the government is accidentally creating the opportunity by funding one half and killing the other."

In v4, this information is fragmented:

- The 1.5M t/yr demand figure appears in Finding 1's context (to justify why the alumina binary matters financially)
- The FEED infrastructure lock-in appears as Window 2 of Finding 3 (compressed into one-third of a timing finding)
- The PSO infrastructure commitment ($3.2B+) and the policy incoherence ($500M/$189M contradiction) appear in the Company Situation section
- The 180-mile proximity, the truck-vs-barge infrastructure question, and the $589M platform-scale NPV don't appear prominently in the key findings at all

The result: v4's reader understands that the alumina quality matters (Finding 1) and that the FEED timeline creates urgency (Finding 3, Window 2), but never receives the full demand-side picture as a coherent argument. The single most compelling evidentiary anchor in the entire research — that a regulated utility committed $3.2B+ in real infrastructure to serve the smelter — is buried in the Company Situation rather than elevated as proof that the demand is bankable.

The brief's claim that a standalone EGA finding "would have restated material already covered in Section II" inverts the priority: if the material is strong enough to be a Key Finding, the Company Situation section should reference it, not the other way around.

**Verdict: Incorrect cut. Candidate E should have replaced Finding 3 (see Part 3).**

### Candidate F — Cement Major Forced Choice (Score: 15/20)

The brief's cut rationale: "absorbed into Finding 3... Standing alone, it would score lower on novelty."

**Was the cut justified?** Yes. The CRH/Amrize analysis is legitimately better as a component of a broader strategic argument than as a standalone finding. The non-compete constraint is the only truly non-obvious element, and it's preserved in Finding 3's first window. The ASTM C150 vs. C1157 distinction, while important, is established in the Company Situation section of both versions. v1 chose to run CRH as a standalone finding and it worked because v1 framed it as a buyer thesis (who buys, under what constraints, with what structure). v4 correctly recognizes that in the presence of the Kajima finding (which v1 didn't have), the CRH material is better distributed across Finding 3 and the buyer universe.

**Verdict: Correct cut, given the presence of Finding 2 (Kajima).**

---

## Part 3: The Finding 3 Question

The core tension: v4's Finding 3 bundles three known-ish catalysts into a convergence argument. Is that a structural observation ("obviously there's a window") or a genuine discovery?

**The brief's best case for Finding 3** rests on one specific claim: that the CRH non-compete provisions surviving Sublime's operational (but not legal) collapse create a constraint that "no individual tension point conveys." The brief's Thread C reasoning makes this explicit: "CRH cannot freely invest in Brimstone until that legal trigger fires." If true, this is non-obvious — it means the strategically optimal buyer (CRH) is legally frozen, which reshuffles the entire buyer priority stack in favor of EGA, Amrize, or financial sponsors. The brief's writer signal guidance correctly identifies this as "the surprising detail that makes the 'obvious' cement-major-pivot narrative non-obvious."

**The problem:** in v4's final text, this insight competes for attention with two other windows. The FEED lock-in and Series B imminence dilute the CRH legal constraint rather than amplifying it. An alternative framing — "CRH Is Frozen: Why the Strategically Optimal Buyer Can't Move and What That Means for Everyone Else" — would have been a more powerful standalone Finding 3 than the three-window bundle. But that's essentially Candidate F, which the brief cut.

**My recommended alternative: Replace Finding 3 with Candidate E (EGA/Inola standalone).**

Here's the case. The three-finding portfolio should answer three questions for the MD:

1. **What's the diligence risk you haven't seen?** → Finding 1 (alumina binary). Correct.
2. **What's the financing insight no one else has?** → Finding 2 (Kajima EPC). Correct.
3. **Why is this company strategically irreplaceable?** → This is the slot Finding 3 should fill.

v4's Finding 3 answers "when should you act?" — a useful question, but one that follows naturally from understanding *why* the company matters. The EGA/Inola standalone answers the "why" with hard infrastructure evidence. The timing urgency can then be communicated in a single paragraph at the end of the findings section or in the Deal Context, rather than consuming an entire finding slot.

Consider the MD's experience reading each version:

- **v1 sequence:** (1) The alumina might not be real → (2) But CRH needs a replacement and here's how they'd structure the deal → (3) And by the way, there's a $5B smelter 180 miles away that needs 1.5M t/yr of alumina. That sequence builds from risk to buyer to demand — each finding amplifying the previous one.

- **v4 sequence:** (1) The alumina might not be real → (2) But the financing has a shortcut through Kajima → (3) And three deadlines converge in Q3 2026. That sequence builds from risk to financing to timing — but the demand thesis (why anyone needs the alumina in the first place) never gets its own moment.

The v1 sequence is more persuasive for cold outreach because it ends on the strongest positive signal in the entire corpus: proven, bankable demand backed by $3.2B+ in committed utility infrastructure. v4's sequence ends on a timing argument that, while analytically sound, reads as advisory urgency-creation rather than market-structure discovery.

**What about Candidate D (Amazon dual consent)?** The brief scored it 15/20 and I agree with the cut. The dual consent event is structurally interesting but too narrow for a Key Finding slot. It lacks the "MD picks up the phone" quality — it's a deal-structuring insight for someone already engaged, not a discovery that creates engagement.

**What about the title issue?** The prompt raises the possibility that Finding 3 is correct and the title just doesn't convey the insight sharply enough. I don't think this is the issue. The v4 title ("Three Clocks, One Window") is actually quite good — it's the underlying material that's the problem. The CRH legal constraint is the only genuinely non-obvious element, and it's one-third of a three-part finding. A title change wouldn't fix the structural dilution.

---

## Part 4: Portfolio Balance

The selection brief self-assessed the portfolio as: A = diligence/valuation, B = structural/financing, C = timing/buyer. The intended balance is "one diligence/valuation finding, one strategic/buyer finding, one structural/timing finding."

**The self-assessment is slightly off.** Finding 3 is labeled "timing/buyer" but it's really timing/catalyst — it names multiple buyers but doesn't develop a specific buyer thesis. The CRH analysis is the most developed buyer thread, but it's presented as a constraint (CRH can't move) rather than an opportunity (here's exactly how CRH should structure an approach). The actual portfolio is: diligence risk + financing mechanism + catalyst timeline. That's analytically rigorous, but it's missing the demand-side "why this matters" finding that would anchor the entire document.

**For a cold outreach to a cement/materials MD, the ideal portfolio is:**

1. **A risk the MD hasn't considered** (Finding 1: alumina binary) — this creates credibility
2. **A structural insight that reveals hidden value or a hidden pathway** (Finding 2: Kajima EPC) — this demonstrates analytical depth
3. **A demand thesis that makes the opportunity concrete and urgent** (Candidate E: EGA/Inola) — this creates the "I need to act" impulse

v4 delivers (1) and (2) excellently and replaces (3) with a timing convergence argument. The problem is that timing urgency without a fully developed demand anchor reads as "you should hurry" without fully establishing "here's what you're hurrying toward." v1's EGA finding provides the demand anchor; v4 distributes it.

**Does the absence of a standalone buyer thesis weaken the document?** Yes, but less than I initially expected. Both versions handle the buyer universe in the Deal Context section, and both name the same candidates (EGA/Mubadala, CRH, Amrize, infrastructure funds). The difference is that v1 elevates CRH into a Key Finding with specific deal-structuring detail (CRH Ventures preferred equity, $75–125M anchor, board observer seat), which gives a CRH-focused banker something immediately actionable. v4 puts CRH in the buyer universe with less structural specificity. If the document is going to a banker whose primary client is CRH, v1's treatment is superior. If the document is going to a banker covering the broader materials space, v4's treatment is adequate.

**My recommended portfolio for a v5:**

1. **Finding 1: Alumina binary** (unchanged from v4)
2. **Finding 2: Kajima EPC financing shortcut** (unchanged from v4)
3. **Finding 3: EGA/Inola demand thesis** (Candidate E, restored as standalone, incorporating the FEED infrastructure lock-in as the time-sensitive dimension and the PSO $3.2B commitment as the bankability proof point)

The three-window timing convergence from v4's Finding 3 would be compressed into 2–3 sentences in the Deal Context section, where it functions as an "act by Q3 2026" call-to-action rather than a standalone finding. The CRH legal constraint gets a dedicated paragraph in the CRH buyer universe entry, which is where a CRH-focused banker will look for it.

This portfolio delivers: risk (alumina), mechanism (Kajima), and demand (EGA) — three fundamentally different dimensions that together make the case for both the company's strategic importance and the advisor's unique value-add. It retains v4's strongest improvement (Finding 2: Kajima) while recovering v1's strongest finding (EGA/Inola) and discarding v4's weakest (three-window timing).

---

## Summary Judgment

| Finding | v4 Selection | Assessment | Recommendation |
|---|---|---|---|
| Finding 1 | Alumina binary ($245M) | Correct | Keep |
| Finding 2 | Kajima EPC financing | Correct — strongest improvement over v1 | Keep |
| Finding 3 | Three Clocks, One Window | Defensible but suboptimal | Replace with EGA/Inola standalone (Candidate E) |

The selection brief did excellent work on the first two findings — particularly Finding 2 (Kajima), which represents genuinely novel synthesis that neither version v1 nor any public analysis has produced. The brief's analytical framework (cross-TP threading, selection matrix, portfolio balance check) is rigorous and well-documented. The error was in the Finding 3 slot: the brief overvalued the compound-timing mechanism's novelty while undervaluing the standalone demand thesis's persuasive power for the specific use case (cold outreach to an MD who needs to be convinced this company is worth a phone call). The "absorption" of Candidate E into Findings 1 and 3 preserved the information but diluted the impact.

v4 is a better document than v1 overall — primarily because Finding 2 (Kajima) is a substantial upgrade over v1's Finding 2 (CRH standalone). But v1's Finding 3 (EGA/Inola) is stronger than v4's Finding 3 (Three Clocks). The optimal document would take v4's Findings 1 and 2 and v1's Finding 3.
