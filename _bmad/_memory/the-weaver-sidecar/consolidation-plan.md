# Consolidation Plan

## Analysis Summary

### Phase 1: Scoping Review (UNCHANGED)
- **Type:** Scoping review (PRISMA-ScR) of AI in geriatric nutrition
- **Scope:** 25 studies, mapping translational evidence on deployed/operationally-tested AI systems
- **Structure:** Introduction > Methods > Results > Discussion > Conclusion > Appendices (search strategy + included studies table)
- **Key findings:** 92% prototype/pilot stage, 4 application categories (behavior change, dietary assessment, screening, activity recognition), 84% private datasets, translational gap between technical capability and clinical deployment

### Phase 2: Design Science Research - "Snap and Say" (REVISED 2026-03-10)
- **Type:** DSR artifact design and evaluation
- **Scope:** Multimodal agentic AI system for dietary assessment targeting older adults
- **Structure:** Introduction > Methodology (DSR Problem ID + 6 Objectives) > Artifact (6 sections) > Evaluation (benchmarking + Digital Buffet + threshold calibration) > Discussion (full academic prose, 7 limitation subsections) > Conclusion
- **Key findings:** 22.8% MAE reduction (agentic vs single-shot), 30.6% on Complex items, TPR=76% (0.759, 95% CI [0.655, 0.840]) on Complex items, TNR≈63% on Simple items, Pareto-optimal thresholds $C_{\text{thresh}}=5.0 / \text{Conf}_{\text{thresh}}=0.85$ (identified via two-phase sweep: N=500 full-distribution for TNR + N=80 stratified Complex-only for TPR), caloric MAE at optimal=92.7 kcal, N=19 older adults validated usability, 7.1s average latency
- **Terminology (aligned):** "friction-fidelity paradox," "directed state graph" (not DCG), "Semantic Gatekeeper" (not Critique step), "deterministic complexity scoring," "clinical threshold routing," AMPM as gold standard (not WFR)

---

## Structural Mapping

### Phase 1 Sections (UNCHANGED)
| Section | Content |
|---------|---------|
| Introduction | Problem framing: aging + nutrition + AI gap, 7 RQs |
| Methods | PRISMA-ScR, PCC framework, search strategy, screening, charting |
| Results | 25 studies synthesized across 4 categories, data modalities, deployment maturity |
| Discussion | Translational gap, early-stage evaluations, data quality, usability, workflow integration, data access, limitations |
| Conclusion | Summary: early stage, data transparency, need for larger evaluations |
| Appendix A | Full MEDLINE search strategy |
| Appendix B | Characteristics of 25 included studies |

