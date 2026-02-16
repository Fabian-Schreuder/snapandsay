---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
inputDocuments:
  - '/home/fabian/dev/work/snapandsay/docs/analysis/product-brief-snapandsay-2025-12-03.md'
  - '/home/fabian/dev/work/snapandsay/docs/analysis/research/technical-Agentic-Multimodal-AI-Dietary-Assessment-research-2025-12-03.md'
workflowType: 'prd'
lastStep: 111
project_name: 'snapandsay'
user_name: 'Fabian'
date: '2025-12-03'
---

# Product Requirements Document - snapandsay

**Author:** Fabian
**Date:** 2025-12-03

## Executive Summary

**Snap and Say** is a conversational dietary assessment tool designed for older adults (65+) managing chronic conditions. It bridges the "Friction-Fidelity Trade-off" by using **Agentic AI** to enable voice-first, conversational logging. Unlike passive tracking apps, the system actively reasons about missing details and asks clarifying questions (e.g., "I can't see the dressing") to ensure medical-grade data fidelity without burdening the user. This approach solves the "Cold Start" problem and empowers clinicians with accurate, structured nutritional data.

### What Makes This Special

The core differentiator is the shift from **Passive AI** (Input Image -> Output Guess) to **Agentic AI** (Input -> Reason -> Clarify -> Output).
-   **Active Reasoning:** The system doesn't just guess; it identifies ambiguity and proactively resolves it through natural conversation.
-   **Zero-Friction for Seniors:** Designed specifically for accessibility, removing the need for complex menus, searching, or typing.
-   **Science-Ready Data:** Focuses on generating structured, verified nutritional data points (VNDP) rather than just engagement metrics.

## Project Classification

**Technical Type:** web_app
**Domain:** healthcare
**Complexity:** high

**Classification Notes:**
This project is classified as a **Healthcare Web Application**.
-   **High Complexity:** Due to the requirement for clinical-grade data accuracy, handling of sensitive health data (potential HIPAA implications), and the need for robust error handling in the agentic workflow to prevent "hallucinations" in a medical context.
-   **Regulatory Considerations:** While an MVP, the roadmap includes alignment with FHIR standards and potential future medical device considerations.
-   **Key Challenges:** Ensuring accessibility for the 65+ demographic while maintaining sophisticated backend agentic logic.

## Success Criteria

### User Success

-   **Zero-Friction Logging:** Users can log a meal in < 30 seconds using voice/photo without typing.
-   **Trust & Clarity:** Users feel "heard" and "helped" by clarifying questions, not interrogated. Measured by qualitative feedback ("It's like talking to a friend").
-   **Peace of Mind:** Users (and family) feel confident that their dietary data is being accurately captured for their doctor.

### Business Success

-   **North Star Metric:** **Verified Nutritional Data Points (VNDP) per User**. (Focus on *quality* data generation).
-   **Retention:** Day-30 Retention Rate > X% (proving "Cold Start" solution).
-   **Data Yield:** > 90% of logs result in valid, structured SQL data usable by clinicians.

### Technical Success

-   **Accuracy:** Structured Output Reliability > 99% (valid JSON schema).
-   **Performance:** Agent Latency < 5s for text, < 10s for vision analysis.
-   **Safety:** 100% of "unsafe" or "ambiguous" inputs are flagged for review or clarification (no hallucinations in medical record).

### Measurable Outcomes

-   **Autonomous Resolution Rate:** > 80% of logs handled without user abandonment.
-   **Correction Rate:** < 10% of agent-generated logs require user editing.

## Product Scope

### MVP - Minimum Viable Product (Research MVP)

-   **Core Loop:** Photo/Voice Input -> Agent Analysis -> Clarification (max 1 turn) -> Structured Log.
-   **Interface:** Mobile-responsive Web App (PWA) with simple chat UI.
-   **Backend:** LangGraph agent with GPT-4o Vision and Pydantic validation.
-   **Data:** Supabase (PostgreSQL) for structured storage.
-   **Auth:** Simple User ID (no complex OAuth).

### Growth Features (Post-MVP)

