---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/ux-design-specification.md'
workflowType: 'epics-and-stories'
project_name: 'snapandsay'
user_name: 'Fabian'
date: '2026-02-16'
---

# Epics & Stories: Snap and Say

**Author:** Fabian (PM Agent)
**Date:** 2025-12-04 (Updated: 2026-02-16)
**Scope Update:** Epic 7 added for Structured Complexity Score Addendum

---

## Overview

This document provides the complete epic and story breakdown for {{project_name}}, decomposing the requirements from the [PRD](./PRD.md) into implementable stories.

**Living Document Notice:** This is the initial version. It will be updated after UX Design and Architecture workflows add interaction and technical details to stories.

### Executive Summary

The **Snap and Say** project is a high-complexity healthcare web application designed to solve the "Friction-Fidelity Trade-off" for older adults. This document outlines the decomposition of the Product Requirements Document (PRD) into actionable Epics and User Stories, leveraging the technical decisions from the Architecture document and the interaction patterns from the UX Design specification.

**Key Context:**
- **Product Vision:** Agentic AI for zero-friction dietary logging.
- **Target Audience:** Seniors (65+) managing chronic conditions.
- **Technical Stack:** Next.js (Frontend), FastAPI (Backend), LangGraph (Agent), Supabase (DB/Auth).
- **UX Core:** Voice-first, "Snap & Say" interaction model with "Probabilistic Silence".

This breakdown focuses on the **Research MVP** scope, prioritizing the core logging loop, data accuracy, and accessibility.

---

## Functional Requirements Inventory

### 1. Authentication & Identity
- **FR1:** Users can log in using a simple, anonymized User ID (no email/password).
- **FR2:** The system can generate unique, random User IDs for new participants.
- **FR3:** Users remain logged in across sessions (persistent session) to minimize friction.

### 2. Multimodal Ingestion
- **FR4:** Users can capture a photo of their meal directly within the application.
- **FR5:** Users can record a voice note describing their meal.
- **FR6:** Users can provide text input to describe a meal or add details.
- **FR7:** Users can provide combined inputs (e.g., Photo + Voice) for a single entry.

### 3. Agentic Processing & Interaction
- **FR8:** The system can analyze inputs to identify food items, quantities, and preparation methods.
- **FR9:** The system can infer missing details based on context without asking the user (Probabilistic Silence).
- **FR10:** The system can request clarification from the user *only* when confidence is below a defined threshold.
- **FR11:** The system can stream "thinking" indicators to the user during processing to maintain engagement.
- **FR12:** The system prevents the generation of medical advice or clinical diagnoses (Refusal Guardrails).

### 4. Dietary Log Management
- **FR13:** Users can view a list of their logged meals for the current day.
- **FR14:** Users can edit the details of a logged meal (e.g., change portion size, correct food item).
- **FR15:** Users can delete a logged meal entry.
- **FR16:** Users can view the nutritional breakdown (e.g., calories, protein) of a logged meal.

### 5. Admin & Research Oversight
- **FR17:** Admins (Researchers) can view all de-identified user logs.
- **FR18:** Admins can manually correct or override agent-generated data.
- **FR19:** Admins can export structured dietary data (CSV/JSON) for analysis.

---

## FR Coverage Map

| Epic | Title | FR Coverage |
| :--- | :--- | :--- |
| **1** | **Foundation & Core Infrastructure** | FR1, FR2, FR3 (Auth & Identity) |
| **2** | **Multimodal Ingestion & Capture** | FR4, FR5, FR6, FR7 (Ingestion) |
| **3** | **Agentic Analysis & Logging** | FR8, FR9, FR10, FR11, FR12 (Agentic Processing) |
| **4** | **Dietary Log Management & History** | FR13, FR14, FR15, FR16 (Log Management) |
| **5** | **Admin Oversight & Data Export** | FR17, FR18, FR19 (Admin) |
| **7** | **Structured Complexity Scoring & Targeted Clarification** | FR8↑, FR9↑, FR10↑ (Enhanced Agentic Processing) |

---

## Epic 1: Foundation & Core Infrastructure

