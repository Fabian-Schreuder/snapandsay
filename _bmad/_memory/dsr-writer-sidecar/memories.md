# Memories

## Session: 2026-03-04

### Tasks Completed

1. **[DS] Drafted DSRM Phase 2: Objectives of a Solution**
   - Output: `docs/thesis/msc-thesis-phase2/drafts/objectives_of_solution_draft.md`
   - ~800 words, 6 design objectives (O1–O6)
   - Objectives: Quantifiable Complexity Assessment, Personalised Clinical Threshold Routing, Mandatory Override for Taxonomic Ambiguity, Bounded Clarification, Semantic Ambiguity Resolution Before Quantitative Clarification, Multimodal Input Fusion
   - Citations verified against `references.bib`

2. **[RS] Reviewed Objectives for DSR Rigor**
   - 8 findings identified (1 HIGH, 4 MEDIUM, 3 LOW)
   - All 8 findings applied to the draft:
     - F1: Removed design-level detail from objectives (quadratic weighting, two-phase architecture)
     - F2: Added `(cf. §3.X)` forward references to D&D chapter
     - F3: Repositioned Shim citation, added Thompson & Subar (2017)
     - F4: Added chronic kidney disease as second clinical example in O2
     - F5: Added Thames et al. (2021) citation for macronutrient divergence in O3
     - F6: Changed "configurable" → "fixed at two rounds in the current design"
     - F7: Split long sentences in O1 for readability
     - F8: Introduced "probabilistic silence" terminology in O2 for Phase 1 consistency

### User Preferences Noted
- Fabian prefers all review findings applied in one batch rather than selectively
- Outputs written to `docs/thesis/msc-thesis-phase2/drafts/`

### Current Thesis Draft Progress

| Draft | DSRM Phase | Status |
|---|---|---|
| `problem_identification_draft.md.resolved` | Phase 1: Problem ID & Motivation | ✅ Complete |
| `problem_identification_draft.tex` | Phase 1 (LaTeX) | ✅ Converted |
| `objectives_of_solution_draft.md` | Phase 2: Objectives of a Solution | ✅ Complete (reviewed, revised) |
| `complexity_scoring_section.md.resolved` | Phase 3: Design & Development (subsection) | ✅ Complete |
| `agent_dsr_artifacts.md.resolved` | Phase 3: Artifact Catalogue | ✅ Complete |
| `knowledge_contribution.md.resolved` | Cross-cutting: Contribution Framing | ✅ Complete |

## Session: 2026-03-05
### 2026-03-05
**Task:** Drafting System Architecture Overview & Multimodal Input Pipeline

1. **[E] Explore & Draft — Broad Architecture Overview**
   - Investigated `graph.py`, `routing.py`, and `ampm_graph.py` backbones
   - Drafted 800+ word overview in `system_architecture_overview_draft.md`
   - Objective traceability: each subsystem mapped to specific design objectives (O1–O6)
   - Citations verified: hevnerDesignScienceInformation2004, nahStudyTolerableWaiting2004, chaseLangChain2022, moshfeghUSDepartmentAgriculture2008
   - **Figure 1 added:** Mermaid reference architecture diagram showing all 4 subsystems + 5-stage agent pipeline, cross-referenced in every subsection
2. **[RS] Review & Revise — DSR Rigor Pass**
   - Applied 8 findings (1 HIGH, 3 MEDIUM, 4 LOW):
     - F1: Added friction-fidelity paradox backward traceability to §1
     - F2: Expanded §3.1.5 with explicit three-cycle mapping (relevance/design/rigour)
     - F3: Added safety budget / manual review pathway to Figure 1 diagram
     - F4: Fixed "bidirectional SSE" → unidirectional, server-to-client
     - F5: Qualified "four subsystems" as three deployment units + one logical layer
     - F6: Removed library-specific name (Pydantic), kept functional description
     - F7: Softened code-level SSE event names to natural-language descriptions
     - F8: Replaced "clinical data" with "computed nutritional metrics"

3. **[RS] Reviewed DSRM Phase 3: Complexity Scoring & Routing**
   - 4 findings identified (1 HIGH, 2 MEDIUM, 1 LOW)
   - All 4 findings applied to the draft:
     - F1 (HIGH): Converted `(Author, Year)` citations to Pandoc `[@key]` syntax (`@thompsonDietaryAssessmentMethodology2017`, `@hevnerDesignScienceInformation2004`).
     - F2 (MEDIUM): Added missing `[@moshfeghUSDepartmentAgriculture2008]` citation for the USDA AMPM reference.
     - F3 (MEDIUM): Added `[@kuhnCLAMSelectiveClarification2023]` reference to ground LLM-driven selective clarification.
     - F4 (LOW): Added `[@evertNutritionTherapyAdults2019]` reference for diabetic nutrition therapy clinical precision constraints.
