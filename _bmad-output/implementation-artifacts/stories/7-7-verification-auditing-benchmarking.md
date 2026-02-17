# Story 7.7: Verification & Auditing (Benchmarking)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want to verify that the new scoring system improves accuracy without annoying users,
So that I can trust the clinical validity.

## Context & Rationale

With the completion of Stories 7.1–7.6, the full "Structured Complexity Scoring & Targeted Clarification" pipeline is now operational:
- **Story 7.1** — LLM outputs `AmbiguityLevels` (three 0–3 integer scores)
- **Story 7.2** — `FoodClassRegistry` provides biomimicry risk profiles
- **Story 7.3** — `SemanticGatekeeper` resolves umbrella terms before scoring
- **Story 7.4** — `ComplexityCalculator` deterministically computes `C = Σ(w·L²) + P`
- **Story 7.5** — Clinical thresholds route decisions per user profile
- **Story 7.6** — Dominant factor drives targeted clarification prompts

**Problem:** The existing benchmarking infrastructure (`backend/app/benchmarking/`) was built before the structured scoring system and only logs nutritional MAE metrics and latency. It does **not** capture:
- The per-dish `ComplexityBreakdown` (score, dominant_factor, levels, weights)
- Which dimension triggered a clarification question
- A comparison between the old opaque `complexity_score` float and the new structured score