**Goal:** Establish the technical groundwork for the PWA, Backend, and Database to support secure, de-identified user access.
**User Value:** Users can access a secure, performant application foundation that respects their privacy.
**PRD Coverage:** FR1, FR2, FR3
**Technical Context:** Next.js setup, FastAPI setup, Supabase Auth (Anon), DB Schema (Users table).
**Dependencies:** None.

<!-- Stories for Epic 1 -->
### Story 1.1: Project Initialization & Repo Setup

As a developer,
I want to initialize the project repository with the correct structure and dependencies,
So that the team can start building on a solid foundation.

**Acceptance Criteria:**
**Given** I have the necessary permissions
**When** I initialize the repository
**Then** The project structure matches the Architecture definition (frontend/backend separation)
**And** The `vintasoftware/nextjs-fastapi-template` is cloned and cleaned of unused boilerplate
**And** CI/CD workflows are configured for linting (ESLint, Ruff)

**Technical Notes:**
- Clone `vintasoftware/nextjs-fastapi-template`.
- Remove unused template files.
- Create directory structure: `frontend/src/app`, `backend/app`, `supabase/migrations`.
- Configure `ruff` for Python and `eslint` for Next.js.

### Story 1.2: Database & Supabase Configuration

As a developer,
I want to set up the Supabase project and database schema,
So that we can store user data securely.

**Acceptance Criteria:**
**Given** A Supabase project is created
**When** I run the migration scripts
**Then** The `users` table exists with `id` (UUID), `anonymous_id` (String), and `created_at`
**And** The `pgvector` extension is enabled
**And** RLS policies are set to allow access only to the owning user

**Technical Notes:**
- Create `supabase/migrations/0000_init.sql`.
- Enable `vector` extension.
- Define `users` table.
- Define `dietary_logs` table with fields: `id`, `user_id`, `image_url`, `audio_url`, `transcript`, `analysis_result` (JSONB), `status`, `created_at`.
- Set up RLS policies for `users` and `dietary_logs` tables.

### Story 1.3: Authentication Foundation (Anonymous)

As a user,
I want to use the app without creating an account (Anonymous Login),
So that I can start logging immediately without friction.

**Acceptance Criteria:**
**Given** I am a new user opening the app
**When** The app loads
**Then** I am automatically signed in anonymously via Supabase Auth
**And** A unique User ID is generated and stored
**And** My session persists across reloads

**Technical Notes:**
- Frontend: `lib/supabase.ts` calls `supabase.auth.signInAnonymously()`.
- Backend: `core/security.py` middleware verifies the JWT token from the request header.
- Ensure `middleware.ts` in Next.js protects `/app` routes.

---

## Epic 2: Multimodal Ingestion & Capture

**Goal:** Enable users to capture meals via Photo and Voice with a senior-friendly UI.
**User Value:** Users can easily capture their meals without typing, using a familiar "Show and Tell" metaphor.
**PRD Coverage:** FR4, FR5, FR6, FR7
**Technical Context:** MediaRecorder API, VoiceCaptureButton, Camera integration, Supabase Storage (Raw uploads).
**UX Integration:** "Snap & Say" flow, "Thinking" states, Large touch targets.
**Dependencies:** Epic 1.

<!-- Stories for Epic 2 -->
### Story 2.1: Camera Capture Component

As a user,
I want to take a photo of my meal with a simple, large interface,
So that I can visually log what I'm eating.

**Acceptance Criteria:**
**Given** I am on the "Snap" page
**When** I tap the large shutter button
**Then** The camera captures an image
**And** The image is displayed in a preview
**And** I receive haptic feedback (if supported)

**UX Integration:**
- Large 60px+ shutter button.
- Full-screen viewfinder.
- High contrast icons.

**Technical Notes:**
- Use `react-webcam` or native Media API.
- Component: `components/features/camera/CameraCapture.tsx`.
- Ensure mobile responsiveness.

### Story 2.2: Voice Recorder Component

As a user,
I want to record a voice note by holding a button,
So that I can describe my meal naturally.

