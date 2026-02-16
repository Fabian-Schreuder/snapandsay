---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - _bmad-output/brainstorming/brainstorming-session-2026-02-16.md
  - _bmad-output/planning-artifacts/research/domain-nutritional-complexity-research-2026-02-16.md
  - docs/project-context.md
  - docs/prd.md
  - docs/architecture.md
  - docs/epics.md
  - docs/ux-design-specification.md
  - docs/benchmarking.md
date: 2026-02-16
author: Fabian
---

# Product Brief: snapandsay

## Executive Summary

**Snap and Say** bridges the critical "Friction-Fidelity Trade-off" in dietary assessment for older adults. By pivoting from **Passive AI** (guessing pixels) to **Agentic AI** (reasoning and negotiation), it enables voice-first, conversational interactions that actively resolve "Hidden Complexity." This approach ensures medical-grade data fidelity for chronic disease management without the cognitive burden of traditional apps, effectively solving the "Cold Start" problem for the $157B predictive health market.

---

## Core Vision

### Problem Statement

Current dietary assessment tools force a binary choice: **High Friction / High Accuracy** (weighed logs, clinical tools) or **Low Friction / Low Accuracy** (simple photo apps, mass market). For older adults managing chronic conditions, neither works: manual logging is too burdensome, and "magic" scanners fail to capture critical "hidden" nutritional data (the Triangle of Ambiguity). This "Input Problem" renders most patient-generated data useless for clinical decision-making.

### Problem Impact

*   **Clinical:** Inaccurate data leads to poor medication adjustments and health outcomes for diabetes and CVD patients.
*   **Economic:** Malnutrition and poor chronic disease management cost the healthcare system over $157 billion annually.
*   **User:** "Visual Biomimicry" (e.g., vegan cheese vs. cheddar) creates a trust gap when AI "hallucinates" ingredients it cannot see, leading to user abandonment.

### Why Existing Solutions Fall Short

*   **Manual Loggers (e.g., Cronometer):** Rely on users being "Data Entry Clerks." High accuracy, but unsustainable friction for the main demographic.
*   **Visual-Only AI (e.g., SnapCalorie):** Hits the "Visual Biomimicry" wall. Depth sensors can measure volume but cannot detect density, cooking fats, or hidden sugars.
*   **Black Box AI:** Lacks **Explainability**. Users cannot verify *why* an estimation was made or correct it easily ("Computer says no").

### Proposed Solution

**Snap and Say** is an **Agentic, Voice-First** dietary assessment platform that negotiates truth with the user.
*   **Active Reasoning:** The system identifies ambiguity (e.g., "I see mashed potatoes, but I don't know the fat content") and proactively asks clarifying questions ("Did you add butter or cream?").
*   **Multimodal Context:** Combines visual data with voice transcripts to capture determining factors that pixels miss.
*   **Adaptive Memory:** Learns user habits (e.g., "User always drinks black coffee") to silence unnecessary questions over time.

### Key Differentiators

*   **The "Agentic Wedge":** The only system that focuses on **Reasoning** about the unseen rather than just **Sensing** the visible.
*   **Resolution of the "Triangle of Ambiguity":** Specifically engineered to target Hidden Ingredients, Invisible Prep, and Portion Uncertainty.
*   **Senior-Centric Design:** Accessible, voice-led interface that removes the need for typing, searching, or complex menu navigation.

## Target Users

### Primary Users

**1. Martha (The "Gentle Nudge" User)**
*   **Context:** 72 years old, lives alone. Values independence but struggles with memory and arthritis.
*   **Motivation:** Wants to keep her doctor happy without the "chore" of logging.
*   **Pain Point:** Typing on small screens is painful; remembering to log is hard.
*   **Success Vision:** A "helpful friend" that reminds her to eat and listens when she speaks, handling the details for her.

**2. Robert (The "Precision Control" User)**
*   **Context:** 68 years old, retired engineer, Type 2 Diabetic.
*   **Motivation:** Data accuracy. He trusts numbers, not "magic."
*   **Pain Point:** Fear that AI "guesses" will mess up his insulin planning.
*   **Success Vision:** A system that respects his corrections ("It's cauliflower rice, not white rice") and updates the data instantly.

### Secondary Users