This story closes the loop by updating the benchmark pipeline to capture and report the full complexity reasoning trace, enabling researchers to audit **why** each meal triggered (or didn't trigger) a clarification.

## Acceptance Criteria

1. **Complexity Breakdown Logging**
   **Given** a benchmark run processes a dish
   **When** the agent returns its analysis
   **Then** the per-dish result includes the full `ComplexityBreakdown` (score, dominant_factor, levels, weights, semantic_penalty)
   **And** these are persisted in the experiment log JSON

2. **Dominant Factor Reporting**
   **Given** a completed benchmark run
   **When** I view the aggregate report
   **Then** I can see a distribution of which dimension (ingredients, prep, volume, none) was the dominant factor across all dishes
   **And** I can see the count of clarification questions that were triggered

3. **Score Comparison Capability**
   **Given** a benchmark run
   **When** the per-dish results are logged
   **Then** both the old-style `complexity_score` float and the new `complexity_breakdown.score` are captured side-by-side
   **And** the experiment report includes a comparison section showing the correlation

4. **CLI Integration**
   **Given** the user runs the existing benchmark CLI
   **When** a benchmark completes
   **Then** the complexity metrics are included in the console summary output
   **And** the saved experiment JSON includes the full complexity data

## Tasks / Subtasks

- [x] Task 1: Extend per-dish result schema (AC: #1)
  - [x] 1.1 Add `complexity_breakdown` field to the per-dish result dict captured by `OracleRunner.run_dish()`
  - [x] 1.2 Parse `complexity_breakdown` from the SSE `agent.response` event payload when available
  - [x] 1.3 Preserve backward compatibility: if `complexity_breakdown` is absent (older runs), set to `None`

- [x] Task 2: Add complexity aggregate metrics (AC: #2)
  - [x] 2.1 Create `ComplexityMetrics` dataclass in `metrics.py` with fields: `total_scored`, `mean_score`, `clarification_triggered_count`, `dominant_factor_distribution` (dict mapping factor → count)
  - [x] 2.2 Implement `MetricsCalculator.aggregate_complexity()` to compute these from per-dish results
  - [x] 2.3 Add `complexity_stats` to the aggregate report dict

- [x] Task 3: Score comparison utilities (AC: #3)
  - [x] 3.1 Ensure per-dish result captures both `complexity_score` (old float from `AnalysisResult`) and `complexity_breakdown.score` (new computed value)
  - [x] 3.2 Add a `score_comparison` section to `ExperimentLog.export_markdown()` showing old vs new scores in a table

- [x] Task 4: CLI summary updates (AC: #4)
  - [x] 4.1 Update `cli.py` benchmark command output to display complexity metrics summary after MAE and latency
  - [x] 4.2 Include `complexity_stats` in the `ExperimentResult` `metrics` dict so it's persisted in experiment JSON

- [x] Task 5: Tests (AC: #1, #2, #3, #4)
  - [x] 5.1 Add unit test for `MetricsCalculator.aggregate_complexity()` with varied dominant factors
  - [x] 5.2 Add unit test ensuring per-dish result captures `complexity_breakdown` from SSE payload
  - [x] 5.3 Add unit test for `export_markdown()` score comparison table
  - [x] 5.4 Add unit test for backward compatibility when `complexity_breakdown` is `None`

## Dev Notes

### Implementation Patterns

- **OracleRunner SSE parsing**: Updated `_process_loop` to extract `complexity_breakdown` and `complexity_score` from `agent.response` payload.
- **Aggregation**: Added `aggregate_complexity` to `MetricsCalculator` to synthesize distribution of dominant factors.
- **Reporting**: Extended `ExperimentLog.export_markdown` to include a dynamic score comparison section.
- **CLI**: CLI summary now outputs dishes scored, mean complexity, and clarification counts.

### Key File Locations

| Purpose | File |
|---|---|
| Oracle runner (SSE parsing) | `backend/app/benchmarking/oracle_runner.py` |
| Metrics calculation | `backend/app/benchmarking/metrics.py` |
| Experiment logging | `backend/app/benchmarking/experiment_log.py` |
| Benchmark schemas | `backend/app/benchmarking/schemas.py` |
| CLI entry point | `backend/app/benchmarking/cli.py` |
| Complexity calculator (reference) | `backend/app/services/complexity_calculator.py` |
| Analysis schemas (reference) | `backend/app/schemas/analysis.py` |
| Existing benchmark tests | `backend/tests/benchmarking/` |
| New Story 7.7 tests | `backend/tests/benchmarking/test_complexity_benchmarking.py` |

### Testing Standards

- **Location**: `backend/tests/benchmarking/`
- **Framework**: Pytest with `asyncio_mode = auto`
- **Patterns**: Follow existing test patterns in `test_metrics.py` and `test_runner.py`
- **No live API calls**: Mock all HTTP/SSE interactions
- **Run**: `cd backend && uv run pytest tests/benchmarking/test_complexity_benchmarking.py -v`

### Project Structure Notes

- All changes are within `backend/app/benchmarking/` — no agent graph or routing changes needed
- The `cli.py` uses `click` for CLI commands
- `ExperimentResult` is a plain `@dataclass`, not Pydantic — follow the same pattern for any new dataclasses

### Previous Story Intelligence

From Story 7.6:
- `ComplexityBreakdown` is stored in `state["complexity_breakdown"]` as a Pydantic model with `.dominant_factor`, `.score`, `.levels`, `.weights`, `.semantic_penalty` attributes
- The `complexity_score` field in `AnalysisResult` is still populated for backward compatibility (computed from breakdown)
- The SSE stream includes the full analysis result in `agent.response` events — this is where the benchmark runner should extract complexity data

### Git Context

Recent commits on `complexity-scoring` branch:
- `cd52a35` — Story 7.7: implementation (benchmarking updates)
- `a5c2aa8` — Story 7.6: targeted question generation
- `21be76a` — Story 7.5: clinical threshold routing
- `885e0fe` — Story 7.4: deterministic complexity scoring
- `99fc886` — Story 7.3: semantic gatekeeper and food class registry

### References

- [Architecture: Research Infrastructure](file:///home/fabian/dev/work/snapandsay/_bmad-output/planning-artifacts/architecture.md#research-infrastructure-benchmarking--optimization)
- [Architecture: Structured Complexity Score Addendum](file:///home/fabian/dev/work/snapandsay/_bmad-output/planning-artifacts/architecture.md#structured-complexity-score-architecture-addendum-2026-02-16)
- [Story 7.4: Deterministic Complexity Scoring](file:///home/fabian/dev/work/snapandsay/_bmad-output/implementation-artifacts/stories/7-4-deterministic-complexity-scoring.md)
- [Story 7.6: Targeted Question Generation](file:///home/fabian/dev/work/snapandsay/_bmad-output/implementation-artifacts/stories/7-6-targeted-question-generation.md)

## Dev Agent Record

### Agent Model Used
Antigravity (Senior AI Engineer) - Gemini 3. Pro

### Debug Log References
- Fixed float formatting ValueError in `experiment_log.py` when metrics were "N/A".
- Fixed NameError in `experiment_log.py` by restoring `ts` variable.

### Completion Notes List
- Updated `oracle_runner.py` to capture `complexity_breakdown` from SSE response.
- Added `ComplexityMetrics` and `aggregate_complexity` to `metrics.py`.
- Enhanced `ExperimentLog.export_markdown` with score comparison table.
- Upgraded CLI summary output to display complexity statistics.
- Added comprehensive unit and integration tests.
- **Review Fixes**: 
  - Fixed `ExperimentResult.metrics` type mismatch (dict instead of float).
  - Added `total_questions_asked` to metrics to better track user effort.
  - Corrected `cli.py` output and import structure.
  - Staged `backend/tests/benchmarking/test_complexity_benchmarking.py` in git.
  - **Review Cycle 2**:
    - Validated `complexity_breakdown` structure in `oracle_runner.py` and `metrics.py` to prevent crashes.
    - Updated `oracle_runner.py` docstrings.
    - Documented reason for `LatencyTracker` re-instantiation in `cli.py`.
    - Updated Story file with latest commit hash (`cd52a35`).

### File List
- `backend/app/benchmarking/oracle_runner.py`
- `backend/app/benchmarking/metrics.py`
- `backend/app/benchmarking/experiment_log.py`
- `backend/app/benchmarking/cli.py`
- `backend/tests/benchmarking/test_complexity_benchmarking.py`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