**Acceptance Criteria:**
**Given** I have captured a photo (or just opened the app)
**When** I press and hold the "Mic" button
**Then** The app starts recording audio
**And** A visual "pulsing" animation indicates recording
**When** I release the button
**Then** Recording stops and the audio blob is ready for upload

**UX Integration:**
- "Hold to Record" pattern (WhatsApp style).
- Visual feedback (Pulse).
- Haptic feedback on start/stop.

**Technical Notes:**
- Use `MediaRecorder` API.
- Component: `components/features/voice/VoiceCaptureButton.tsx`.
- Hook: `hooks/use-audio.ts`.

### Story 2.4: Text-Only Meal Entry

As a user,
I want to type my meal description if I can't speak or take a photo,
So that I can still log my food in quiet environments.

**Acceptance Criteria:**
**Given** I am on the dashboard or snap page
**When** I tap the "Text Input" button
**Then** A text input field appears
**When** I type a description and submit
**Then** The entry is created and processed just like a voice note

**UX Integration:**
- Discrete "Keyboard" icon near the Mic button.
- Transitions to the same "Thinking" state.

**Technical Notes:**
- Reuses the `analyze_input` pipeline (skipping Whisper transcription).
- Backend accepts text-only payload.

### Story 2.3: Combined Capture & Upload Service

As a user,
I want my photo and voice note to be uploaded securely,
So that the AI can analyze them.

**Acceptance Criteria:**
**Given** I have a photo and/or voice note
**When** The capture is complete
**Then** The files are uploaded to Supabase Storage (`raw_uploads` bucket)
**And** A "Draft" log entry is created in the backend
**And** I see a "Thinking" state in the UI

**Technical Notes:**
- Frontend: Upload to Supabase Storage using `supabase-js`.
- Backend: `POST /api/v1/analysis/upload` endpoint to receive file paths/metadata.
- Create `dietary_logs` table entry with status "processing".

---

## Epic 3: Agentic Analysis & Logging

**Goal:** Implement the AI agent to process inputs, reason about food, and generate structured logs.
**User Value:** Users get accurate food logs without manual entry, and the system intelligently infers details to reduce questions.
**PRD Coverage:** FR8, FR9, FR10, FR11, FR12
**Technical Context:** LangGraph Agent, OpenAI/LLM integration, SSE Streaming, Pydantic validation.
**UX Integration:** "Probabilistic Silence", "Thinking" feedback animation.
**Dependencies:** Epic 2.

<!-- Stories for Epic 3 -->
### Story 3.1: LangGraph Agent Setup

As a developer,
I want to initialize the LangGraph orchestration layer,
So that we can manage the complex reasoning loop of the AI.

**Acceptance Criteria:**
**Given** The backend is running
**When** The agent is invoked
**Then** It initializes a `StateGraph` with the correct `AgentState`
**And** It can transition between nodes (Reasoning -> Clarification -> Final)

**Technical Notes:**
- File: `app/agent/graph.py`.
- State: `messages` (list), `image_url` (str), `nutritional_data` (dict).
- Define basic nodes: `analyze_input`, `generate_clarification`, `finalize_log`.

### Story 3.2: Vision & Audio Analysis Node

As a user,
I want the AI to analyze my photo and voice note,
So that it can identify the food items.

**Acceptance Criteria:**
**Given** An image and audio file are uploaded
**When** The `analyze_input` node runs
**Then** The audio is transcribed (Whisper)
**And** The image + transcript are sent to GPT-4o
**And** The LLM extracts food items, quantities, and confidence scores

**Technical Notes:**
- Service: `app/services/llm_service.py`.
- Service: `app/services/voice_service.py` (Whisper integration).
- Prompt Engineering: System prompt to act as a dietary expert.
- **Guardrails:** Include specific instructions to refuse medical advice requests (e.g., "I cannot provide medical advice. Please consult your doctor.").
- **Test Case:** Verify that inputs like "What should I eat for my diabetes?" trigger the refusal message.

### Story 3.3: Streaming Response Implementation (SSE)

As a user,
I want to see "thinking" indicators while the AI processes,
So that I know the app hasn't frozen.

