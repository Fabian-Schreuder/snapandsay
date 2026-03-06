# Story 7.3: Semantic Gatekeeper

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want the system to ask me "What kind of sandwich?" *before* asking about ingredients,
So that the conversation feels natural and logical.

## Acceptance Criteria

1. **Given** I have logged a generic item (e.g., "Sandwich")
2. **When** the system analyzes it
3. **Then** the Gatekeeper detects it is an "Umbrella Term"
4. **And** the system asks a "Type" clarification question first (Semantic Interruption)
5. **And** the system does *not* try to guess ingredients until I answer
6. **And** the Semantic Gatekeeper implements the "Lexical Bounding Check" pattern defined in Architecture Decision 3

## Tasks / Subtasks

- [x] Implement Semantic Gatekeeper Service
  - [x] Create `backend/app/services/semantic_gatekeeper.py`.
  - [x] Implement `assess_lexical_boundedness(food_items)` using `FoodClassRegistry`.
  - [x] Returns list of `UnboundedItem` (generic terms requiring specification).
- [x] Update Agent State & Models
  - [x] Update `backend/app/agent/state.py` to include `unbounded_items` or `semantic_interruption_needed` flag.
  - [x] Ensure `AnalysisResult` or intermediate state enables tracking lexical specificity.
- [x] Integrate into LangGraph
  - [x] Create or Update a node (e.g., `check_semantic_ambiguity` or within `analyze_input`) to call the Gatekeeper.
  - [x] Update `backend/app/agent/graph.py` topology: Ensure Gatekeeper runs *after* initial item identification but *before* complexity scoring/Triangle Audit.
  - [x] Implement routing logic: If Semantically Unbounded -> Route to Clarification immediately.
- [x] Add Unit Tests
  - [x] Test `assess_lexical_boundedness` with "Sandwich" (Unbounded) vs "Turkey Sandwich" (Bounded).
  - [x] Test integration with `FoodClassRegistry` mock.
  - [x] Test graph transition logic.

## Dev Notes

### Architecture Decisions (Addendum 2026-02-16)

This story implements **Decision 3: Semantic Gatekeeper Pattern** and **Decision 8: Mandatory 3-Phase Ordering**.

**Pattern:**
Two-stage gate:
1. **Lexical Bounding Check:** Identifies items names that are too generic (Umbrella Terms).
2. **Registry Lookup:** (Already implemented in 7.2, used here).

**Strict Ordering:**
Phase 1 (Semantic Resolution) MUST happen before Phase 2 (Triangle Audit).
*Do not calculate material complexity (ingredients/prep) for unbounded terms.*

**Pseudocode:**
```python
def assess_lexical_boundedness(food_items: list[FoodItem]) -> list[UnboundedItem]:
    unbounded = []
    for item in food_items:
        match = registry.lookup(item.name)
        if match and match.is_umbrella_term:
            unbounded.append(item)
    return unbounded
```

### Project Structure Notes

- **Backend-Only:** This story is purely backend logic.
- **Files to Touch:**
  - `backend/app/services/semantic_gatekeeper.py` (New)
  - `backend/app/agent/graph.py` (Modify)
  - `backend/app/agent/state.py` (Modify)
  - `backend/tests/services/test_semantic_gatekeeper.py` (New)
- **Dependencies:**
  - Uses `backend/app/services/food_class_registry.py` (Implemented in Story 7.2).

### References

- [Architecture Addendum: Semantic Gatekeeper Pattern](file:///home/fabian/dev/work/snapandsay/_bmad-output/planning-artifacts/architecture.md#Decision-3-Semantic-Gatekeeper-Pattern)
- [Architecture Addendum: Mandatory 3-Phase Ordering](file:///home/fabian/dev/work/snapandsay/_bmad-output/planning-artifacts/architecture.md#Decision-8-Mandatory-3-Phase-Ordering)
- [Food Class Registry](file:///home/fabian/dev/work/snapandsay/backend/app/services/food_class_registry.py)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

- `backend/app/agent/graph.py`
- `backend/app/agent/nodes.py`
- `backend/app/agent/state.py`
- `backend/app/agent/constants.py`
- `backend/app/services/semantic_gatekeeper.py`
- `backend/tests/services/test_semantic_gatekeeper.py`
- `backend/tests/agent/test_semantic_routing.py`
