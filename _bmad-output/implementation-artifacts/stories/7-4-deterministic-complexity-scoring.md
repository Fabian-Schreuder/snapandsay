# Story 7.4: Deterministic Complexity Scoring

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want the complexity score to be calculated using the transparent formula `C = Σ(w · L²) + P`,
So that I can audit exactly why a specific meal triggered a clarification.

## Acceptance Criteria

1. **Given** the ambiguity levels (`L_i`, `L_p`, `L_v`) and class weights (`w_i`, `w_p`, `w_v`)
2. **When** the score is calculated
3. **Then** the result follows the formula `(w_i · L_i²) + (w_p · L_p²) + (w_v · L_v²) + P_sem`
4. **And** the "Dominant Factor" (the dimension contributing the most to the score) is identified and returned
5. **And** the final score (`C`) is stored in the `AnalysisResult` and `dietary_logs` table
6. **And** the calculation handles cases where specific levels are missing (defaults to 0)
7. **And** the system ensures backward compatibility by populating the legacy `complexity_score` float field with the new calculated value

## Tasks / Subtasks

- [x] Implement Complexity Calculator Service
  - [x] Create `backend/app/services/complexity_calculator.py`
  - [x] Implement `calculate_complexity(ambiguity_levels, food_class_metadata) -> ComplexityBreakdown`
  - [x] Implement the formula: `C = Σ(w · L²) + P`
  - [x] Logic to identify the dominant factor (max of the weighted squared terms)
- [x] Integrate into Agent Workflow
  - [x] Modify `backend/app/agent/nodes.py` (specifically `analyze_input` or a new `audit_complexity` node)
  - [x] Retrieve weights/penalty from `FoodClassRegistry` (implemented in 7.2)
  - [x] Call `calculate_complexity` after getting LLM ambiguity levels
  - [x] Update `AgentState` with the full `ComplexityBreakdown`
- [x] Update Data Models
  - [x] Ensure `AnalysisResult` (in `backend/app/schemas/analysis.py`) has the `complexity_breakdown` field (likely added in 7.1, simplify verify)
- [x] Add Unit Tests
  - [x] Create `backend/tests/services/test_complexity_calculator.py`
  - [x] Test cases for:
    - Zero ambiguity (Baseline)
    - High ambiguity single dimension
    - Mixed ambiguity
    - Umbrella term penalty application
  - [x] Verify dominant factor selection logic

## Dev Notes

### Architecture Decisions (Addendum 2026-02-16)

This story implements **Decision 1: The Complexity Equation** and **Decision 8: Mandatory 3-Phase Ordering (Phase 3)**.

**Formula:**
```python
C = (w_i * L_i**2) + (w_p * L_p**2) + (w_v * L_v**2) + P_sem
```
*Note the squaring of Levels! This is critical for penalizing high ambiguity.*

**3-Phase Ordering Compliance:**
This calculation happens in **Phase 3 (Convergence)**. It relies on:
1. **Phase 1 (Semantic):** `FoodClassRegistry` lookup provides `w` (weights) and `P_sem` (penalty).
2. **Phase 2 (Triangle Audit):** LLM provides `L` (levels 0-3).

**Dependencies:**
- `backend/app/services/food_class_registry.py` (Story 7.2 - DONE) to get weights.
- `backend/app/schemas/analysis.py` (Story 7.1 - DONE) to get `AmbiguityLevels` schema.

### Project Structure Notes

- **Service Layer Pattern:** Implement pure logic in `services/complexity_calculator.py`. Do NOT put calculation logic directly in the agent node.
- **Typing:** Use `ComplexityBreakdown` Pydantic model for return type.
- **Testing:** Pure function, easy to test with unit tests. No mocks needed for the calculator itself, but `nodes.py` integration will need to mock the service.

### Technical Guardrails

- **Float Precision:** Standard Python `float` is fine.
- **Missing Data:** If `AmbiguityLevels` is `None` (e.g., failure in Phase 2), treat all `L=0`, but log a warning.
- **Legacy Compatibility:** The `AnalysisResult` schema likely has a root-level `complexity_score` float. You must set this to the calculated `C` value so existing routing logic (currently checking `complexity_score > 0.7`) continues to work until we update the Router in Story 7.5. (Note: Story 7.5 updates the router to use `C > τ`, but for *this* story, we just ensure the data is there).

### References

- [Architecture Addendum: Complexity Equation](file:///home/fabian/dev/work/snapandsay/_bmad-output/planning-artifacts/architecture.md#Decision-1-The-Complexity-Equation)
- [Architecture Addendum: 3-Phase Ordering](file:///home/fabian/dev/work/snapandsay/_bmad-output/planning-artifacts/architecture.md#Decision-8-Mandatory-3-Phase-Ordering)
- [Food Class Registry Service](file:///home/fabian/dev/work/snapandsay/backend/app/services/food_class_registry.py)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List


- `backend/app/services/complexity_calculator.py`
- `backend/app/agent/nodes.py`
- `backend/tests/services/test_complexity_calculator.py`
- `backend/tests/agent/test_complexity_integration.py`

### Change Log

- 2026-02-17: Implemented `complexity_calculator` service with deterministic formula.
- 2026-02-17: Updated `nodes.py` to integrate complexity calculation into `analyze_input` and `analyze_input_streaming`.
- 2026-02-17: Added comprehensive unit tests and integration tests.
- 2026-02-17: [CR] Fixed type annotation, redundant lookups, verbose comments, typo, duplicate header. Added default-profile fallback test.