**Acceptance Criteria:**
**Given** The agent is processing
**When** It moves between steps or generates tokens
**Then** The UI receives Server-Sent Events (SSE)
**And** The UI displays a "Thinking..." animation or text stream

**Technical Notes:**
- Backend: `FastAPI` SSE response generator.
- Frontend: `hooks/use-agent.ts` with `EventSource`.
- Events: `agent.thought`, `agent.response`.

### Story 3.4: Clarification Logic (Probabilistic Silence)

As a user,
I want the AI to only ask me questions when it's unsure,
So that I'm not annoyed by obvious questions.

**Acceptance Criteria:**
**Given** The AI has analyzed the input
**When** The confidence score is > 0.85
**Then** It automatically logs the meal (Silence)
**When** The confidence score is < 0.85
**Then** It generates a clarification question (e.g., "What kind of dressing?")

**Technical Notes:**
- LangGraph Conditional Edge: Check confidence score in `AgentState`.
- If high confidence -> Go to `finalize_log`.
- If low confidence -> Go to `generate_clarification`.

### Story 3.5: Snap Page Streaming UI Integration

As a user,
I want to see real-time thinking indicators and clarification prompts on the Snap page,
So that I understand what the AI is doing and can answer questions when needed.

**Acceptance Criteria:**
**Given** I have captured a photo and voice note
**When** The upload completes and analysis begins
**Then** The "Analyzing..." overlay shows real-time agent thoughts (via SSE)
**And** If the agent needs clarification, the ClarificationPrompt component appears
**And** When I respond, the agent continues processing with my answer
**And** On completion, I am navigated to the dashboard

**UX Integration:**
- `ThinkingIndicator` component for streaming thoughts.
- `ClarificationPrompt` component for questions.
- Timeout with graceful skip option.
- Progress bar during processing.

**Technical Notes:**
- File: `app/(dashboard)/snap/page.tsx`.
- Import `useStreamingAnalysis` hook from Epic 3 SSE work.
- Import `ClarificationPrompt` and `ThinkingIndicator` components.
- Add `'streaming'` step to page state machine.
- Handle SSE events: `agent.thought`, `agent.clarification`, `agent.response`.

---

## Epic 4: Dietary Log Management & History

**Goal:** Allow users to view and manage their daily food logs.
**User Value:** Users can review their day, feel in control of their data, and correct any mistakes easily.
**PRD Coverage:** FR13, FR14, FR15, FR16
**Technical Context:** Log CRUD endpoints, FoodEntryCard, DailySummary.
**UX Integration:** "No-Edit" default, "Voice as Eraser" correction flow.
**Dependencies:** Epic 3.

<!-- Stories for Epic 4 -->
### Story 4.1: Daily Log List UI

As a user,
I want to see a list of my meals for today,
So that I can keep track of my eating.

**Acceptance Criteria:**
**Given** I have logged meals
**When** I view the dashboard
**Then** I see a list of `FoodEntryCard`s for today
**And** Each card shows the photo, description, and calorie count
**When** I tap a card
**Then** I see the full nutritional breakdown (Protein, Carbs, Fat)

**UX Integration:**
- `FoodEntryCard` component.
- "No-Edit" default state.
- Optimistic UI updates.

**Technical Notes:**
- Endpoint: `GET /api/v1/logs?date={today}`.
- Frontend: `useQuery` to fetch logs.

### Story 4.2: Edit & Delete Log

As a user,
I want to edit or delete a log entry,
So that I can correct mistakes.

**Acceptance Criteria:**
**Given** A logged meal
**When** I tap "Edit"
**Then** I can update the description or quantities
**When** I tap "Delete"
**Then** The entry is removed from my list

**UX Integration:**
- "Voice as Eraser" (optional for MVP, text edit mandatory).
- Confirmation dialog for delete.

**Technical Notes:**
- Endpoints: `PUT /api/v1/logs/{id}`, `DELETE /api/v1/logs/{id}`.
- Update DB and invalidate React Query cache.

---

## Epic 5: Admin Oversight & Data Export