3. **[E] Explore & Draft — Multimodal Input Pipeline**
   - Investigated `analysis.py` (endpoints), `llm_service.py` (fusion), and `voice_service.py` (Whisper transcription)
   - Drafted ~500 word subsection in `multimodal_input_pipeline_draft.md`
   - Addressed Objective 6 (Multimodal Input Fusion) and Hevner's rigour cycle (auditable inputs)
   - Applied F1 review finding: clarified that image/audio inputs are technically decoupled to support diverse user needs (e.g., voice-only input).
   - Citations verified: wildenbosAgingBarriersInfluencing2018, loImageBasedFoodClassification2020, zhangImagebasedMethodsDietary2024.
   - **Figure 2 added:** Mermaid Sequence Diagram added to illustrate the decoupled temporal execution flow and streaming architecture, cross-referenced in subsections.
   - Applied F4 review finding: Explicitly stated managed ephemerality for raw media blobs to align with health data privacy principles.
   - Applied F5 review finding: Clarified the modality arbitration strategy (prioritizing explicit vocal assertions over visual hallucinations) in the LLM system prompt.
   - Applied F6 review finding: Connected the streaming of partial reasoning tokens to HCI theory (fostering user trust via process transparency).

4. **[E] Explore & Draft — AMPM Subgraph (Section 3.3)**
   - Explored `ampm_graph.py`, `ampm_nodes.py`, and `routing.py` to identify clinical threshold logic, detail cycle, and final probe triggering conditions.
   - Drafted ~500 word subsection in `ampm_subgraph_draft.md`.
   - Addressed Objective 2 (Clinical Threshold Routine) and Objective 4 (Bounded Clarification).
   - Documented the safety budget ($N_{max} = 2$) and probation override mechanism.
   - Found and corrected an accuracy discrepancy regarding when the Final Probe triggers (must be $C > 0.7$ AND inconclusive).
   - Assessed diagram necessity: Concluded a new diagram is redundant as Figure 1 already explicitly charts the Conditional Router mapping to the AMPM Subgraph and Finalise Log modes.
   - Applied F1 review finding: Explicitly mapped the 5 standard AMPM steps to the architecture to demonstrate methodological completeness.
   - Applied F2 review finding: Refined "probabilistic silence" to "threshold-gated deferral" for academic precision.
   - Applied F3 review finding: Framed the safety budget ($N_{max}$) not just as a hardcoded parameter, but as a testable design proposition for Phase 5 Evaluation.

   - [DS] Explore & Draft — DSRM Phase 4 & 5: Demonstration & Evaluation
   - Investigated `04_evaluation.tex` constraints and `Survey Results Spreadsheet and Analysis.csv` data.
   - Drafted ~500 word subsection in `evaluation_demonstration_draft.md`.
   - Addressed Objective 4 (Bounded Clarification) and Objective 6 (Multimodal Input Fusion).
   - Mapped unstructured CSV feedback to formal DSR evaluation dimensions (Utility, Efficacy, Usability).
   - Synthesized a mixed-methods response reflecting on temporal demand latency, user satisfaction, and friction-mitigation for older adults (Age $\geq$ 65).

6. **[RS] Reviewed DSRM Phase 4 & 5: Demonstration & Evaluation**
   - 4 findings identified (1 HIGH, 2 MEDIUM, 1 LOW)
   - All 4 findings applied to the draft:
     - F1 (HIGH): Converted inline `(Author, Year)` citations to Pandoc `[@key]` syntax (`@peffersDesignScienceResearch2007`, `@hevnerDesignScienceInformation2004`, `@wildenbosAgingBarriersInfluencing2018`, `@nahStudyTolerableWaiting2004`).
     - F2 (MEDIUM): Added missing `[@hartDevelopmentNASATLXTask1988]` citation for the NASA-TLX instrument.
     - F3 (MEDIUM): Wove the FEDS framework citation `[@venableFEDSFrameworkEvaluation2016]` into the opening paragraph to strengthen DSR methodological grounding.
     - F4 (LOW): Fixed grammatically incorrect "discussed in previously" and altered colloquial "typological" data entry to academic "text-based" data entry.