### Phase 2 Sections (REVISED 2026-03-10)
| Section | Content |
|---------|---------|
| Introduction | Friction-fidelity paradox, AMPM gold standard, agentic AI proposal, 3 RQs with sub-questions, thesis roadmap |
| Methodology §1 | DSR framework (Peffers), Problem Identification (3 subsections: Burden of Dietary Assessment, Conversational Interfaces and Ambiguity Problem, Motivation for Artifact) |
| Methodology §2 | Objectives of a Solution (6 design objectives with DSR knowledge base grounding) |
| Artifact §1 | System Architecture Overview (4 subsystems: PWA, API server, agent layer, data layer, mapped to Hevner's three-cycle view) |
| Artifact §2 | Dynamic Complexity Scoring: formula $C = \sum w_d L_d^2 + P_{\text{sem}}$, Food Class Registry, three-tier routing |
| Artifact §3 | **NEW** Multimodal Input Pipeline (capture, transcription via Whisper, LLM fusion, streaming) |
| Artifact §4 | **NEW** Dynamic Routing and AMPM Subgraph (threshold routing, Detail Cycle, Final Probe, safety budget) |
| Artifact §5 | Prompt Engineering and Model Configuration |
| Artifact §6 | Geriatric-Centric Interface Design |
| Evaluation §1 | Simulated Benchmarking: Oracle protocol, $N=500$ Nutrition5k, MAE comparison table |
| Evaluation §2 | **NEW** Calibration of Routing Thresholds (parameter sweep, Pareto boundary) |
| Evaluation §3 | **NEW** User Experience: $N=19$ older adults, adapted SUS/NASA-TLX, 3 findings |
| Evaluation §4 | **NEW** Qualitative Insights: latency friction, acoustic challenges, competence expectations |
| Discussion | **REWRITTEN** Full academic prose: interpretation, objective-level assessment (all 6), literature contextualisation (3 departures), 7 limitation subsections, future directions |
| Conclusion | **NEW** Summary, principal findings, 3 knowledge contributions (Gregor & Hevner framework), limitations/future work, closing remarks |

---

## Overlap Analysis (REVISED 2026-03-10)

### [OVERLAP: Repeated background on aging populations and nutritional challenges]
Both introductions establish aging + chronic conditions + dietary assessment context. Phase 2 is now more focused (diabetes/sarcopenia + AMPM gold standard) but still covers the same ground as Phase 1's broader landscape. **Decision (unchanged):** Consolidate into single authoritative introduction; Phase 2's framing becomes the problem narrowing. **Update:** Phase 2's rewritten intro is sharper and more focused — the overlap is narrower than before but still present.

### [OVERLAP: AI in nutrition landscape description]
Phase 1 comprehensively maps the field; Phase 2 intro paragraph 3 references "our preceding scoping review" with `[CITATION NEEDED]`. **Decision (unchanged):** Phase 1's landscape belongs in Literature Review chapter; Phase 2 should reference it via cross-reference. **Update:** Phase 2 now handles this more cleanly — a single paragraph callbacks to the review rather than re-describing the landscape.

### [OVERLAP: Translational gap framing]
Both phases identify the prototype-to-deployment gap. **Decision (unchanged):** Single narrative arc: gap identified (review) → gap addressed (artifact). **Update:** Phase 2 now explicitly uses the 92% figure from Phase 1, making the connection tighter but still needing a formal cross-reference.

### [OVERLAP: Usability barriers for older adults]
Phase 1 Discussion on usability mismatch and Phase 2's Problem Identification §2.1 both cite Wildenbos, Czaja, Berkowsky for age-related barriers. **Decision (unchanged):** Consolidate citations; primary treatment in Problem Identification, cross-reference in unified discussion. **Update:** Overlap is now more extensive — Phase 2's Problem ID section has substantial usability argumentation that partially duplicates Phase 1 Discussion.

### [OVERLAP: AMPM methodology description]
**NEW.** Phase 2 now describes AMPM in three locations: Introduction (gold standard framing), Problem Identification (burden of dietary assessment), and Artifact §4 (AMPM Subgraph adaptation). While each serves a different purpose, the five-step AMPM is explained redundantly. **Decision:** In consolidated thesis, AMPM should be introduced once in the Methodology/Problem ID and referenced thereafter.

### [OVERLAP: Data quality challenges — RECLASSIFIED as complementary]
Phase 1 = field-level data quality challenges. Phase 2 Discussion = system-specific limitations (cultural/lexical ambiguity, plate waste, provider coupling). **Decision (unchanged):** These are complementary, not duplicative. Both belong in unified discussion.

---

## Gap Analysis (REVISED 2026-03-10)

### [GAP: RESOLVED — Phase 2 Discussion is incomplete]
~~The Phase 2 discussion section is in draft/bullet-point form.~~ **STATUS: RESOLVED.** Discussion is now full academic prose with: interpretation of findings, objective-level assessment (all 6 objectives), literature contextualisation (3 departures from prior work), 7 limitation subsections (sample size, oracle vs real-world, cultural/lexical, intake vs serving, latency, provider coupling, threats to validity), and 6 future directions.

### [GAP: Phase 2 lacks a standalone Literature Review]
**STATUS: UNCHANGED.** Phase 2 embeds literature references within introduction and methodology but has no dedicated literature review section. In consolidated thesis, Phase 1 scoping review serves as the literature foundation. This is BY DESIGN for the consolidated structure — not a gap within Phase 2 itself.

### [GAP: RESOLVED — No explicit connection from Phase 1 findings to Phase 2 design decisions]
~~Still absent.~~ **STATUS: RESOLVED.** §2.5 contains 5 explicit gap-to-requirement bridges. §6.2 weaves 6 Phase 1 studies into the Contextualisation section. §6.3 traces 5 closed-loop threads from evidence gaps through design responses to evaluation outcomes. The Closed Loop is closed.

### [GAP: RESOLVED — Phase 2 does not reference Phase 1 citation keys — Closed Loop violation]
~~Self-citation unresolved, Phase 1 studies not brought back.~~ **STATUS: RESOLVED.** Self-citation replaced with "Chapter 2" cross-reference (consolidated thesis). §6.2 weaves 6 Phase 1 studies (Papathanail, Balsa, Chopra, Pfisterer, Di Martino, Seok) into the discussion with confirm/contradict/nuance pattern. Closed Loop closed.

### [GAP: RESOLVED — Consolidated conclusion missing]
~~Phase 2 has no conclusion.~~ **STATUS: RESOLVED.** Phase 2 now has a full conclusion with: summary, principal findings, 3 knowledge contributions (Gregor & Hevner framework), limitations/future work, closing remarks. For consolidated thesis, this conclusion needs to be expanded to encompass both phases.

### [GAP: RESOLVED — Ethical considerations thin across both phases]
~~No standalone Ethics section, no GDPR citations, no IRB.~~ **STATUS: RESOLVED.** §3.5 now contains: informed consent procedure, de-identified authentication (GDPR Art. 25), managed ephemerality (GDPR Art. 5(1)(c,e)), and WUR-REC governance model (supervisor-delegated oversight). GDPR also cited in §4.1.1 (Art. 25), §4.1.4 (Art. 32), and §6.3.4 (Art. 9, 32).

### [GAP: RESOLVED — Phase 2 user study results not reported in detail]
~~NASA-TLX results, interview findings, and participant demographics not presented.~~ **STATUS: RESOLVED.** Evaluation now reports: $N=19$ participants (Age ≥ 65), adapted SUS/NASA-TLX survey (Q1-Q13 Likert), three quantitative finding clusters (usability/learnability, temporal demand/complexity, clarification acceptance), qualitative insights (latency, acoustic challenges, competence expectations), Dutch-language participant quotes.

### [GAP: NEW — Threshold calibration methodology could be circular]
**NEW.** The threshold calibration ($C_{\text{thresh}}=15.0$, $\text{Conf}_{\text{thresh}}=0.85$) was performed on the same Nutrition5k dataset used for evaluation. Phase 2 Discussion acknowledges this as a threat to internal validity ("risk of overfitting the routing parameters to the specific characteristics of the Nutrition5k corpus"). This is appropriately flagged but remains an unresolved methodological limitation.

### [GAP: NEW — Digital Buffet ecological validity]
**NEW.** Phase 2 Discussion acknowledges that the Digital Buffet used "high-resolution images on a monitor rather than photographs of the participants' own meals." This is flagged as a threat to external validity. The usability findings may overestimate real-world performance.

---

## Core Novelty Detection (REVISED 2026-03-10)

### [CORE NOVELTY: Agentic AI architecture for dietary assessment]
The directed state graph (LangGraph) with three-tier clinical threshold routing is the primary technical contribution. This is NOT a vehicle — it IS the contribution. **Updated terminology:** "directed state graph" (not DCG), "Semantic Gatekeeper" (not Critique step), "threshold-gated deferral" as the architectural pattern name.

### [TECHNICAL PRESERVATION: Deterministic Complexity Scoring Engine]
The scoring formula $C = \sum w_d \cdot L_d^2 + P_{\text{sem}}$ with the Food Class Registry is a novel technical artifact. The quadratic penalty curve, three-tier routing logic (mandatory override > clinical threshold > confidence gate), and the "dominant factor" identification for question targeting must be preserved in full technical detail. **Updated:** Now has empirical calibration data: optimal $C_{\text{thresh}}=15.0$, $\text{Conf}_{\text{thresh}}=0.85$ from parameter sweep.

### [TECHNICAL PRESERVATION: Three-tier routing policy]
**EXPANDED from previous "Confidence-gated suppression logic."** The routing is now explicitly three-tiered: (1) mandatory override via Food Class Registry flags, (2) clinical threshold $C > \tau$ with configurable per-session $\tau$, (3) standard confidence gate at 0.85. Safety budget $N_{max}=2$. Empirically validated (two-phase sweep): TNR≈63% on Simple items, TPR=76% (0.759, 95% CI [0.655, 0.840]) on Complex items, at Pareto-optimal configuration $C_{\text{thresh}}=5.0$, $\text{Conf}_{\text{thresh}}=0.85$.

### [CORE NOVELTY: Friction-fidelity paradox as a design construct]
**NEW.** Phase 2 now formally names and defines the "friction-fidelity paradox" as a design construct within dietary information systems. The conclusion claims this formalisation as one of three knowledge contributions.

### [CORE NOVELTY: AMPM-to-software-agent translation]
**NEW.** The adaptation of the five-step clinician-administered AMPM into a truncated, budget-constrained LangGraph state machine is explicitly positioned as a translational contribution. The mapping of traditional steps to software nodes (Quick List → multimodal pipeline, Time/Occasion → PWA metadata, Detail Cycle → LangGraph node, etc.) is novel.

### [CORE NOVELTY: Evidence gap mapping methodology]
Phase 1's evidence gap map visualization (application goals x study settings x maturity) is a methodological contribution. UNCHANGED.

### [CORE NOVELTY: Two-phase scoping review → DSR pipeline]
The thesis structure itself (systematic evidence mapping → artifact design informed by that mapping) is a methodological contribution. UNCHANGED.

---

## Citation Gap Analysis (REVISED 2026-03-10)

### [CITATION GAP: RESOLVED — Phase 2 self-citation]
~~`[CITATION NEEDED]` placeholder.~~ **STATUS: RESOLVED.** Consolidated thesis uses "Chapter 2" cross-reference directly. No external self-citation needed.

### [CITATION GAP: RESOLVED — Agentic AI definitions]
~~No canonical definition.~~ **STATUS: RESOLVED.** §1.3 now explicitly acknowledges the absence of a field-wide consensus definition and operationalises the term through converging characterisations (Xi et al. 2025, Qiu et al. 2024, Sumers et al. 2023). Defined as "LLM-driven systems capable of autonomous reasoning, tool use, and iterative self-correction within a bounded task." Examples-based definition is epistemically honest for a nascent field.

### [CITATION GAP: RESOLVED — AMPM methodology]
~~Only Moshfegh et al. 2008.~~ **STATUS: RESOLVED.** Blanton et al. 2006 added alongside Moshfegh 2008 in §3.2.1 as validation evidence for the AMPM methodology.

### [CITATION GAP: RESOLVED — Geriatric usability standards]
~~No WCAG 2.1 or geriatric-specific HCI guidelines.~~ **STATUS: RESOLVED.** WCAG 2.1 Level AA cited in §4.6 with guideline-level references (2.1 Keyboard Accessible, 1.3 Adaptable, 1.4 Distinguishable). Framed as "guided by" rather than "compliant with."

### [CITATION GAP: RESOLVED — Privacy/regulatory compliance]
~~No HIPAA/GDPR citations.~~ **STATUS: RESOLVED.** GDPR cited across 4 locations: Art. 25 (§3.5, §4.1.1), Art. 5(1)(c,e) (§3.5), Art. 32 (§4.1.4), Art. 9+32 (§6.3.4). HIPAA omitted — EU context (Dutch participants).

### [CITATION GAP: CLOSED — Nutrition5k dataset limitations]
~~No geriatric representativeness citations.~~ **STATUS: CLOSED (no action needed).** Limitations acknowledged in §6.4.7 (Western dietary bias, overfitting risk). No published literature discusses Nutrition5k's geriatric representativeness because the dataset lacks age metadata. The limitation is honestly framed; no citation exists to add.

### [CITATION GAP: NEW — DSR knowledge base references]
Phase 2 now cites Gregor 2006 (theory taxonomy), Hevner 2004 (three-cycle view), Peffers 2007 (process model), Venable 2016 (FEDS evaluation framework). These are well-grounded. No gap.

### [CITATION GAP: RESOLVED — Closed Loop citations missing]
~~Phase 1 studies not brought back.~~ **STATUS: RESOLVED.** CL step wove 6 Phase 1 studies into §6.2: Papathanail (image-based MAE comparison), Balsa (usability barriers), Chopra (LLM coaching extension), Pfisterer (food segmentation ceiling), Di Martino (LTC operational deployment), Seok (longitudinal clinical impact). Each follows confirm/contradict/nuance pattern.

---

## Proposed Unified Table of Contents (REVISED 2026-03-10)

### Front Matter
- Title Page
- Abstract
- Acknowledgements
- Table of Contents
- List of Figures
- List of Tables
- List of Abbreviations

### Chapter 1: Introduction
**Rationale:** Single entry point. Consolidate both introductions into one narrative arc: aging challenge → dietary assessment burden → friction-fidelity paradox → two-phase research design.
- 1.1 Background and Problem Context (consolidated)
- 1.2 The Friction-Fidelity Paradox (Phase 2's core framing, now the thesis's central construct)
- 1.3 Research Gap and Motivation (translational gap → need for evidence mapping AND artifact design)
- 1.4 Research Questions (Phase 1 RQs as "Evidence Mapping" + Phase 2 RQs as "Artifact Design & Evaluation")
- 1.5 Research Approach Overview (two-phase: scoping review → DSR)
- 1.6 Thesis Structure

### Chapter 2: Literature Review (Scoping Review)
**Rationale (unchanged):** Phase 1 IS the literature review.
- 2.1 Introduction (shortened Phase 1 intro)
- 2.2 Methods (Phase 1 methods, full PRISMA-ScR)
- 2.3 Results (Phase 1 results)
- 2.4 Discussion of Review Findings (Phase 1 discussion)
- 2.5 Implications for System Design (NEW bridging section: gap-to-requirement mapping)

### Chapter 3: Methodology
**Rationale:** DSR framework + Problem Identification + Objectives. Phase 2's expanded methodology content now fills this chapter substantially.
- 3.1 Design Science Research Framework (Peffers et al.)
- 3.2 Problem Identification (Phase 2's three subsections: Burden, Ambiguity Problem, Motivation)
- 3.3 Objectives of a Solution (Phase 2's 6 design objectives)
- 3.4 Evaluation Strategy (mixed-method: benchmarking + Digital Buffet)
- 3.5 Ethical Considerations (NEW — informed consent, de-identified auth, managed ephemerality, IRB)

### Chapter 4: Artifact Design — Snap and Say
**Rationale:** Technical heart. Updated to reflect Phase 2's expanded artifact description.
- 4.1 System Architecture Overview (4 subsystems, Hevner's three-cycle mapping)
- 4.2 Dynamic Complexity Scoring and Agent Routing (formula, Food Class Registry, three-tier routing)
- 4.3 Multimodal Input Pipeline (capture, Whisper transcription, LLM fusion, streaming)
- 4.4 Dynamic Routing and the AMPM Subgraph (threshold routing, Detail Cycle, Final Probe, safety budget)
- 4.5 Prompt Engineering and Model Configuration
- 4.6 Geriatric-Centric Interface Design

### Chapter 5: Evaluation
**Rationale:** Updated to reflect Phase 2's expanded evaluation. User study results are now present.
- 5.1 Simulated Benchmarking: Oracle Protocol ($N=500$)
- 5.2 Calibration of Routing Thresholds (parameter sweep, Pareto boundary)
- 5.3 User Experience: Digital Buffet Protocol ($N=19$, SUS/NASA-TLX)
- 5.4 Qualitative Insights and Edge Cases

### Chapter 6: Discussion
**Rationale (unchanged):** The Closed Loop. Phase 2 now has full discussion content. The consolidation task is to weave in Phase 1 citations and cross-phase argumentation.
- 6.1 Interpretation of Findings (from Phase 2 Discussion, expanded with Phase 1 context)
- 6.2 Objective-Level Assessment (Phase 2's 6-objective assessment)
- 6.3 Closing the Loop: From Evidence Gaps to Artifact Validation (BRIDGING — bring Phase 1 studies back)
- 6.4 Contextualisation Within the Literature (Phase 2's 3 departures + Phase 1 study comparisons)
- 6.5 Limitations (holistic: review + artifact + evaluation, 7 subsections from Phase 2 + Phase 1 methodological limitations)
- 6.6 Future Directions (consolidated)

### Chapter 7: Conclusion
**Rationale:** Phase 2 now has a strong conclusion. Expand to encompass both phases.
- 7.1 Summary of Research (both phases)
- 7.2 Principal Findings (from both phases)
- 7.3 Contribution to Knowledge (Phase 2's 3 contributions + Phase 1's evidence mapping contribution)
- 7.4 Limitations and Future Work
- 7.5 Closing Remarks

### References (unified .bib)

### Appendices
- Appendix A: MEDLINE Search Strategy (Phase 1)
- Appendix B: Included Studies Characteristics Table (Phase 1)
- Appendix C: Supplementary System Architecture Figures (Phase 2)
- Appendix D: Research Schema (Phase 2)
- Appendix E: Post-Task Survey Instrument (Phase 2)
- Appendix F: Task Script and Observation Log (Phase 2)
- Appendix G: Participant Consent Form (Phase 2)
- Appendix H: Food Class Registry Specification (Phase 2 technical detail)

---

## Structural Decision Rationale (REVISED 2026-03-10)

| Decision | Rationale |
|----------|-----------|
| Phase 1 as Chapter 2 (Literature Review) | Unchanged. The scoping review IS the literature foundation. |
| Expanded Methodology (Ch 3) | Phase 2 now has substantial Problem ID and Objectives content. This fills Ch 3 beyond just a brief DSR framework description. The 6 design objectives provide verifiable requirements that the evaluation can assess. |
| Expanded Artifact (Ch 4) with 6 sections | Phase 2 now has 6 distinct artifact sections including NEW multimodal pipeline and AMPM subgraph. These deserve individual treatment. |
| Evaluation includes threshold calibration | Phase 2 now includes systematic parameter sweep. This methodological rigour deserves its own subsection rather than being buried in results. |
| Unified Discussion (Ch 6) with Closed Loop | Phase 2 Discussion is now strong standalone prose. The consolidation task shifts from "writing the discussion" to "weaving in Phase 1 citations and cross-phase argumentation." |
| Expanded Conclusion (Ch 7) | Phase 2 now has a substantial conclusion with knowledge contribution framework. Expand to encompass both phases rather than writing from scratch. |
| Ethics section added (3.5) | COMPLETE. Informed consent, de-identified auth (GDPR Art. 25), managed ephemerality (GDPR Art. 5(1)(c,e)), WUR-REC governance model. |
| Bridging section (2.5) | COMPLETE. 5 gap-to-requirement bridges drafted (BR step). |