-   **Clinician Dashboard:** Visualization of longitudinal data for doctors.
-   **EHR Integration:** FHIR export/sync.
-   **Family Sharing:** "Worried Child" view.
-   **Personalized Insights:** "You're eating more protein this week!"

### Vision (Future)

-   **Digital Twin:** Metabolic simulation based on dietary intake.
-   **Voice-First Hardware:** Dedicated device or smart speaker integration.
-   **Closed-Loop Care:** Agent directly alerts care team of critical anomalies.

## User Journeys

### Journey 1: Martha's "Gentle Nudge" (Primary User - Success Path)
**The Character:** Martha (72), lives alone, values independence but is forgetful.
**The Challenge:** She knows she needs to track her lunch for Dr. Chen, but her arthritis makes typing painful, and she often forgets until it's too late.
**The Journey:**
1.  **Opening Scene:** It's 1:30 PM. Martha is settling in for her afternoon soaps. She completely forgot to log her turkey sandwich.
2.  **Rising Action:** Her phone chimes gently. It's the Snap and Say agent. "Hi Martha, hope you're having a nice afternoon. Did you manage to grab some lunch?" It's not a demand; it's a check-in.
3.  **Climax:** Martha taps the microphone button. "Oh, yes dear. I had a turkey sandwich and some tomato soup." She doesn't worry about portion sizes or brands.
4.  **Resolution:** The agent replies, "Sounds lovely. Was that the homemade soup or from a can?" Martha replies, "Canned, the low-sodium one." The agent confirms, "Got it. Logged for you." Martha feels supported, not managed.

### Journey 2: Robert's "Precision Control" (Primary User - Edge Case/Correction)
**The Character:** Robert (68), retired engineer, Type 2 Diabetic.
**The Challenge:** He trusts data, not "magic". He wants to ensure the AI isn't guessing wrong about his carb intake.
**The Journey:**
1.  **Opening Scene:** Robert sits down to a complex homemade curry. He knows the sauce has hidden sugar. He snaps a photo.
2.  **Rising Action:** The agent analyzes the image. "Looks like a chicken curry with rice. I've estimated 1 cup of rice."
3.  **Climax:** Robert knows it's actually cauliflower rice. He taps the microphone: "Actually, that's cauliflower rice, and the sauce has added palm sugar."
4.  **Resolution:** The agent immediately corrects itself. "Understood. Updating to cauliflower rice and adding the sugar note. Thanks for the detail, Robert." Robert checks the log: "Carbs: 12g". He nods, satisfied. The system respected his correction.

### Journey 3: Dr. Chen's "Longitudinal Insight" (Secondary User)
**The Character:** Dr. Chen, Geriatrician.
**The Challenge:** She has 15 minutes per patient. She can't read 3 months of food diaries. She needs patterns.
**The Journey:**
1.  **Opening Scene:** Dr. Chen opens Martha's file before her appointment. She dreads seeing a blank log or a messy handwritten note.
2.  **Rising Action:** She logs into the Clinician Dashboard. She doesn't see a list of meals. She sees a trend line: "Protein Intake vs. Energy Levels".
3.  **Climax:** The system highlights a pattern: "Martha skips lunch 40% of the time on weekends."
4.  **Resolution:** When Martha walks in, Dr. Chen doesn't ask "What did you eat?". She asks, "Martha, tell me about your weekends. Are you finding it hard to cook then?" They have a meaningful conversation about care, driven by data.

### Journey 4: Sarah's "System Oversight" (Admin/Support User)
**The Character:** Sarah, Product Support Specialist.
**The Challenge:** A user reports that the agent "didn't understand" their regional dish.
**The Journey:**
1.  **Opening Scene:** Sarah sees a flagged interaction in the admin panel: "Low Confidence Resolution".
2.  **Rising Action:** She reviews the transcript. The user said "I had a knish," and the agent asked "Is that a type of fish?".
3.  **Climax:** Sarah tags the interaction for the engineering team to improve the "Regional Cuisine" knowledge base. She manually corrects the log for the user.
4.  **Resolution:** She sends a quick note to the user: "Sorry about the mix-up! We've taught the system what a knish is now." The user feels heard and sees the product improving.

### Journey Requirements Summary

