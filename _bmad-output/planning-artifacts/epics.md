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
- Set up RLS policies for `users` table.

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

**Goal:** Replace the opaque LLM-derived complexity float with a transparent, clinically-grounded scoring formula that enables targeted clarification questions and clinical adaptability.
**User Value:** Users receive fewer, smarter clarification questions that target the specific dimension of ambiguity (ingredients, prep, or portion). Clinically sensitive users (e.g., diabetic) get appropriately thorough probing. Researchers gain transparent reasoning traces for every complexity decision.
**PRD Coverage:** FR8 (enhanced), FR9 (enhanced), FR10 (enhanced)
**Architecture Decisions:** D1–D8 from Structured Complexity Score Addendum (2026-02-16)
**Dependencies:** Epic 3 (Agentic Analysis & Logging).

### Story 7.1: Complexity Schema & Data Foundation

As a developer,
I want to define the Pydantic models and AgentState fields for structured complexity scoring,
So that the system has a typed schema for ambiguity levels, complexity breakdowns, and clinical thresholds.

**Acceptance Criteria:**

**Given** the existing `AnalysisResult` model in `schemas/analysis.py`
**When** the schema update is applied
**Then** a new `AmbiguityLevels` Pydantic model exists with three `int` fields (`hidden_ingredients`, `invisible_prep`, `portion_ambiguity`), each constrained to range 0–3
**And** a new `ComplexityBreakdown` Pydantic model exists with fields: `levels` (AmbiguityLevels), `weights` (dict[str, float]), `semantic_penalty` (float), `dominant_factor` (str), `score` (float)
**And** the existing `AnalysisResult.complexity_score` float field is retained for backward compatibility
**And** `AnalysisResult` gains optional fields `ambiguity_levels: AmbiguityLevels | None` and `complexity_breakdown: ComplexityBreakdown | None`

**Given** the existing `AgentState` in `agent/state.py`
**When** the state update is applied
**Then** `AgentState` gains three new fields: `complexity_breakdown: dict | None`, `clinical_threshold: float`, `mandatory_clarification: bool`
**And** the existing `complexity_score: float` field is retained

**Given** `agent/constants.py`
**When** clinical threshold constants are added
**Then** a `CLINICAL_THRESHOLDS` dict exists mapping profile names to threshold values: `{"general": 15.0, "diabetes": 5.0, "renal": 8.0, "cardiac": 7.0}`
**And** a `DEFAULT_CLINICAL_PROFILE` constant is set to `"general"`

**Technical Notes:**
- Files: `backend/app/schemas/analysis.py`, `backend/app/agent/state.py`, `backend/app/agent/constants.py`
- All new fields must have defaults (None/0.0/False) to avoid breaking existing tests
- Architecture ref: Decisions 4, 5, 7

---

### Story 7.2: Food Class Registry

As a developer,
I want to create a versioned YAML registry of food classes with biomimicry risk weights and umbrella term flags,
So that the Semantic Gatekeeper can perform deterministic lookups instead of relying on LLM judgment for category-level decisions.

**Acceptance Criteria:**

**Given** no registry file exists
**When** the registry is created
**Then** a file `backend/app/agent/data/food_class_registry.yaml` exists with:
  - A `default` entry with moderate weights (`{ingredients: 0.5, prep: 0.5, volume: 0.5}`), `semantic_penalty: 0.0`, `mandatory_clarification: false`, `is_umbrella_term: false`
  - At least 5 food `classes` entries (e.g., `burger`, `sandwich`, `milk`, `pasta`, `curry`) with specific weights, penalties, aliases, and umbrella term flags matching the Architecture addendum

**Given** the registry YAML file
**When** a registry loader service is invoked
**Then** the registry is parsed and cached in memory at application startup
**And** lookup by food name or alias returns the matching class entry (case-insensitive)
**And** lookup for an unknown food name returns the `default` entry
**And** the loader validates the YAML schema on startup and raises a clear error if malformed

**Technical Notes:**
- New files: `backend/app/agent/data/food_class_registry.yaml`, `backend/app/agent/registry.py`
- AI agents MUST NOT hardcode food class weights in Python — always read from registry
- Architecture ref: Decision 3 (Stage 2)

