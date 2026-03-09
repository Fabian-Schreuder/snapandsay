# Consolidation Plan

## Analysis Summary

### Phase 1: Scoping Review
- **Type:** Scoping review (PRISMA-ScR) of AI in geriatric nutrition
- **Scope:** 25 studies, mapping translational evidence on deployed/operationally-tested AI systems
- **Structure:** Introduction > Methods > Results > Discussion > Conclusion > Appendices (search strategy + included studies table)
- **Key findings:** 92% prototype/pilot stage, 4 application categories (behavior change, dietary assessment, screening, activity recognition), 84% private datasets, translational gap between technical capability and clinical deployment

### Phase 2: Design Science Research - "Snap and Say"
- **Type:** DSR artifact design and evaluation
- **Scope:** Multimodal agentic AI system for dietary assessment targeting older adults
- **Structure:** Introduction > Methodology (DSR framework) > Artifact Description > Evaluation > Discussion (INCOMPLETE - draft/bullet-point quality)
- **Key findings:** 22.8% error reduction with agentic loop vs single-shot, confidence-gating suppression logic works (92% TNR on simple items), geriatric-centric interface design, latency within tolerability thresholds

---

## Structural Mapping

### Phase 1 Sections
| Section | Content | Lines |
|---------|---------|-------|
| Introduction | Problem framing: aging + nutrition + AI gap, 7 RQs | ~24 lines |
| Methods | PRISMA-ScR, PCC framework, search strategy, screening, charting | ~72 lines |
| Results | 25 studies synthesized across 4 categories, data modalities, deployment maturity | ~80 lines |
| Discussion | Translational gap, early-stage evaluations, data quality, usability, workflow integration, data access, limitations | ~19 paragraphs |
| Conclusion | Summary: early stage, data transparency, need for larger evaluations | ~5 lines |
| Appendix A | Full MEDLINE search strategy | Table |
| Appendix B | Characteristics of 25 included studies | Long table |

### Phase 2 Sections
| Section | Content | Lines |
|---------|---------|-------|
| Introduction | Binary trade-off problem, AMPM rationale, agentic AI proposal, 3 RQs with sub-questions | ~32 lines |
| Methodology | DSR framework (Peffers), problem ID, design/development, evaluation strategy | ~20 lines |
| Artifact Description | System architecture, agentic workflow (DCG), complexity scoring, prompt engineering, geriatric UI | ~61 lines |
| Evaluation | Simulated user protocol (N=500), Digital Buffet protocol, results for RQ1-RQ3 | ~48 lines |
| Discussion | INCOMPLETE - bullet points on cultural context, plate waste, future directions | ~16 lines |

---

## Overlap Analysis

### [OVERLAP: Repeated background on aging populations and nutritional challenges]
Both introductions establish the same demographic context (aging population, malnutrition/sarcopenia, heterogeneous needs). Phase 1 intro lines 1-3 and Phase 2 intro line 1 cover identical ground. **Decision:** Consolidate into single authoritative introduction; Phase 2's framing becomes the problem narrowing after the landscape is established.

### [OVERLAP: AI in nutrition landscape description]
Phase 1 intro paragraphs 2-3 and Phase 2 intro paragraph 3 both describe AI capabilities in nutrition. **Decision:** Phase 1's comprehensive landscape belongs in a unified Literature Review; Phase 2's reference to it should be a brief callback ("As our preceding review demonstrated...").

### [OVERLAP: Translational gap framing]
Both phases identify the gap between technical AI capability and real-world deployment. Phase 1 frames it as the review's raison d'etre; Phase 2 frames it as the motivation for Snap and Say. **Decision:** Single narrative arc: gap identified (review) -> gap addressed (artifact).

### [OVERLAP: Usability barriers for older adults]
Phase 1 Discussion paragraph on usability mismatch and Phase 2's problem identification both cite age-related declines. **Decision:** Consolidate in problem identification; cross-reference in discussion.

### [OVERLAP: Data quality challenges]
Phase 1 Discussion on data quality in geriatric populations and Phase 2's discussion of plate waste / cultural context. **Decision:** These are complementary, not duplicative. Phase 1 = field-level challenges; Phase 2 = system-specific challenges. Both belong in unified discussion.

---

## Gap Analysis

### [GAP: Phase 2 Discussion is incomplete]
The Phase 2 discussion section is in draft/bullet-point form. It contains two substantive paragraphs (cultural context, plate waste) and a bullet list of future directions. This is the most critical gap - a consolidated thesis needs a robust, unified discussion that closes the loop.

### [GAP: Phase 2 lacks a standalone Literature Review]
Phase 2 embeds literature references within the introduction and methodology but has no dedicated literature review section. In a consolidated thesis, the scoping review findings would serve as the literature foundation.

