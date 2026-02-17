# Story 7.6: Targeted Question Generation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want clarification questions to be specific to the uncertainty,
So that I can answer quickly with one word.

## Context & Rationale

Currently, the system detects complexity but often asks generic questions like "Can you tell me more about this?" even when the uncertainty is specific (e.g., we know it's a sandwich, but don't know the size).
With the **Structure Complexity Scoring** (Story 7.4), we now have a `ComplexityBreakdown` in the state which identifies the **Dominant Factor** driving the uncertainty:
- `ingredients`: Hidden items (e.g., what's in the curry?)
- `prep`: Invisible preparation (e.g., fried vs grilled?)
- `volume`: Portion size (e.g., cup vs bowl?)

This story implements the logic to use this `dominant_factor` to select a targeted prompt template, reducing cognitive load on the user.

## Acceptance Criteria

1. **Targeted Prep Questioning**
   **Given** a high `prep` ambiguity score is the dominant factor
   **When** the system asks a question
   **Then** it asks about preparation (e.g., "Was this fried or grilled?") rather than a generic "Tell me more".

2. **Targeted Portion Questioning**
   **Given** a high `portion` (volume) ambiguity score is the dominant factor
   **When** the system asks a question
   **Then** it asks about size/quantity (e.g., "Was that a cup or a bowl?").

3. **Fallback Behavior**
   **Given** no dominant factor is clear or the factor is `ingredients`
   **When** the system asks a question
   **Then** it asks a broad but relevant question about composition (e.g., "What specific ingredients were in this?").

## Tasks / Subtasks

- [x] Update Prompt Templates
  - [x] Define targeted prompt templates in `backend/app/agent/constants.py` for 'prep', 'volume', and 'ingredients'.
- [x] Update AMPM Node Logic
  - [x] Modify `generate_clarification` (or equivalent node) in `backend/app/agent/ampm_nodes.py`.
  - [x] Extract `dominant_factor` from `state["complexity_breakdown"]`.
  - [x] Select the appropriate prompt template based on the factor.
- [x] Verification
  - [x] Add unit tests in `backend/tests/agent/test_ampm_nodes.py` to verify dominant_factor propagation.
  - [x] Add unit tests in `backend/tests/services/test_llm_service_targeting.py` to verify prompt template selection.

## Dev Notes

- **State Access**: `state["complexity_breakdown"]` is a Pydantic model `ComplexityBreakdown`. Access `.dominant_factor` attribute.
- **Prompt Strategy**: Keep prompts conversational but direct.
  - Prep: "I see [Food], but I can't tell how it was cooked. Was it [Option A] or [Option B]?"
  - Volume: "I'm not sure about the portion size of [Food]. How much did you have?"
- **Test Coverage**: Mock the state with different `dominant_factor` values and assert the prompt content.

### Project Structure Notes

- Alignment with unified project structure (paths, modules, naming)
- Detected conflicts or variances (with rationale)

### References

- [Architecture: Structured Complexity Score Addendum](file:///home/fabian/dev/work/snapandsay/_bmad-output/planning-artifacts/architecture.md#structured-complexity-score-architecture-addendum-2026-02-16)
- [Story 7.4: Deterministic Complexity Scoring](file:///home/fabian/dev/work/snapandsay/_bmad-output/implementation-artifacts/stories/7-4-deterministic-complexity-scoring.md)

## Dev Agent Record

### Agent Model Used

Gemini (Antigravity)

### Debug Log References

### Completion Notes List

- Added `CLARIFICATION_TEMPLATES` dict to `constants.py` with templates for 'prep', 'volume', 'ingredients', and 'default'.
- Updated `generate_clarification_question` in `llm_service.py` to accept `dominant_factor` parameter and inject the corresponding template instruction into the system prompt.
- Updated both `detail_cycle` and `detail_cycle_streaming` in `ampm_nodes.py` to extract `dominant_factor` from `state["complexity_breakdown"]` and pass it to the LLM service.
- Restored missing `return messages` in `_build_messages` (regression from earlier edit).
- All 22 tests pass (18 existing + 4 new).

### File List
- backend/app/agent/constants.py
- backend/app/agent/ampm_nodes.py
- backend/app/services/llm_service.py
- backend/tests/agent/test_ampm_nodes.py
- backend/tests/services/test_llm_service_targeting.py
- _bmad-output/implementation-artifacts/sprint-status.yaml