These journeys reveal specific capability requirements:
-   **Proactive Engagement:** The system must be able to initiate contact (Push Notifications/SMS) based on time/logic (Martha's journey).
-   **Correction Handling:** The agent must accept user corrections as the "source of truth" and update structured data accordingly (Robert's journey).
-   **Data Aggregation:** The backend must support querying longitudinal trends, not just individual log retrieval (Dr. Chen's journey).
-   **Admin Oversight:** A "Human-in-the-Loop" review interface is needed for flagged/low-confidence interactions (Sarah's journey).

## Domain-Specific Requirements

### Healthcare Compliance & Regulatory Overview
Snap and Say is classified as a **General Wellness Tool (Class I Exempt)**. It is designed to facilitate data logging and visualization but strictly avoids providing medical diagnoses, treatment recommendations, or dosage adjustments. The system acts as a descriptive tool, not a prescriptive one.

### Key Domain Concerns
-   **FDA/SaMD Status:** Must remain a "Wellness Tool" by avoiding medical advice.
-   **Clinical Validation:** Trust is established via statistical accuracy against Weighed Food Records (WFR), not just user sentiment.
-   **HIPAA/Privacy:** Data is treated as PHI. De-identification (User IDs) is the primary protection mechanism for this Research MVP.
-   **Patient Safety:** AI hallucinations or "medical advice" are critical failure modes.
-   **Liability:** Clear disclaimers and "Research Prototype" labeling are mandatory.

### Compliance Requirements
-   **De-identification:** No PII (names, emails) stored in the cloud. Users identified by random codes (e.g., `User_8821`) mapped locally.
-   **Disclaimers:** Login and main screens must state: "Research Prototype. Not medical advice. Estimates may contain errors."
-   **Guardrails:** System prompts must explicitly forbid medical advice (insulin dosing, symptom interpretation).

### Industry Standards & Best Practices
-   **Gold Standard:** Weighed Food Records (WFR).
-   **Data Privacy:** Minimization of data collection (only what is needed for the study).
-   **Transparency:** Clear distinction between "AI Estimate" and "Verified Data".

### Required Expertise & Validation
-   **Validation Study:** A technical accuracy study comparing AI output against 20 ground-truth weighed meals.
-   **Metric:** Error rate calculation (e.g., % of meals within 10% of true weight).

### Implementation Considerations
-   **System Prompt Engineering:** Critical for safety guardrails.
-   **UI/UX:** "Beta" labeling and prominent disclaimers.
-   **Data Architecture:** Separation of PII (local) and PHI (cloud/anonymized).

### Clinical Requirements & Validation Methodology
**Validation Protocol:**
1.  **Ground Truth:** Researcher creates 20 test meals, weighing every ingredient (e.g., "150g rice, 100g chicken").
2.  **Test:** Meals are photographed and described to Snap and Say.
3.  **Comparison:** Export SQL data and compare to weighed logs.
4.  **Success Metric:** > 85% of meals within 10% of true weight.

### Regulatory Pathway
-   **Classification:** Class I Exempt (General Wellness Policy).
-   **Justification:** The software performs functions (logging, organizing) that do not involve medical decision-making.
-   **Constraint:** The Agent must be **descriptive** ("You ate 45g carbs"), NEVER **prescriptive** ("That's too much, take 2 units").

### Safety Measures
-   **Refusal Guardrail:** If a user asks for medical advice (e.g., "Should I double my dose?"), the agent MUST reply: "I cannot give medical advice. Please contact your provider."
-   **System Prompt:** "You are a dietary logger, NOT a doctor. NEVER give advice on medication, insulin dosage, or medical symptoms."

## Innovation & Novel Patterns

### Detected Innovation Areas
-   **Probabilistic "Silence" (The Dietitian Detective):** Unlike standard chatbots that follow rigid decision trees ("If slot=empty, ask"), this agent uses **Chain-of-Thought (CoT)** and **World Knowledge** to infer details. It analyzes context (Time: 7 AM + Visual: Dark Liquid -> Coffee) to make high-confidence guesses, knowing when *not* to ask.
-   **Adaptive Memory:** The system learns user habits over time (e.g., "User_8821 always puts butter on toast"). This creates a "flywheel of fidelity" where the app gets quieter and smarter the longer you use it.
-   **Behavioral Context Vectors:** Beyond calories, the MVP captures the *conditions* of eating (Time, Location, Social Context, Voice Sentiment). This lays the groundwork for a future "Behavioral Digital Twin" without requiring complex physiology modeling today.
-   **Inversion of the Data Burden:** Shifting the workload from the human (measuring, typing) to the computer (seeing, reasoning, structuring).

### Market Context & Competitive Landscape
-   **Current State:** Most dietary apps are "Passive Form-Fillers" requiring users to act as data entry clerks. High friction leads to abandonment.
-   **Snap and Say:** Acts as an "Active Reasoning Agent." It turns unstructured life (messy photos) into structured science (SQL) with minimal user effort.

### Validation Approach
-   **Metric:** **Intervention Rate (IR)**. The average number of clarifying questions asked per logged meal.
-   **Target:** IR < 0.5 (asking a question only once every two meals).
-   **Longitudinal Success:** The IR should trend downward over time as **Adaptive Memory** kicks in.

### Risk Mitigation
-   **Risk:** The Agent infers incorrectly (e.g., logs Coffee instead of Cola).
-   **Mitigation:** **Confidence Thresholds**. The agent only "silently" logs if confidence > 0.85. Otherwise, it triggers a clarification.
-   **Risk:** User annoyance from repetitive questions.
-   **Mitigation:** The "Memory Check" step in the agent chain ensures it never asks about established habits (e.g., "Butter or Jam?").

## Web App (PWA) Specific Requirements

### Project-Type Overview
Snap and Say will be built as a **Next.js (React)** application using the **App Router**. It adopts a **Hybrid Architecture**: Server-Side Rendering (SSR) for public marketing pages to ensure SEO, and Client-Side Rendering (CSR) for the private application to deliver a fluid, native-app-like experience.

### Technical Architecture Considerations
-   **Framework:** Next.js with App Router.
-   **Real-Time Strategy:** **Server-Sent Events (SSE)** for streaming agent responses (the "thinking" effect). Avoids WebSocket complexity while maintaining user engagement.
-   **Browser Support:** Targeted at **Modern Mobile Browsers** (iOS Safari 15+, Chrome Android 100+) to leverage the **MediaRecorder API**. Legacy browsers will receive a "please upgrade" message rather than polyfills.

### Implementation Considerations
-   **Accessibility (Senior-Focused):**
    -   **Contrast:** Target **AAA (7:1)** for text legibility (e.g., almost black on off-white).
    -   **Touch Targets:** Minimum **60x60px** for primary actions (exceeding the 48px standard).
    -   **Dynamic Type:** Layouts must adapt to system font size settings without breaking.
-   **SEO Strategy:**
    -   **Public:** Semantic HTML (`<article>`, `<h1>`) for marketing pages.
    -   **Private:** `robots.txt` disallow for `/app` routes to protect patient privacy.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** **Problem-Solving MVP (Research Prototype)**. Focus entirely on solving the "Friction-Fidelity Trade-off" for the older adult user.
**Resource Requirements:** Lean Team (1 Full-Stack Engineer for App/Agent, 1 Researcher for Validation/SQL Analysis).

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
-   **Martha (The Gentle Nudge):** Frictionless logging via voice/photo.
-   **Robert (Precision Control):** User correction of agent assumptions.
-   **Sarah (Admin):** Backend oversight (manual SQL/Admin panel) for fixing errors.

**Must-Have Capabilities:**
-   **Multimodal Input:** Simultaneous Voice + Photo capture (MediaRecorder API).
-   **Agentic Reasoning:** LangGraph backend to process inputs and "silently" infer details.
-   **Structured Storage:** Supabase DB with strict schema for nutritional data.
-   **De-identified Auth:** Simple User ID generation and login.
-   **Basic History:** User can see "Today's Log" (read-only list).

### Post-MVP Features

**Phase 2 (Growth - The Clinician Loop):**
-   **Clinician Dashboard:** Web portal for Dr. Chen to view patient trends.
-   **Longitudinal Visualization:** Graphs for "Protein vs. Energy" over weeks.
-   **Family Sharing:** "Worried Child" view (read-only access).

**Phase 3 (Expansion - The System Loop):**
-   **EHR Integration:** FHIR export to hospital systems.
-   **Digital Twin:** Predictive metabolic modeling based on behavioral vectors.
-   **Voice Hardware:** Integration with smart speakers (Alexa/Google Home).

### Risk Mitigation Strategy

**Technical Risks:**
-   *Risk:* Agent Hallucination (Safety). *Mitigation:* Strict System Prompts + Confidence Thresholds (Silence < 0.85).
-   *Risk:* Latency (User Patience). *Mitigation:* Server-Sent Events (SSE) to stream "thinking" tokens.

**Market Risks:**
-   *Risk:* User Abandonment (Annoyance). *Mitigation:* Track "Intervention Rate" (IR). If IR > 0.5, tune agent to be less inquisitive.

**Resource Risks:**
-   *Risk:* Backend complexity explodes. *Mitigation:* Cut "Clinician Dashboard" from MVP (Researcher queries SQL directly).

## Functional Requirements

### 1. Authentication & Identity
-   **FR1:** Users can log in using a simple, anonymized User ID (no email/password).
-   **FR2:** The system can generate unique, random User IDs for new participants.
-   **FR3:** Users remain logged in across sessions (persistent session) to minimize friction.

### 2. Multimodal Ingestion
-   **FR4:** Users can capture a photo of their meal directly within the application.
-   **FR5:** Users can record a voice note describing their meal.
-   **FR6:** Users can provide text input to describe a meal or add details.
-   **FR7:** Users can provide combined inputs (e.g., Photo + Voice) for a single entry.

### 3. Agentic Processing & Interaction
-   **FR8:** The system can analyze inputs to identify food items, quantities, and preparation methods.
-   **FR9:** The system can infer missing details based on context without asking the user (Probabilistic Silence).
-   **FR10:** The system can request clarification from the user *only* when confidence is below a defined threshold.
-   **FR11:** The system can stream "thinking" indicators to the user during processing to maintain engagement.
-   **FR12:** The system prevents the generation of medical advice or clinical diagnoses (Refusal Guardrails).

### 4. Dietary Log Management
-   **FR13:** Users can view a list of their logged meals for the current day.
-   **FR14:** Users can edit the details of a logged meal (e.g., change portion size, correct food item).
-   **FR15:** Users can delete a logged meal entry.
-   **FR16:** Users can view the nutritional breakdown (e.g., calories, protein) of a logged meal.

### 5. Admin & Research Oversight
-   **FR17:** Admins (Researchers) can view all de-identified user logs.
-   **FR18:** Admins can manually correct or override agent-generated data.
-   **FR19:** Admins can export structured dietary data (CSV/JSON) for analysis.

## Non-Functional Requirements

### Accessibility (Critical - Senior First)
-   **NFR1 (Contrast):** All text must meet **WCAG AAA (7:1)** contrast ratios to ensure legibility for aging eyes.
-   **NFR2 (Touch Targets):** All interactive elements must have a minimum touch target of **60x60px**.
-   **NFR3 (Font Scaling):** The interface must remain functional and unbroken when the system font size is increased by up to **200%**.

### Security & Privacy (HIPAA Context)
-   **NFR4 (De-identification):** No PII (names, emails) shall be stored in the central database; users are identified solely by random UUIDs.
-   **NFR5 (Data Minimization):** Voice recordings must be processed for transcription and then immediately deleted (or strictly access-controlled if required for research validation).
-   **NFR6 (Encryption):** All data must be encrypted at rest (AES-256) and in transit (TLS 1.3).

### Performance (User Engagement)
-   **NFR7 (Perceived Latency):** The "Thinking" state (streaming tokens) must initiate within **1.5 seconds** of input completion to prevent user abandonment.
-   **NFR8 (Cold Start):** The application (PWA) must load and be interactive within **3 seconds** on a 4G network.

### Reliability
-   **NFR9 (Offline Grace):** If the network is lost, the app must allow the user to complete the current log and queue it for sync, rather than showing an error.