### [GAP: No explicit connection from Phase 1 findings to Phase 2 design decisions]
Phase 1 identifies specific gaps (e.g., no behavior change in LTC, usability barriers, isolated applications). Phase 2's design addresses some of these (usability, workflow integration) but never explicitly traces "Finding A necessitated Feature B." This connective tissue is missing.

### [GAP: Phase 2 does not reference Phase 1 citation keys]
Phase 2 introduction uses `[CITATION NEEDED]` placeholder for the scoping review itself. Beyond this, Phase 2 does not bring back foundational papers from Phase 1 to confirm/contradict findings in its discussion - a Closed Loop violation.

### [GAP: Consolidated conclusion missing]
Phase 1 has a brief conclusion. Phase 2 has none. A unified thesis needs a conclusion that synthesizes both phases.

### [GAP: Ethical considerations thin across both phases]
Phase 1 mentions data access/privacy briefly. Phase 2 mentions HIPAA/GDPR nowhere. For a health informatics thesis, ethical data handling, informed consent for the user study, and regulatory compliance deserve explicit treatment.

### [GAP: Phase 2 user study results not reported in detail]
The Digital Buffet protocol is described but NASA-TLX results, interview findings, and participant demographics are not presented in the evaluation section. Either they were omitted or not yet written.

---

## Core Novelty Detection

### [CORE NOVELTY: Agentic AI architecture for dietary assessment]
The directed cyclic graph (DCG) with confidence-gated clarification is the primary technical contribution. This is NOT a vehicle - it IS the contribution. The architecture that mimics clinical AMPM methodology through automated multi-pass reasoning is novel.

### [TECHNICAL PRESERVATION: Dynamic Complexity Scoring mechanism]
The deterministic scoring formula $C = \sum w_d \cdot L_d^2 + P_{sem}$ with the Food Class Registry is a novel technical artifact. The quadratic penalty curve and three-tier routing logic (mandatory override > clinical threshold > confidence gate) must be preserved in full technical detail.

### [TECHNICAL PRESERVATION: Confidence-gated suppression logic]
The transition function $f(state)$ with $T=0.85$ and turn constraint $N=2$ is a specific technical design decision with empirical validation (92% TNR). Preserve.

### [CORE NOVELTY: Evidence gap mapping methodology]
Phase 1's evidence gap map visualization (application goals x study settings x maturity) is a methodological contribution that directly informed Phase 2's design space.

### [CORE NOVELTY: Bridging the scoping review to artifact design via DSR]
The two-phase structure itself (systematic evidence mapping -> artifact design informed by that mapping) is a methodological contribution. The thesis demonstrates how scoping review findings can directly drive DSR problem identification.

---

## Citation Gap Analysis

### [CITATION GAP: Phase 2 self-citation]
Phase 2 intro line 8: `[CITATION NEEDED]` for the scoping review. **Needed:** Self-citation to Phase 1 publication or chapter reference.

### [CITATION GAP: Agentic AI definitions]
Phase 2 cites Xi et al. 2025, Qiu et al. 2024, Sumers et al. 2023 for agentic AI but lacks a grounding definition from a canonical source. **Needed:** Foundational reference for agent architectures in healthcare context.

### [CITATION GAP: AMPM methodology]
Only Moshfegh et al. 2008 cited for AMPM. This is the original source but the methodology has been validated and updated since. **Needed:** More recent validation studies of AMPM (e.g., Raper et al. 2004, Blanton et al. 2006 or newer).

### [CITATION GAP: Geriatric usability standards]
Phase 2 cites Wildenbos, Czaja, and Berkowsky for aging barriers but lacks citations for specific accessibility guidelines (WCAG) or geriatric HCI design principles. **Needed:** WCAG 2.1 reference, geriatric-specific HCI guidelines.

### [CITATION GAP: Privacy/regulatory compliance]
No HIPAA, GDPR, or health data protection regulation citations in either phase. **Needed:** Regulatory framework references for health data in AI systems.

### [CITATION GAP: Nutrition5k dataset]
Phase 2 evaluation cites Thames et al. 2021 for Nutrition5k but does not discuss its limitations or representativeness for geriatric populations. **Needed:** Discussion of dataset limitations with supporting references.

---

## Proposed Unified Table of Contents

### Front Matter
- Title Page
- Abstract
- Acknowledgements
- Table of Contents
- List of Figures
- List of Tables
- List of Abbreviations

### Chapter 1: Introduction
**Rationale:** Single entry point that establishes the problem space, narrows from global aging challenge to the specific binary trade-off in dietary assessment, and presents the two-phase research design.
- 1.1 Background and Problem Context (consolidated from both Phase 1 and Phase 2 introductions)
- 1.2 Research Gap and Motivation (the translational gap -> need for both evidence mapping AND artifact design)
- 1.3 Research Questions (Phase 1 RQs as "Evidence Mapping" + Phase 2 RQs as "Artifact Design & Evaluation")
- 1.4 Research Approach Overview (two-phase: scoping review -> DSR)
- 1.5 Thesis Structure

