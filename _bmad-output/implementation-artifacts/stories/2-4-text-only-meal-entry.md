
# Story 2.4: Text-Only Meal Entry

**Story ID:** 2.4
**Epic:** 2 - Multimodal Ingestion & Capture
**Status:** in-progress
**Author:** SM Agent (Fabian)
**Date:** 2026-02-16

---

## 1. Story Foundation

### User Story
**As a** user,
**I want to** type my meal description if I can't speak or take a photo,
**So that** I can still log my food in quiet environments or when I don't have a camera available.

### Acceptance Criteria
- [ ] **Trigger:** A discrete "Keyboard" icon is available near the Mic button on the "Snap" page.
- [ ] **Input:** Tapping the icon opens a text input field (Modal or Drawer) with a clear "Type what you ate..." placeholder.
- [ ] **Submission:** Submitting the text triggers the SAME analysis pipeline as voice inputs.
- [ ] **Feedback:** The UI immediately transitions to the "Thinking" state with streaming updates.
- [ ] **Data:** The text is stored as the "transcript" in the log, with null audio/image URLs.
- [ ] **Accessibility:** The input field supports dynamic type settings and has a 60px height (Senior-friendly).

### Business Context
This feature ensures accessibility for users with speech impairments or those in social situations where speaking to a phone is socially awkward. It closes a critical gap in the "Multimodal" promise.

---

## 2. Developer Context & UX Guidance

### Goal
Enable a text-based fallback for meal entry that feels just as "magical" as the voice flow.

### UX Design Requirements (Ref: `ux-design-specification.md`)
- **Entry Point:** Small, discrete keyboard icon next to the main Mic button.
- **Interaction Flow:**
  1. User taps Keyboard icon.
  2. Input field slides up (Drawer on mobile, Dialog on desktop).
  3. User types "Grilled cheese sandwich".
  4. User taps "Log Meal" (Primary Action Button).
  5. UI immediately shows "Thinking..." animation (reusing existing component).
- **Design System:**
  - Use `Dialog` or `Drawer` from Shadcn/UI.
  - Input field height: `h-14` (56px) minimum.
  - Font size: `text-lg` (18px) minimum.
  - Contrast: High contrast text on background.

---

## 3. Technical Implementation Guide

### Frontend Implementation (Next.js 15 + Shadcn/UI)

**File: `src/components/features/input/TextEntryModal.tsx` (NEW)**
- Create a managed component using Shadcn `Dialog` (Desktop) / `Drawer` (Mobile) combined pattern.
- State: `isOpen`, `text`, `isSubmitting`.
- Action: On submit, call the analysis API.

**File: `src/app/(dashboard)/snap/page.tsx`**
- Integrate `TextEntryModal`.
- Add the trigger button near `VoiceCaptureButton`.
- Ensure the `useStreamingAnalysis` hook (or equivalent) handles text-only submission state.

**File: `src/hooks/use-agent.ts`**
- Update to support a `submitText(text: string)` method.
- This method should hit the new/updated API endpoint and establish the SSE connection for "Thinking" events.

### Backend Implementation (FastAPI + LangGraph)

**File: `backend/app/api/v1/schemas/analysis.py`**
- Ensure `AnalysisRequest` (or `AnalysisInput`) supports an optional `text_input` field.
- If strictly separate, creating a specific schema `TextAnalysisRequest` is preferred.

**File: `backend/app/api/v1/endpoints/analysis.py`**
- **New Endpoint:** `POST /text` (or logic in existing endpoint) to handle text-only payloads.
- **Logic:**
  1. Create `dietary_log` entry with `transcript=text`, `source='text'`, `status='processing'`.
  2. Trigger the LangGraph runner.
  3. Return SSE stream generator.

**File: `backend/app/agent/nodes.py`**
- Modify `analyze_input` node:
  - Check if `state.image_url` is missing.
  - If missing, skip Vision API calls.
  - Use the `state.transcript` (from text input) directly for the LLM extraction step.
  - **Constraint:** Ensure the LLM prompt handles "text-only" context (it won't have visual cues).

### Database Schema (Supabase)
- **Table:** `dietary_logs`
- **Impact:** No schema changes expected *if* `image_url` and `audio_url` are nullable.
- **Verification:** Ensure `image_url` and `audio_url` columns allow NULLs. If not, a migration is required.

- [/] **Implementation Task 1: Create TextEntryModal Component**
    - [x] Create `src/components/features/input/TextEntryModal.tsx` using Shadcn/UI Dialog/Drawer.
    - [x] Implement state management (`isOpen`, `text`, `isSubmitting`).
    - [x] Implement submission handler calling `useAgent.submitText`.
    - [x] Add unit tests for component rendering and submission.

- [/] **Implementation Task 2: Integrate Text Entry into Snap Page**
    - [x] Update `src/app/(dashboard)/snap/page.tsx`.
    - [x] Add keyboard icon trigger button near microphone.
    - [x] Hook up state to open the modal.
    - [ ] Add E2E test for opening and closing the modal.

- [/] **Implementation Task 3: Update Agent Hook and API Service**
    - [x] Update `src/hooks/use-agent.ts` with `submitText` method.
    - [x] Verify or implement `POST /analysis/text` (or equivalent) endpoint.
    - [x] Ensure `dietary_log` creation handles text-only input correctly.
    - [ ] Add integration test for text submission flow.

- [ ] **Implementation Task 4: Enhance Agent Logic for Text-Only**
    - [ ] Modify `backend/app/agent/nodes.py` -> `analyze_input`.
    - [ ] Handle missing `image_url` gracefully.
    - [ ] Use `transcript` directly for LLM extraction.
    - [ ] Verify LLM prompts work without visual context.
    - [ ] Add unit tests for `analyze_input` with text-only state.

---

## 4. Architecture & Patterns Compliance

### Critical Rules (Ref: `project-context.md`)
- **Next.js 15:** Use `use client` for the Modal component.
- **Async:** Await all promises.
- **Python:** Use `async def` for the FastAPI endpoint.
- **Pydantic v2:** Use `model_validate` if parsing raw data.
- **Naming:** `TextEntryModal` (PascalCase), `text_entry_service.py` (snake_case).

### Reusability
- **Reuse:** `ThinkingIndicator` component (must be identical to Voice flow).
- **Reuse:** `useAgent` hook logic for SSE handling.
- **Avoid:** Creating a separate "Text Analysis" pipeline in LangGraph. The existing graph should adapt to missing image inputs.

---

## 5. Testing Strategy

### Unit Tests
- **Frontend:** Test `TextEntryModal` renders correctly and calls `onSubmit` with text.
- **Backend:** Test the API endpoint accepts text payload and creates a log entry.
- **Agent:** Test `analyze_input` node handles `image_url=None` gracefully.

### Integration Tests
- **Flow:** Submit text -> Verify Log Entry created in DB -> Verify Stream starts.

### E2E Tests (Playwright)
- **Scenario:**
  1. Go to Snap page.
  2. Click Keyboard icon.
  3. Type "Banana".
  4. Submit.
  5. Verify "Thinking..." appears.
  6. Verify "Banana" is logged in history.

---

## 6. Git & Version Control
- **Branch:** `feat/story-2-4-text-entry`
- **Commit Message:** `feat: implement text-only meal entry flow`
