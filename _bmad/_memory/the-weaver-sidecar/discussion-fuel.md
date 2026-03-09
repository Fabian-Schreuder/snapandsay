# Discussion Fuel

## Status
Initialized during [AN] Analyze step. Accumulating editorial decisions for unified discussion drafting.

## Accumulated Fuel

### From Analysis Step

#### DF-001: The Two-Phase Structure as Methodological Contribution
- **Source:** Structural analysis of both phases
- **Decision:** The thesis demonstrates a replicable pattern: scoping review -> DSR artifact design informed by review gaps
- **Discussion relevance:** This is worth framing as a methodological contribution. Few MSc theses in health informatics explicitly trace the path from evidence mapping to artifact design. The Closed Loop Model (baseline -> metrics -> close) should be presented as the thesis's epistemological backbone.

#### DF-002: The 92% Prototype Problem
- **Source:** Phase 1 Results (92% of systems at prototype/pilot stage)
- **Decision:** This finding is THE justification for Phase 2. The field has ideas but not operational systems.
- **Discussion relevance:** Phase 2's Snap and Say should be positioned not as "yet another prototype" but as a system designed with deployment consciousness (PWA, cloud-native, configurable thresholds). However, it IS still a prototype - this tension must be acknowledged honestly.

#### DF-003: The Translational Gap Thread
- **Source:** Phase 1 Discussion + Phase 2 Introduction
- **Decision:** Both phases identify the same gap from different angles. Phase 1 maps it empirically; Phase 2 attempts to bridge it.
- **Discussion relevance:** The unified discussion should trace this thread explicitly: "Our review identified that X... our artifact addresses this by Y... however, our evaluation reveals that Z remains unresolved."

#### DF-004: Usability as the Forgotten Variable
- **Source:** Phase 1 Discussion (usability mismatch) + Phase 2 Artifact (geriatric-centric design)
- **Decision:** Phase 1 found that existing systems don't design for older adults. Phase 2 explicitly addresses this with Tap-to-Toggle, haptic feedback, high-contrast UI.
- **Discussion relevance:** Direct gap-to-solution mapping. But the Digital Buffet results are needed to close this loop - did the geriatric-centric design actually work?

#### DF-005: The Confidence-Gating Innovation vs Clinical Reality
- **Source:** Phase 2 Evaluation (92% TNR on simple items, 78% trigger on complex)
- **Decision:** The suppression logic works in simulation but hasn't been validated with real geriatric users providing real (imperfect) answers.
- **Discussion relevance:** Honest epistemic positioning. The Oracle simulation isolates architecture from human variability - this is a strength for technical validation but a limitation for clinical claims.

#### DF-006: Cultural and Contextual Blind Spots
- **Source:** Phase 2 Discussion (draft) - cultural/lexical context, plate waste
- **Decision:** These are genuine limitations that extend beyond the system's current scope.
- **Discussion relevance:** Frame as "the walls of what agentic AI can see" - the system closes the gap for hidden ingredients but opens new questions about cultural interpretation and consumption vs serving.

#### DF-007: Data Availability Hypocrisy Risk
- **Source:** Phase 1 found 84% of studies used private datasets; Phase 2 uses Nutrition5k (public) for evaluation but the system itself stores user data in Supabase.
- **Discussion relevance:** The thesis should address whether Snap and Say perpetuates or addresses the data transparency problem it identified. Consider discussing open science implications.

#### DF-008: The LTC Gap Remains
- **Source:** Phase 1 Evidence Gap Map (no behavior change interventions in LTC settings)
- **Decision:** Phase 2's Snap and Say is designed for community-dwelling older adults, not LTC.
- **Discussion relevance:** Acknowledge that while the thesis addresses the translational gap, it does not address the setting gap. This is an honest limitation and a clear future direction.

#### DF-009: Missing User Study Results
- **Source:** Phase 2 Evaluation - Digital Buffet protocol described but NASA-TLX results not reported
- **Discussion relevance:** If these results exist but weren't written up, they are critical for the discussion. If the study wasn't completed, this is a major limitation that must be acknowledged. Either way, this gap must be resolved before the discussion can close the loop on RQ3.

#### DF-010: Complexity Scoring as Transferable Artifact
- **Source:** Phase 2 Section 3.3 - Dynamic Complexity Scoring
- **Decision:** The scoring mechanism ($C = \sum w_d \cdot L_d^2 + P_{sem}$) is potentially transferable beyond dietary assessment to any multimodal AI system needing confidence-based routing.
- **Discussion relevance:** Frame as a secondary contribution with broader applicability. But be careful not to overclaim - it hasn't been validated outside the dietary domain.
