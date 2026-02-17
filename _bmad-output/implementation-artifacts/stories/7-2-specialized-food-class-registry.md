# Story 7.2: Specialized Food Class Registry

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a system,
I want to recognize specific classes of food (e.g., "Sandwich", "Soup") and apply pre-defined risk profiles,
So that I don't treat a high-risk "Burrito" the same as a low-risk "Salad" when deciding to ask questions.

## Acceptance Criteria

1. **Given** a food item is identified
2. **When** I consult the Food Class Registry
3. **Then** I retrieve specific "Biomimicry Risk" weights for that class
4. **And** if the item is an "Umbrella Term" (like "Sandwich"), I flag it for immediate clarification
5. **And** unknown foods fall back to a default "Moderate Risk" profile
6. **And** the registry is loaded from a YAML configuration file at startup

## Tasks / Subtasks

- [ ] Create Food Class Registry Configuration
  - [x] Create `backend/app/agent/data/food_class_registry.yaml` with initial classes: `burger`, `sandwich`, `milk`, `pasta`, `curry` and `default` profile.
- [x] Ensure YAML structure matches Architecture Addendum specifications.
- [ ] Implement Food Class Registry Service
  - [x] Create `backend/app/services/food_class_registry.py` (Singleton pattern).
- [x] Implement `load_registry()` to parse YAML.
- [x] Implement `lookup(food_name: str)` with fuzzy matching (alias support).
- [x] Implement `get_risk_profile(food_name: str)` returning weights, penalties, and flags.
- [ ] Add Unit Tests
  - [x] Create `backend/tests/services/test_food_class_registry.py`.
- [x] Test loading valid/invalid YAML.
- [x] Test exact match lookup.
- [x] Test alias lookup (e.g., "cheeseburger" -> "burger").
- [x] Test fallback to default for unknown foods.

## Dev Notes

### Architecture Decisions (Addendum 2026-02-16)

This story implements **Stage 2: Registry Lookup (Biomimicry Risk)** from the Structured Complexity Score architecture.

**Key Data Structure (YAML):**
```yaml
classes:
  burger:
    weights: { ingredients: 0.8, prep: 0.6, volume: 0.3 }
    semantic_penalty: 3.0
    mandatory_clarification: true
    is_umbrella_term: false
    aliases: ["hamburger", "patty"]
```

**Implementation Pattern:**
- **Singleton:** The registry should be loaded once at startup (e.g., in `main.py` lifespan or lazily) and cached.
- **Path:** `backend/app/agent/data/food_class_registry.yaml`
- **Service:** `backend/app/services/food_class_registry.py`

### Project Structure Notes

- **Backend-Only:** This story is purely backend.
- **Files to Touch:**
  - `backend/app/agent/data/food_class_registry.yaml` (New)
  - `backend/app/services/food_class_registry.py` (New)
  - `backend/tests/services/test_food_class_registry.py` (New)

### References

- [Architecture Addendum: Biomimicry Risk Registry](file:///home/fabian/dev/work/snapandsay/_bmad-output/planning-artifacts/architecture.md#Stage-2-Registry-Lookup-Biomimicry-Risk)
- [Food Class Registry YAML Structure](file:///home/fabian/dev/work/snapandsay/_bmad-output/planning-artifacts/architecture.md#New-file-backendappagentdatafood_class_registryyaml)

## Dev Agent Record

### Agent Model Used

Antigravity (Gemini 2.0 Flash)

### Debug Log References

### Completion Notes List
- [2026-02-17] Code Review: Fixed missing test coverage for invalid YAML. Added `test_load_invalid_yaml`. Validated all ACs.

### File List
- backend/app/agent/data/food_class_registry.yaml
- backend/app/services/food_class_registry.py
- backend/tests/services/test_food_class_registry.py