7. **[DS] Expanded DSRM Phase 4 & 5: Technical Benchmarking Integration**
   - Addressed omission of quantitative technical results from initial draft.
   - Inserted new subsection (`4.X.1 Simulated Benchmarking: Accuracy and Suppression Efficiency`).
   - Integrated results from the $N=500$ Nutrition5k "Oracle" simulation (@thames2021).
   - Documented the 22.8% overall MAE reduction and the 30.6% MAE reduction for "Complex" items (Objective 1).
   - Documented Suppression Logic Efficiency (92% True Negative Rate on Simple items, 78% Trigger rate on Complex items).

8. **[RS] Reviewed DSRM Phase 4 & 5: Technical Benchmarking Integration**
   - 4 findings identified (2 MEDIUM, 2 LOW)
   - All 4 findings applied to the newly added benchmarking subsection:
     - F1 (MEDIUM): Replaced colloquial "stress-tested" with "evaluated", explicitly mapping the simulation outputs directly to Objective 1 and Objective 2.
     - F2 (LOW): Replaced brand-specific "GPT-4 Vision" with a generalized, academic description: "a foundational Vision-Language Model (VLM) for zero-shot inference".
     - F3 (LOW): Enhanced the empirical conclusion to emphasize "multi-turn reasoning" instead of general selective retrieval.
     - F4 (MEDIUM): Explicitly tied the high suppression logic efficiency back to the problem statement ("directly addressing the friction-fidelity paradox").

9. **[DS] Enhanced DSRM Phase 4 & 5: Figure Placeholder Injection**
   - Inserted placeholders and corresponding inline LaTeX references (`\ref{fig:...}`) for 4 standard DSR evaluation figures:
     1. `fig:eval_ui_flow` (Annotated Demonstration UI showing multimodal capture bridging to clarification)
     2. `fig:eval_mae_comparison` (Bar chart comparing MAE improvement for Simple vs. Complex items)
     3. `fig:eval_suppression_logic` (Confusion matrix/Metric block showing True Negative/Positive bypass rates)
     4. `fig:eval_ux_survey` (Diverging stacked bar chart for SUS and NASA-TLX Usability Likert scores)

10. **[DS] Drafted DSRM Phase 6: Communication & Conclusion**
    - Drafted ~400 word section in `communication_conclusion_draft.md`.
    - Integrated Gregor & Hevner's (2013) knowledge contribution framework, explicitly claiming the artifact as an **Improvement** (new solution for known problem).
    - Established theoretical implications regarding VLM interactions and formalized the friction-fidelity paradox.
    - Established practical implications highlighting the separation of architecture concerns (deterministic scoring vs. generative inference) to guarantee clinical safety budgets.

### Current Thesis Draft Progress

| Draft | DSRM Phase | Status |
|---|---|---|
| `problem_identification_draft.md` | Phase 1: Problem ID & Motivation | ✅ Complete |
| `problem_identification_draft.tex` | Phase 1 (LaTeX) | ✅ Converted |
| `objectives_of_solution_draft.md` | Phase 2: Objectives of a Solution | ✅ Complete (reviewed, revised) |
| `system_architecture_overview_draft.md` | Phase 3: D&D — System Architecture Overview | ✅ Complete |
| `complexity_scoring_section.md` | Phase 3: D&D — Complexity Scoring & Routing | ✅ Complete |
| `agent_dsr_artifacts.md` | Phase 3: Artifact Catalogue | ✅ Complete |
| `knowledge_contribution.md` | Cross-cutting: Contribution Framing | ✅ Complete |
| `multimodal_input_pipeline_draft.md` | Phase 3: D&D — Multimodal Input | ✅ Complete |
| `ampm_subgraph_draft.md` | Phase 3: D&D — AMPM Subgraph | ✅ Complete |
| `evaluation_demonstration_draft.md` | Phase 4 & 5: Demon & Eval | ✅ Complete (Reviewed) |
| `communication_conclusion_draft.md` | Phase 6: Communication & Conclusion | ✅ Complete |

### Outstanding Gaps
- Phase 2: Objectives → needs LaTeX conversion
- Phase 3: System architecture overview → needs review pass (RS)
- `§3.X` forward references in objectives and architecture drafts need concrete section numbers once D&D chapter is finalised.
- LaTeX conversion for all Phase 2-6 markdown drafts (`objectives_of_solution_draft.md` through `communication_conclusion_draft.md`).