**Goal:** Provide researchers with tools to monitor data quality and export results.
**User Value:** Researchers can validate the study and access structured data for analysis.
**PRD Coverage:** FR17, FR18, FR19
**Technical Context:** Admin Dashboard (simple), CSV/JSON export endpoints.
**Dependencies:** Epic 4.

<!-- Stories for Epic 5 -->
### Story 5.1: Admin Dashboard View

As a researcher (Admin),
I want to view all user logs in a table,
So that I can monitor the study progress.

**Acceptance Criteria:**
**Given** I am logged in as an Admin
**When** I visit the `/admin` route
**Then** I see a table of all de-identified logs
**And** I can filter by User ID or Date

**Technical Notes:**
- Protected route (Admin role check).
- Simple table component (Shadcn Table).
- **Manual Correction:** Add an "Edit" button for admins to override the JSONB data directly or via a form.

### Story 5.2: Data Export

As a researcher,
I want to export the dietary data as a CSV,
So that I can perform statistical analysis.

**Acceptance Criteria:**
**Given** I am on the Admin Dashboard
**When** I click "Export CSV"
**Then** A CSV file is downloaded containing all structured log data

**Technical Notes:**
- Endpoint: `GET /api/v1/admin/export`.
- Generate CSV from `dietary_logs` table.

---

## FR Coverage Matrix

{{fr_coverage_matrix}}

---

## Summary

{{epic_breakdown_summary}}

---

_For implementation: Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown._

_This document will be updated after UX Design and Architecture workflows to incorporate interaction details and technical decisions._

## Epic 6: Deployment & Hardening

**Goal:** Prepare the application for production release, establish CI/CD pipelines, and ensure system stability.
**User Value:** Users can access the application in a reliable, production-grade environment.
**PRD Coverage:** Non-Functional Requirements (Deployment, Stability).
**Technical Context:** Vercel (Frontend), Railway (Backend), Supabase (Prod Project).
**Dependencies:** Epic 5.

### Story 6.1: Production Deployment Pipeline

As a developer,
I want to set up the production deployment pipeline,
So that code changes are automatically deployed to the production environment.

**Acceptance Criteria:**
**Given** Code is merged to `main`
**Then** The frontend is deployed to Vercel (Production)
**And** The backend is deployed to Railway
**And** Database migrations are applied
**And** Environment variables are correctly configured in both environments

**Technical Notes:**
- Frontend: Configure `vercel.json` if needed, set up Vercel Project.
- Backend: Configure `nixpacks.toml` or `Dockerfile` for Railway, set up Railway Project.
- Monorepo handling: Ensure independent builds.

---

## Epic 7: Structured Complexity Scoring & Targeted Clarification

**Goal:** Ensure the system asks the *right* kind of clarification question (Ingredient, Prep, or Portion) based on a transparent, clinically-grounded scoring formula.
**User Value:** Users receive fewer, smarter clarification questions that target the specific dimension of ambiguity (ingredients, prep, or portion). Clinically sensitive users (e.g., diabetic) get appropriately thorough probing. Researchers gain transparent reasoning traces for every complexity decision.
**PRD Coverage:** FR8 (enhanced), FR9 (enhanced), FR10 (enhanced)
**Architecture Decisions:** D1–D8 from Structured Complexity Score Addendum (2026-02-16)
**Dependencies:** Epic 3 (Agentic Analysis & Logging).

### Story 7.1: Structured Ambiguity Analysis (Phase 1)

As a system,
I want to assess ambiguity across three specific dimensions (Hidden Ingredients, Invisible Prep, Portion Size) using a 0-3 scale,
So that I can identify exactly *why* a meal is complex.

**Acceptance Criteria:**

**Given** an analyzed food item
**When** the agent performs its assessment
**Then** it assigns a score (0-3) for:
  - `hidden_ingredients` (e.g., 3 for "Curry", 0 for "Apple")
  - `invisible_prep` (e.g., 2 for "Deep Fried", 0 for "Raw")
  - `portion_size` (e.g., 3 for "Plate", 0 for "1 cup")
**And** these scores are grounded in the specific definitions from the Architecture
**And** the system supports fallback to a default score if structured analysis fails