---

### Story 7.3: Semantic Gatekeeper Service

As a developer,
I want to implement a Semantic Gatekeeper that checks food noun specificity before material ambiguity assessment,
So that the system doesn't waste computation analyzing foods it can't even identify yet (e.g., "sandwich" without knowing what kind).

**Acceptance Criteria:**

**Given** an `AnalysisResult` with food items
**When** the gatekeeper performs lexical bounding checks
**Then** food items whose names match `is_umbrella_term: true` entries in the registry are flagged as unbounded
**And** unbounded items produce a list of `UnboundedItem` results with the original name and the registry class

**Given** food items that pass the lexical bounding check (or have been resolved)
**When** the gatekeeper performs registry lookup
**Then** each item receives its food class weights (`w_i`, `w_p`, `w_v`), `semantic_penalty` (`P_sem`), and `mandatory_clarification` flag from the registry
**And** items not found in the registry receive `default` weights

**Given** the gatekeeper identifies unbounded items
**When** the system processes these items in the agent graph
**Then** the agent generates a targeted semantic clarification question (e.g., "What kind of sandwich was it?") before proceeding to the Triangle Audit
**And** the agent does NOT attempt to assess material ambiguity on unbounded items

**Technical Notes:**
- New file: `backend/app/agent/gatekeeper.py`
- The gatekeeper is a pure function (no LLM calls) — deterministic and testable
- This runs as Phase 1 of the 3-phase ordering (Decision 8)
- Architecture ref: Decision 3 (Stage 1 + Stage 2)

---

### Story 7.4: LLM Prompt Update for Structured Level Assessment

As a developer,
I want to update the analysis prompt to request structured ambiguity levels (three integers 0–3) instead of an opaque complexity float,
So that the LLM provides transparent, dimensional assessment data that feeds the complexity formula.

**Acceptance Criteria:**

**Given** the current analysis prompt in `llm_service.py`
**When** the prompt is updated
**Then** the LLM is instructed to output `hidden_ingredients` (0–3), `invisible_prep` (0–3), and `portion_ambiguity` (0–3) as part of the `AnalysisResult`
**And** the prompt includes the scale descriptions from Decision 2 (Container Scale, Catalyst Scale, Spatial Scale) as reference for the LLM
**And** the `complexity_score` float is no longer set directly by the LLM — it is left as default (0.0) for later computation

**Given** the LLM returns structured levels
**When** the response is parsed
**Then** `AnalysisResult.ambiguity_levels` is populated with the three integer levels
**And** each level is validated to be in range 0–3 by Pydantic

**Given** the LLM fails to return structured levels (legacy behavior / parsing error)
**When** fallback is triggered
**Then** `ambiguity_levels` remains `None`
**And** the system falls back to the legacy `complexity_score > 0.7` behavior
**And** a warning is logged indicating structured output failed

**Technical Notes:**
- File: `backend/app/services/llm_service.py`
- The prompt change is the primary interface between the LLM and the new scoring system
- Architecture ref: Decision 4

---

### Story 7.5: Complexity Calculator & 3-Phase Pipeline

As a developer,
I want to implement the complexity formula `C = (w_i · L_i²) + (w_p · L_p²) + (w_v · L_v²) + P_sem` and wire the 3-phase pipeline (Gatekeeper → Calculator → Router),
So that complexity scores are computed deterministically from structured inputs rather than guessed by the LLM.

**Acceptance Criteria:**

**Given** an `AmbiguityLevels` object and weights/penalty from the registry
**When** the complexity calculator is invoked
**Then** it computes `C` using the squared-weighting formula
**And** it identifies the `dominant_factor` as the dimension with the highest `w · L²` contribution
**And** it returns a `ComplexityBreakdown` object with all intermediate values
**And** the `complexity_score` float field on `AnalysisResult` is set to `breakdown.score` for backward compatibility

**Given** ambiguity levels of `L_i=3, L_p=3, L_v=3` with all weights `1.0` and `P_sem=5.0`
**When** computed
**Then** the maximum score is `32.0`

**Given** ambiguity levels of `L_i=0, L_p=0, L_v=0` with default weights and `P_sem=0.0`
**When** computed
**Then** the score is `0.0`

