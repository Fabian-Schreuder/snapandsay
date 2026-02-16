# Story 7.1: Structured Ambiguity Analysis (Phase 1)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a system,
I want to assess ambiguity across three specific dimensions (Hidden Ingredients, Invisible Prep, Portion Size) using a 0-3 scale,
So that I can identify exactly *why* a meal is complex.

## Acceptance Criteria

1. **Given** an analyzed food item
2. **When** the agent performs its assessment
3. **Then** it assigns a score (0-3) for:
   - `hidden_ingredients` (e.g., 3 for "Curry", 0 for "Apple")
   - `invisible_prep` (e.g., 2 for "Deep Fried", 0 for "Raw")
   - `portion_size` (e.g., 3 for "Plate", 0 for "1 cup")
4. **And** these scores are grounded in the specific definitions from the Architecture
5. **And** the system supports fallback to a default score if structured analysis fails
6. **And** the `AnalysisResult` and `ComplexityBreakdown` schemas are updated to match the addendum

## Tasks / Subtasks

- [x] Update Data Models (Schema)
  - [x] Update `backend/app/schemas/analysis.py` to include `AmbiguityLevels` and `ComplexityBreakdown`
  - [x] Ensure backward compatibility for `complexity_score` (float)
  - [x] Add field validation (0-3 range)
- [x] Update LLM Service & Prompts
  - [x] Modify `backend/app/services/llm_service.py` system prompt to explain the 3 scales
  - [x] Update structured output request to include `ambiguity_levels`
  - [x] Implement fallback logic for legacy responses
- [x] Update State & Analysis Flow
  - [x] Update `backend/app/agent/state.py` to include `complexity_breakdown`
  - [x] Ensure `analyze_input` node populates the new fields
- [x] Add Unit Tests for Schema & Logic
  - [x] Test `AmbiguityLevels` validation
  - [x] Test `ComplexityBreakdown` calculation (if computed here, though Calculator is 7.4)

## Dev Notes

### Architecture Decisions (Addendum 2026-02-16)

This story implements **Decision 4: LLM Prompt — Matrix Scan** and parts of **Decision 1**.

**Key Schemas:**
```python
class AmbiguityLevels(BaseModel):
    hidden_ingredients: int = Field(ge=0, le=3)
    invisible_prep: int = Field(ge=0, le=3)
    portion_ambiguity: int = Field(ge=0, le=3)

class ComplexityBreakdown(BaseModel):
    levels: AmbiguityLevels
    weights: dict[str, float]  # Filled later by Gatekeeper (Story 7.3)
    semantic_penalty: float
    dominant_factor: str
    score: float
```
*Ref: `_bmad-output/planning-artifacts/architecture.md` Section: Structured Complexity Score Architecture*

### Project Structure Notes

- **Backend-Only:** This story is purely backend (FastAPI/LangGraph).
- **Files to Touch:**
  - `backend/app/schemas/analysis.py`
  - `backend/app/services/llm_service.py`
  - `backend/app/agent/state.py`
  - `backend/tests/services/test_llm_service.py`
- **Naming:* Use `snake_case` for all Python fields.

### References

- [Architecture Addendum: Structured Complexity Score](file:///home/fabian/dev/work/snapandsay/_bmad-output/planning-artifacts/architecture.md#Structured-Complexity-Score-Architecture-Addendum-2026-02-16)
- [Ambiguity Scales Definition](file:///home/fabian/dev/work/snapandsay/_bmad-output/planning-artifacts/architecture.md#Decision-2-Ambiguity-Level-Scales)

## Dev Agent Record

### Agent Model Used

Antigravity (Gemini 2.0 Flash)

### Debug Log References

### Completion Notes List

- Verified implementation of ambiguity analysis.
- Confirmed ACs 1-6 are met.
- Unit tests passed.
- Marked as done via Code Review.

### File List
- backend/app/schemas/analysis.py
- backend/app/services/llm_service.py
- backend/app/agent/state.py
- backend/app/agent/nodes.py
- backend/tests/services/test_ambiguity_analysis.py
- backend/tests/services/test_llm_service.py