### Chapter 2: Literature Review (Scoping Review)
**Rationale:** Phase 1 IS the literature review. The scoping review serves dual purpose: it maps the field AND identifies the specific gaps that Phase 2 addresses. This is the fabric's foundation.
- 2.1 Introduction (shortened Phase 1 intro, focused on review objectives)
- 2.2 Methods (Phase 1 methods, full PRISMA-ScR)
- 2.3 Results (Phase 1 results, all 4 application categories + cross-cutting themes)
- 2.4 Discussion of Review Findings (Phase 1 discussion, reframed as "what the field tells us")
- 2.5 Implications for System Design (NEW bridging section: explicit gap-to-requirement mapping)

### Chapter 3: Methodology
**Rationale:** DSR framework presentation, separated from the artifact itself for clarity.
- 3.1 Design Science Research Framework
- 3.2 Problem Identification and Objectives (linked to Chapter 2 findings)
- 3.3 Design and Development Approach
- 3.4 Evaluation Strategy (mixed-method: artificial benchmarking + naturalistic study)
- 3.5 Ethical Considerations (NEW - informed consent, data handling, IRB approval if applicable)

### Chapter 4: Artifact Design - Snap and Say
**Rationale:** The technical heart. All [TECHNICAL PRESERVATION] content lives here.
- 4.1 System Architecture Overview
- 4.2 Agentic Workflow Implementation (DCG, state graph)
- 4.3 Dynamic Complexity Scoring and Agent Routing
- 4.4 Prompt Engineering and Model Configuration
- 4.5 Geriatric-Centric Interface Design

### Chapter 5: Evaluation
**Rationale:** Both evaluation protocols and their results.
- 5.1 Technical Performance: Simulated User Protocol (RQ1 + RQ3)
- 5.2 User Experience: Digital Buffet Protocol (RQ2 + RQ3)
- 5.3 Estimation Accuracy Results
- 5.4 Suppression Logic Efficiency Results
- 5.5 System Latency Results
- 5.6 User Experience Results (currently missing - needs writing or recovery)

### Chapter 6: Discussion
**Rationale:** The Closed Loop. This is where Discussion Fuel accumulates into a unified argument. Phase 1 papers return to confirm/contradict/nuance.
- 6.1 Principal Findings (unified across both phases)
- 6.2 Closing the Loop: From Evidence Gaps to Artifact Validation
- 6.3 The Agentic Trade-off: Intervention Depth vs User Burden
- 6.4 Cultural and Contextual Limitations (Phase 2 cultural context + plate waste)
- 6.5 Comparison with Existing Systems (bring back Phase 1 studies)
- 6.6 Limitations (holistic: review limitations + artifact limitations + evaluation limitations)
- 6.7 Future Directions (consolidated from both phases)

### Chapter 7: Conclusion
- 7.1 Summary of Contributions
- 7.2 Practical Implications
- 7.3 Closing Statement

### References (unified .bib)

### Appendices
- Appendix A: MEDLINE Search Strategy (from Phase 1)
- Appendix B: Included Studies Characteristics Table (from Phase 1)
- Appendix C: Supplementary System Architecture Figures (from Phase 2)
- Appendix D: Task Script and Observation Log (from Phase 2)
- Appendix E: Participant Consent Form (from Phase 2)
- Appendix F: Post-Task Survey Instrument (from Phase 2)
- Appendix G: Food Class Registry Specification (technical detail from Phase 2)

---

## Structural Decision Rationale

| Decision | Rationale |
|----------|-----------|
| Phase 1 as Chapter 2 (Literature Review) | The scoping review IS the literature foundation. Presenting it as a standalone review chapter serves dual purpose: establishes the field AND identifies gaps. Examiners expect literature review early. |
| Separate Methodology (Ch 3) from Artifact (Ch 4) | DSR methodology is the research framework; the artifact is the output. Separating them follows DSR convention and allows the methodology to reference the review findings as input. |
| Unified Discussion (Ch 6) | The Closed Loop Model requires that Phase 1 citations return in discussion. A unified discussion is the only structure that enables this. |
| Bridging section (2.5) | Explicit "gap-to-requirement" mapping prevents the reader from having to infer why the review matters for the artifact. This is the connective tissue. |
| Ethics section added (3.5) | Health informatics thesis examining a system for vulnerable populations requires explicit ethical treatment. Currently absent from both phases. |
| Appendix expansion | Technical detail (Food Class Registry, full system figures) moves to appendices to maintain narrative flow while preserving [TECHNICAL PRESERVATION] content. |
