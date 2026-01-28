---
title: 'Observation Validation'
slug: 'observation-validation'
created: '2026-01-28'
status: 'complete'
stepsCompleted: [1, 2, 3, 4, 5, 6]
tech_stack: ['Python', 'FastAPI', 'Pydantic', 'OpenAI', 'Next.js', 'React']
files_to_modify: ['backend/app/schemas/analysis.py', 'backend/app/services/llm_service.py', 'backend/app/agent/nodes.py', 'frontend/components/features/logs/FoodEntryCard.tsx', 'backend/app/models/log.py']
code_patterns: ['Pydantic Schema Validation', 'LLM Prompt Engineering', 'LangGraph Agent Logic', 'Frontend Component State']
test_patterns: ['Unit Tests (Backend)', 'Manual Verification']
---

# Tech-Spec: Observation Validation

**Created:** 2026-01-28

## Overview

### Problem Statement

Currently, the system attempts to process any input as a meal, even if the photo is of a non-food object (e.g., a shoe). This results in confusing log entries where the LLM tries to hallucinate nutritional data or returns empty data that isn't handled gracefully.

### Solution

Implement a validation step. Input will be categorized:
1. **Valid**: Food, Drink, Supplements.
2. **Unclear**: Blurry, dark, or ambiguous (Triggers Clarification, NOT invalidation).
3. **Invalid**: Clearly non-food objects (e.g., shoe, laptop).

Invalid entries will be marked with a new status `invalid` (distinct from `failed`). Users will have a UI option to "Retry Analysis" or "Edit Details" to override false negatives, ensuring a recovery path.

### Scope

**In Scope:**
- Update `AnalysisResult` schema to include validity flags.
- Update `llm_service.py` system prompt to enforce validation logic and distinguish "Unclear" from "Invalid".
- Update `analyze_input_streaming` in `nodes.py` to handle `is_food=False` cases.
- Valid input types: Food, Drinks, Supplements (protein, vitamins, etc).
- Invalid input types: Non-food objects.
- **Recovery Path**: "Invalid" logs can be manually edited by the user to "correct" them (effectively forcing them to valid).

**Out of Scope:**
- Client-side pre-validation.
- Deleting the log entirely (User requested to keep it with invalid status).

## Context for Development

### Codebase Patterns

- **Schema-Driven AI**: The `AnalysisResult` Pydantic model directly controls the structured output from the LLM. Adding fields here is the standard way to extract new metadata.
- **Agent Orchestration**: `nodes.py` contains the business logic for handling the analysis result. It already handles exceptions and persistence.
- **Frontend Display**: `FoodEntryCard.tsx` consumes the `DietaryLog` type. We need to ensure "failed" or invalid logs are handled appropriately (likely filtered or shown with a specific error state).

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `backend/app/schemas/analysis.py` | Defines `AnalysisResult` struct for LLM |
| `backend/app/services/llm_service.py` | Constructs the prompt and calls OpenAI |
| `backend/app/agent/nodes.py` | Implementation of `analyze_input_streaming` where logic resides |
| `frontend/app/(dashboard)/page.tsx` | Main dashboard view listing logs |
| `frontend/components/features/logs/FoodEntryCard.tsx` | Component for individual log card |

### Technical Decisions

- **Schema Change**: Adding `is_food: bool` and `non_food_reason: str | None` to `AnalysisResult`.
- **Status Mapping**:
  - `is_food=True` -> `status='created'` (or normal flow)
  - `is_food=False` -> `status='invalid'` (New ENUM value for DietaryLog status)
  - **Clarification**: If LLM is unsure, it should ask a question (standard clarification flow), NOT mark as invalid.

- **Prompt Engineering**:
  - Explicitly list categories: "Food, Drink, Pills/Supplements".
  - "If the image is too blurry to see, ask for clarification." (Don't auto-reject).
  - "If it is clearly a non-food object (e.g., shoe, car), set is_food=False."

- **Frontend**:
  - `FoodEntryCard` for `status='invalid'` shows Red warning.
  - Action: "Delete" (Cleanup) or "Edit" (Override - allows user to manually input food if AI was wrong).

## Implementation Plan

### Tasks

- [x] Task 1: Update DietaryLog Model & Migration
  - File: `backend/app/models/log.py`
  - Action: Update `LogStatus` enum (if exists) or valid values to include `invalid`.
  - Notes: Check if it's a PG Enum or String. If String, just documented update.

- [x] Task 2: Update Analysis Schema
  - File: `backend/app/schemas/analysis.py`
  - Action: Add `is_food: bool` (default False - safe fail) and `non_food_reason: str | None`.
  - Notes: Default to False to prevent fail-open.

- [x] Task 3: Update LLM Prompt
  - File: `backend/app/services/llm_service.py`
  - Action: Update prompt. Rules:
    1. Food/Drink/Supplements = Valid.
    2. Blurry/Dark/Ambiguous = Ask Question (Clarification Event), do NOT invalidate.
    3. Clearly Non-Food = Invalid.

- [x] Task 4: Handle Invalid Logic
  - File: `backend/app/agent/nodes.py`
  - Action: In `analyze_input_streaming`:
    - If `events` has Clarification -> Proceed as normal clarification.
    - Else If `is_food` is False -> Mark log status as `invalid`.
    - Else -> Normal processing.

- [x] Task 5: Frontend Invalid Components
  - File: `frontend/components/features/logs/FoodEntryCard.tsx`
  - Action: Handle `invalid` status.
  - UI: Red/Warning card. "Invalid Entry: [Reason]".
  - Actions: Delete, Edit (allows user to rescue).

### Acceptance Criteria

- [ ] AC 1: Review "Shoe" -> Status `invalid`, user sees "Invalid Observation".
- [ ] AC 2: Review "Blurry Sandwich" -> Agent asks "I can't see clearly", Status remains `analyzing` or `clarifying`. (Does NOT Invalid).
- [ ] AC 3: Review "Vitamins" -> Valid.
- [ ] AC 4: User Override -> User clicks "Edit" on Invalid Shoe log -> Can manually type "Cake" -> Status becomes `created`.

## Additional Context

### Dependencies

- None. Pure logic update.

### Testing Strategy

- **Unit Tests**:
  - `test_llm_validation.py`: Mock `analyze_multimodal` returning `is_food=False`. Verify `AnalysisResult` parses it.
- **Manual Verification**:
  - Upload a random non-food image (e.g., laptop, table surface).
  - Verify it shows up as failed in Dashboard.
  - Upload a valid meal. Verify it still works.

### Notes

- We depend on the LLM's ability to discern food vs non-food. It won't be perfect.
- We are using `failed` status which might overlap with technical failures (e.g. database error). We should prefix the description with "[Invalid]" to distinguish.