**Technical Notes:**
- Update `AnalysisResult` schema to include `AmbiguityLevels`.
- Update prompt to request these specific fields.

### Story 7.2: Specialized Food Class Registry

As a system,
I want to recognize specific classes of food (e.g., "Sandwich", "Soup") and apply pre-defined risk profiles,
So that I don't treat a high-risk "Burrito" the same as a low-risk "Salad" when deciding to ask questions.

**Acceptance Criteria:**

**Given** a food item is identified
**When** I consult the Food Class Registry
**Then** I retrieve specific "Biomimicry Risk" weights for that class
**And** if the item is an "Umbrella Term" (like "Sandwich"), I flag it for immediate clarification
**And** unknown foods fall back to a default "Moderate Risk" profile

**Technical Notes:**
- Implement `FoodClassRegistry` (YAML-based).
- Support lookup by name/alias.

### Story 7.3: Semantic Gatekeeper

As a user,
I want the system to ask me "What kind of sandwich?" *before* asking about ingredients,
So that the conversation feels natural and logical.

**Acceptance Criteria:**

**Given** I have logged a generic item (e.g., "Sandwich")
**When** the system analyzes it
**Then** the Gatekeeper detects it is an "Umbrella Term"
**And** the system asks a "Type" clarification question first (Semantic Interruption)
**And** the system does *not* try to guess ingredients until I answer

**Technical Notes:**
- Implement Gatekeeper logic in Phase 1 of the pipeline.
- Trigger "Targeted Clarification" for unbounded terms.

### Story 7.4: Deterministic Complexity Scoring

As a researcher,
I want the complexity score to be calculated using the transparent formula `C = Σ(w · L²) + P`,
So that I can audit exactly why a specific meal triggered a clarification.

**Acceptance Criteria:**

**Given** the ambiguity levels and class weights
**When** the score is calculated
**Then** the result follows the formula `(w_i · L_i²) + (w_p · L_p²) + (w_v · L_v²) + P_sem`
**And** the "Dominant Factor" (the dimension contributing the most to the score) is identified
**And** the final score is stored in the log

**Technical Notes:**
- Implement `ComplexityCalculator`.
- Ensure backward compatibility with existing float scores.

### Story 7.5: Clinical Threshold Routing

As a user with a specific condition (e.g., Diabetes),
I want the system to be more thorough when checking for hidden ingredients,
So that I don't miss something that affects my health.

**Acceptance Criteria:**

**Given** my user profile has a clinical condition (e.g., "Diabetes")
**When** the system decides whether to ask a question
**Then** it uses a lower threshold (e.g., 5.0) than for a general user (e.g., 15.0)
**And** if the Complexity Score exceeds this threshold, I am asked a clarification
**And** the clarification question targets the "Dominant Factor" (e.g., "Does the sauce contain sugar?" if Ingredients was the driver)

**Technical Notes:**
- Update `Router` to check `clinical_threshold`.
- Pass `dominant_factor` to the Question Generator.

### Story 7.6: Targeted Question Generation

As a user,
I want clarification questions to be specific to the uncertainty,
So that I can answer quickly with one word.

**Acceptance Criteria:**

**Given** a high `prep` ambiguity score
**When** the system asks a question
**Then** it asks about preparation (e.g., "Was this fried or grilled?") rather than a generic "Tell me more".

**Given** a high `portion` ambiguity score
**When** the system asks a question
**Then** it asks about size (e.g., "Was that a cup or a bowl?")

**Technical Notes:**
- Update `AMPM` nodes to use `dominant_factor` for prompt templating.

### Story 7.7: Verification & Auditing (Benchmarking)

As a researcher,
I want to verify that the new scoring system improves accuracy without annoying users,
So that I can trust the clinical validity.

**Acceptance Criteria:**

**Given** a set of test meals (Gold Standard)
**When** the benchmark is run
**Then** I can see the calculated Complexity Score for each
**And** I can see which dimension triggered the clarification
**And** I can compare the new scores against the old opaque scores

**Technical Notes:**
- Update benchmark tools to log the full `ComplexityBreakdown`.