**1. Dr. Chen (The Clinician)**
*   **Role:** Geriatrician with limited time (15 mins/patient).
*   **Need:** Aggregated trends ("Protein is down"), not raw logs.
*   **Value:** Uses **Snap and Say** data to have meaningful care conversations rather than interrogation.

**2. Sarah (System Oversight)**
*   **Role:** Product Support / Human-in-the-Loop.
*   **Need:** Ability to review flagged "low confidence" logs and correct them to improve the system.

### User Journey

**The "Cold Start" Resolution (Martha's Flow):**
1.  **Trigger:** 1:30 PM. Martha forgot lunch. System sends a gentle audio nudge: "Hi Martha, did you grab a bite?"
2.  **Action:** Martha taps widely (easy touch target) and speaks: "Just a turkey sandwich and soup."
3.  **Agentic Loop:** System detects ambiguity (Soup type?). Agent asks: "Was that homemade or canned?"
4.  **Resolution:** Martha replies "Canned, low sodium." System logs 350kcal, 900mg sodium.
5.  **Value:** Zero typing, complete medical data captured.

**The "Correction" Flow (Robert's Flow):**
1.  **Action:** Robert snaps a curry.
2.  **Agent Output:** "Chicken Curry with Rice identified."
3.  **Correction:** Robert says: "That's cauliflower rice."
4.  **Verification:** Agent explicitly confirms: "Updating to cauliflower rice. Carbs reduced to 12g."
5.  **Value:** Trust established through verified correction.

## Success Metrics

### User Success Outcomes
*   **Zero-Friction Logging:** Users can log a full meal in **< 30 seconds** using voice/photo.
*   **Trust & Clarity:** Qualitative feedback confirms users feel "helped" not "interrogated" (Sentiment Analysis > Positive).
*   **Peace of Mind:** Users express confidence that their doctor "sees" their effort.

### Business Objectives
*   **North Star Metric:** **Verified Nutritional Data Points (VNDP) per User**.
    *   *Why:* We value *quality data generation* over simple engagement. A user who logs 3 perfect meals is more valuable than one who logs 10 messy ones.
*   **Retention:** **Day-30 Retention > 40%**.
    *   *Why:* Proves we have solved the "Cold Start" abandonment problem common in diet apps.
*   **Data Liquidity:** **> 90%** of user logs result in valid, structured SQL usable by clinicians.

### Key Performance Indicators (KPIs)
1.  **Autonomous Resolution Rate:** **> 80%** of logs handled without user abandonment or frustration.
2.  **Intervention Rate (IR):** **< 0.5** questions per meal (Average). We want the agent to be smart/quiet, not chatty.
3.  **Correction Rate:** **< 10%** of agent-generated logs require manual user editing.
3.  **Correction Rate:** **< 10%** of agent-generated logs require manual user editing.
4.  **Safety:** **100%** of "unsafe" or "ambiguous" inputs (e.g., medical questions) are refused/flagged.

## MVP Scope

### Core Features (Phase 1)
1.  **Multimodal Capture:** Users can photo and voice-note a meal simultaneously.
2.  **Agentic Orchestrator:** LangGraph backend that "reasons" about the input before logging.
3.  **Proactive Nudge:** Simple scheduled push notification ("Did you eat lunch?") to trigger the flow.
4.  **Adaptive Memory:** System remembers "Black Coffee" preference to avoid finding it ambiguous.
5.  **Verified Log View:** A simple, read-only list of today's meals with nutritional breakdown.

### Out of Scope for MVP
*   **Clinician Dashboard:** Researchers will query SQL directly; no UI needed yet.
*   **EHR Integration (FHIR):** Too complex for MPV; data export via CSV is sufficient.
*   **Social/Family Features:** No "Worried Child" view in Phase 1.
*   **Complex Auth:** No email/password; simple Device UUID is enough for research.

### MVP Success Criteria
*   **Adoption:** 50 Beta users logging > 2 meals/day for 2 weeks.
*   **Validation:** 20 "Ground Truth" weighed meals compared against Agent logs with < 15% error.

### Future Vision
*   **Phase 2:** The "Metabolic Digital Twin" that predicts sugar spikes before they happen.
*   **Phase 3:** Closed-loop integration with clinical teams where the Agent alerts the doctor of dangerous trends.

<!-- Content will be appended sequentially through collaborative workflow steps -->