**Given** the 3-phase pipeline in the agent graph
**When** a food analysis completes
**Then** Phase 1 (Semantic Resolution) runs before Phase 2 (Triangle Audit)
**And** Phase 2 runs before Phase 3 (Convergence)
**And** phase transitions are one-directional (no returning to Phase 1 from Phase 2)

**Technical Notes:**
- New file: `backend/app/agent/complexity.py` (calculator function)
- Integration point: the calculator runs after the gatekeeper resolves weights and the LLM provides levels
- Architecture ref: Decision 1 (Equation), Decision 8 (3-Phase Ordering)

---

### Story 7.6: Routing & AMPM Integration

As a developer,
I want to update the routing logic to use the structured complexity score `C > τ` and pass `dominant_factor` into AMPM nodes for targeted questioning,
So that clarification questions target the most ambiguous dimension instead of asking broadly.

**Acceptance Criteria:**

**Given** the existing `route_by_confidence()` in `routing.py`
**When** a `complexity_breakdown` exists in the agent state
**Then** the router compares `breakdown.score` against `state.clinical_threshold` (defaulting to `CLINICAL_THRESHOLDS["general"]` = 15.0)
**And** if `C > τ`, it routes to `AMPM_ENTRY` with the `dominant_factor` available in state
**And** if `mandatory_clarification` is `True` in state, it routes to `AMPM_ENTRY` regardless of score

**Given** the `complexity_breakdown` is `None` (fallback/legacy path)
**When** routing occurs
**Then** the existing `overall_confidence >= 0.85` logic is used unchanged

**Given** the AMPM `detail_cycle` node in `ampm_nodes.py`
**When** `dominant_factor` is available in state
**Then** the clarification question targets the dominant dimension:
  - `"ingredients"` → asks about hidden/unknown ingredients
  - `"prep"` → asks about preparation method
  - `"volume"` → asks about portion size
**And** the node uses `complexity_breakdown.score > state.clinical_threshold` instead of `complexity_score > 0.7`

**Given** the AMPM `final_probe` node
**When** the probe condition is evaluated
**Then** it uses `complexity_breakdown.score > state.clinical_threshold` instead of the hardcoded `complexity_score > 0.7`

**Technical Notes:**
- Files: `backend/app/agent/routing.py`, `backend/app/agent/ampm_nodes.py`
- The threshold for the confidence-based fast path (`overall_confidence >= 0.85`) remains unchanged — it is separate from the complexity threshold
- Architecture ref: Decision 6 (Routing), Decision 8 (Convergence phase)

---

### Story 7.7: Test Fixtures & Benchmark Integration

As a developer,
I want to update test fixtures with structured complexity data and extend the benchmarking infrastructure to track complexity scoring metrics,
So that we can validate the new scoring system and measure its impact on clarification accuracy.

**Acceptance Criteria:**

**Given** existing agent tests in `backend/tests/`
**When** tests are updated
**Then** test fixtures include `AmbiguityLevels` and `ComplexityBreakdown` objects matching various scenarios (simple meal, complex meal, biomimicry risk)
**And** the gatekeeper service has unit tests for: registry lookup, alias matching, umbrella term detection, unknown food fallback
**And** the complexity calculator has unit tests for: boundary values (0,0,0 → 0.0 and 3,3,3 → 32.0), dominant factor identification, and weight application
**And** the routing logic has unit tests for: `C > τ` routing, mandatory clarification flag, fallback to legacy behavior when `complexity_breakdown` is None

**Given** the existing benchmarking infrastructure in `app/benchmarking/`
**When** benchmark experiments are run
**Then** experiment logs include the `complexity_breakdown` for each analyzed dish
**And** the benchmark report includes average `C` scores alongside existing MAE metrics
**And** the per-dish log includes `dominant_factor` and whether clarification was triggered

**Technical Notes:**
- Files: `backend/tests/test_*.py` (updated fixtures), `backend/app/benchmarking/` (extended logging)
- Existing tests must continue to pass — the backward-compatible `complexity_score` float ensures no regressions
- Architecture ref: Backward compatibility and graceful degradation (Risk Mitigation section)
