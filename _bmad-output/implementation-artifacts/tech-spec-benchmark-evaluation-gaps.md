---
title: 'Benchmark Evaluation Gaps - Multi-Mode Runner, N=500, and Complexity Capture'
slug: 'benchmark-evaluation-gaps'
created: '2026-03-07'
status: 'completed'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.12+', 'FastAPI', 'LangGraph', 'Pydantic v2', 'httpx', 'pytest']
files_to_modify:
  - 'backend/app/schemas/sse.py'
  - 'backend/app/api/v1/endpoints/stream.py'
  - 'backend/app/agent/nodes.py'
  - 'backend/app/benchmarking/oracle_runner.py'
  - 'backend/app/benchmarking/cli.py'
  - 'backend/app/benchmarking/metrics.py'
  - 'backend/tests/benchmarking/test_runner.py'
  - 'backend/app/agent/graph.py'
code_patterns:
  - 'SSE streaming via httpx async client with event type routing'
  - 'Pydantic v2 BaseModel schemas for request/response contracts'
  - 'Dataclass-based metrics with to_dict() serialization'
  - 'Checkpoint JSON files for crash recovery'
  - 'argparse subcommands for CLI (run, experiment, history, optimize)'
test_patterns:
  - 'pytest with async fixtures in backend/tests/benchmarking/'
  - 'Existing test files: test_runner.py, test_stratification.py, test_question_parser.py, test_loader.py, test_metrics.py, test_complexity_benchmarking.py'
---

# Tech-Spec: Benchmark Evaluation Gaps - Multi-Mode Runner, N=500, and Complexity Capture

**Created:** 2026-03-07

## Overview

### Problem Statement

The thesis claims a three-way comparison (single-shot VLM vs agentic loop vs naive-always-ask) at N=500 per stratum with complexity scoring data, but the benchmark infrastructure only runs the agentic pipeline, caps at N<=20, doesn't capture `complexity_breakdown`, and has no baseline modes - making the thesis claims unsubstantiated.

### Solution

Extend `OracleRunner` with a `mode` parameter wiring existing `force_finalize`/`force_clarify` flags, diagnose and fix the `complexity_breakdown` pipeline break, fix pre-existing clarification bugs, add checkpointing/retry infrastructure for long N=500 runs, and re-derive all thesis metrics (MAE per stratum, TNR/TPR, turn reduction %) from the full dataset.

### Scope

**In Scope:**
- `mode` param on `OracleRunner` (`agentic`, `single-shot`, `naive-always-ask`)
- Fix `complexity_breakdown` pipeline (SSE schema + dual emission sites)
- Fix `_submit_answer` payload format mismatch (pre-existing bug blocking clarification modes)
- Fix clarification question extraction in OracleRunner (pre-existing bug — extracts `"question"` but payload has `"questions"` list)
- Long-run infrastructure: checkpointing, retry, timeout handling for N=500
- CLI flags to select mode and stratum size
- Re-derive TNR/TPR, MAE per stratum, turn-reduction `[Y]%` from large runs

**Out of Scope:**
- Changes to the complexity scoring formula itself
- Changes to the agent's clarification question generation logic
- Frontend/UI changes
- New stratification logic or threshold tuning
- Actually executing the N=500 runs (spec covers the infra, not the run itself)
- `experiment` subcommand mode support (deferred — requires `PromptOptimizer` changes)

## Context for Development

### Codebase Patterns

- `force_finalize` and `force_clarify` flags already exist in `routing.py:29-36` and `stream.py:23-24` — not wired into OracleRunner's `stream_payload` (line 124-131)
- **Force-flag flow**: `StreamAnalysisRequest` fields → `event_generator` copies them into `initial_state` dict (stream.py:62-63) → `run_streaming_agent(initial_state)` propagates to agent state → `route_by_confidence(state)` reads `state.get("force_clarify")` / `state.get("force_finalize")` at routing.py:29-30. Note: `force_finalize` is checked BEFORE mandatory_clarification and clinical threshold checks (routing.py:33-34), meaning single-shot mode bypasses all safety routing — acceptable for benchmarking purposes as the goal is measuring raw single-shot accuracy.
- SSE streaming: OracleRunner listens for `agent.clarification`, `agent.response`, `agent.error` via httpx async stream
- **Stream termination after clarification (Critical)**: The SSE stream TERMINATES after a clarification event. In `graph.py:132-134`, after `generate_semantic_clarification_streaming` completes and `needs_clarification` is true, the generator does `yield state; return` — the stream ends. The frontend handles this by POSTing a NEW `/api/v1/analysis/stream` request (with `log_id` from the clarification event) to continue the conversation. OracleRunner's `_process_loop` currently assumes a single persistent stream for multi-turn clarification — this is architecturally broken. The runner must implement a reconnection loop: detect clarification event → submit answer → open NEW stream → repeat until `agent.response` received.
- **Semantic gatekeeper bypasses force_finalize**: The semantic gatekeeper runs BEFORE `route_by_confidence` in `graph.py:117-122`. If the gatekeeper determines `semantic_interruption_needed`, a clarification is generated regardless of `force_finalize`. The `force_finalize` flag is only checked at `routing.py:33` in `route_by_confidence`, which executes at `graph.py:140` — AFTER the gatekeeper. This means `single-shot` mode can still receive clarification events. The OracleRunner must handle this gracefully.
- **complexity_breakdown bug — dual emission root cause**: There are TWO `AgentResponse` SSE emissions:
  1. `finalize_log_streaming` in `nodes.py:928-935` emits an `SSEEvent(type=EVENT_RESPONSE, payload=AgentResponse(...))` with only `log_id`, `nutritional_data`, `status` — no complexity fields. This event flows through `event_generator` as a pass-through (`yield await format_sse(item)` at stream.py:81).
  2. `event_generator` in `stream.py:92-100` constructs a SECOND `AgentResponse` after the loop ends, also without complexity fields.
  - **The OracleRunner receives emission #1 first** (the `finalize_log_streaming` one), matches `event_type == "agent.response"` at line 199, and `break`s at line 217. It never sees emission #2. Both emission sites must include complexity data.
- **Complexity data location in state**: Multiple state dict yields exist throughout the node pipeline. The `complexity_breakdown` is populated by `_enrich_with_complexity()` and yielded in the analysis state dict at `nodes.py:417-426`. The `finalize_log_streaming` state yield at `nodes.py:937` does NOT include `complexity_breakdown` — it must be read from the accumulated state, not from the finalize yield.
- **Pydantic v2 serialization warning**: `state["complexity_breakdown"]` is a `ComplexityBreakdown` Pydantic model (confirmed in `agent/state.py`). The new `AgentResponse.complexity_breakdown` field is typed as `dict[str, Any]`. Pydantic v2 will NOT auto-coerce the model to a dict — `.model_dump()` MUST be called explicitly before passing to `AgentResponse` at BOTH emission sites, or validation will fail.
- **`_submit_answer` payload mismatch (pre-existing bug)**: OracleRunner sends `{"response": answer, "is_voice": False}` at line 244. But the clarify endpoint (`analysis.py:59-62`) expects `ClarifyRequest` which requires `{"responses": [{"response": "...", "is_voice": false}]}` — a list of `ClarifyResponse` objects under a `responses` key.
- **Clarification question extraction bug (pre-existing)**: OracleRunner at line 172 does `question = data.get("question", "")`, but the `AgentClarification` payload schema (`sse.py:46-57`) has `questions` — a list of `ClarificationItem` objects, each with `item_name`, `question`, `options`. The runner extracts a key that doesn't exist, gets an empty string, and `QuestionParser` falls back to generic answers. This degrades all clarification modes.
- **`force_clarify` limitation**: `force_clarify=True` routes to AMPM via `route_by_confidence`, and `_get_all_low_confidence_items` (nodes.py:63-81) returns ALL items when `force_clarify=True`. However, `detail_cycle_streaming` in `ampm_nodes.py` filters items through `_item_already_asked` and only asks about items not yet asked. If all items have been asked about in a prior round, no question is generated and turns may be 0 even with `force_clarify`. This affects the "naive-always-ask" baseline reliability.
- Benchmark results stored as JSON in `backend/benchmark_output/` with per-experiment and per-dish granularity. The `run` subcommand generates experiment IDs with `run_` prefix (e.g., `run_20260307_143022`), so files are `experiment_run_20260307_143022.json`.
- **Per-dish result schema divergence**: The `run` subcommand transforms results into `{dish_id, success, mae, latency, turns, complexity_breakdown, complexity_score}` (cli.py:249-269). The `experiment` subcommand (via `PromptOptimizer`) stores raw oracle results `{dish_id, success, turns, final_data, complexity_breakdown, ...}`. The `compare` subcommand must handle both schemas.
- Checkpointing already exists: `load_checkpoint`/`save_checkpoint` in `cli.py:30-49`, saves every `batch_size` items. Metadata currently stores `{seed, complexity, batch_size}` — no `mode` key.
- Stratification via `StratificationEngine.classify()` using weighted 4-factor analysis
- No TNR/TPR calculation in metrics.py — only MAE, latency, and complexity aggregation
- No per-stratum MAE split — `aggregate_mae()` doesn't group by complexity (but `LatencyTracker` does)
- **`within_10_pct_*` fields always 0.0**: `AggregateMAE` has `within_10_pct_calories`, `within_10_pct_protein` etc. fields that are never populated — always 0.0. Not blocking but should be noted as a known limitation or fixed in a follow-up.
- **`vars(args)` leaks password**: In `cli.py:285`, `vars(args)` is persisted to the experiment JSON config dict. This includes the `--password` argument value. Must filter sensitive keys before persisting.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `backend/app/benchmarking/oracle_runner.py` | Main runner — `run_dish()` (line 53), `_process_loop()` (line 104), `stream_payload` (line 124), clarification extraction (line 172), `_submit_answer` (line 241) |
| `backend/app/agent/routing.py` | `route_by_confidence()` consumes `force_finalize`/`force_clarify` (lines 29-36). `force_finalize` checked before mandatory/clinical (line 33) |
| `backend/app/schemas/stream.py` | `StreamAnalysisRequest` with force flags (lines 23-24) |
| `backend/app/schemas/sse.py` | `AgentResponse` — missing complexity fields (lines 20-25). `AgentClarification` — `questions` list (lines 46-57) |
| `backend/app/api/v1/endpoints/stream.py` | `event_generator()` — copies force flags to initial_state (lines 62-63), builds final SSE payload (lines 92-100), server-side `PROCESSING_TIMEOUT = 120` (line 24) |
| `backend/app/agent/graph.py` | `run_streaming_agent()` — stream lifecycle. Semantic gatekeeper at lines 117-122, stream terminates after clarification at lines 132-134 (`yield state; return`), `route_by_confidence` at line 140 (AFTER gatekeeper) |
| `backend/app/agent/nodes.py` | `_enrich_with_complexity()` (line 84), analysis state dict yield with complexity at lines 417-426, `finalize_log_streaming` emits first `AgentResponse` (lines 928-935, does NOT include complexity — must read from accumulated state) |
| `backend/app/agent/state.py` | `complexity_breakdown` is typed as `ComplexityBreakdown` Pydantic model in state |
| `backend/app/schemas/analysis.py` | `ComplexityBreakdown` model (line 41), `AnalysisResult` (line 51), `ClarifyRequest` (line 101) |
| `backend/app/api/v1/endpoints/analysis.py` | Clarify endpoint expects `ClarifyRequest` (line 59-62) |
| `backend/app/services/complexity_calculator.py` | `calculate_complexity()` — deterministic scoring engine |
| `backend/app/benchmarking/stratification.py` | `StratificationEngine.classify()` |
| `backend/app/benchmarking/metrics.py` | `MetricsCalculator` (line 123), `ComplexityMetrics` (line 301), `LatencyTracker` (line 321) |
| `backend/app/benchmarking/experiment_log.py` | `ExperimentLog` (line 18), `ExperimentResult` dataclass (line 8) |
| `backend/app/benchmarking/cli.py` | CLI with `run`/`experiment`/`history`/`optimize` subcommands, checkpoint logic. `run` prefixes experiment IDs with `run_` (line 279) |
| `backend/app/benchmarking/nutrition5k_loader.py` | `Nutrition5kLoader.load_dishes()` — loads from two cafe CSVs, stratifies at parse time |
| `backend/app/benchmarking/prompt_optimizer.py` | `PromptOptimizer` — creates own `OracleRunner` (line 26) without `mode`. Used by `experiment` subcommand. |
| `backend/app/agent/ampm_nodes.py` | `detail_cycle_streaming()` — generates clarification questions, filters via `_item_already_asked` |
| `backend/tests/benchmarking/test_runner.py` | Existing runner tests — constructs `OracleRunner` without `mode` (line 36), asserts old `_submit_answer` payload shape (line 140) |

### Technical Decisions

- Reuse existing `force_finalize`/`force_clarify` infrastructure rather than building separate runner classes
- Fix complexity pipeline at BOTH emission sites (`finalize_log_streaming` in nodes.py AND `event_generator` in stream.py) — always call `.model_dump()` on `ComplexityBreakdown` before passing to `AgentResponse`
- Fix `_submit_answer` payload to match `ClarifyRequest` schema before adding modes
- Fix clarification question extraction to read from `questions[0].question` instead of `question`
- Enhance existing checkpointing with per-dish saves (atomic write via temp+rename) and retry logic
- Add per-stratum MAE to existing `MetricsCalculator` rather than creating a new class
- Mode is a runner-level parameter stored in experiment config for reproducibility
- Checkpoint resume must validate that `--seed`, `--complexity`, `--mode` match the original run
- Do NOT add `--mode` to `exp_parser` — `PromptOptimizer` doesn't support it and a silently-ignored flag is worse than no flag
- `PROCESSING_TIMEOUT` change from 120→180 affects all users (including frontend). Acceptable trade-off — 60s additional wait on timeout is low-risk and prevents premature server-side kills on complex dishes.
- Restructure `_process_loop` into a reconnection loop — after each clarification event, submit answer via clarify endpoint, then POST a NEW stream request (with `log_id`) to continue. Loop until `agent.response` is received.
- Handle semantic gatekeeper in single-shot mode — if a clarification event arrives despite `force_finalize`, auto-answer it (the oracle can answer) and reconnect. Log a warning that the semantic gatekeeper fired in single-shot mode. Do NOT skip the clarification — the gatekeeper exists for food-safety reasons and the agent needs the answer to produce valid results.
- Filter `password` from `vars(args)` before persisting experiment config to JSON
- `compare` subcommand must validate `seed`, `limit`, AND `complexity` across experiments (not just `seed`)
- N=500 workflow requires 6 CLI invocations (3 modes × 2 strata), producing 6 experiment result files. The `compare` subcommand expects 3 experiment IDs (one per mode) — must handle per-stratum experiment files or require users to run without `--complexity` filter (all strata in one run). Decision: require runs WITHOUT `--complexity` filter for compare. Per-stratum MAE is computed from the full mixed dataset.
- `compare` must handle schema divergence: `run` results have pre-computed `mae` key, `experiment` results have `final_data`. For `experiment` results, recompute MAE from `final_data` against ground truth.

## Implementation Plan

### Tasks

Tasks are ordered by dependency — lowest-level fixes first, then features, then consumers.

#### Pre-requisite Fixes (blocking all modes)

- [x] Task 1: Fix `AgentResponse` SSE schema to include complexity fields
  - File: `backend/app/schemas/sse.py`
  - Action: Add `complexity_breakdown: dict[str, Any] | None = Field(None)` and `complexity_score: float | None = Field(None)` to `AgentResponse` model (after line 25). Add `Any` to the `typing` import at line 4.
  - Notes: Use `dict[str, Any]` not the Pydantic model, since the SSE consumer (OracleRunner) expects raw dict. Keep existing fields unchanged. The frontend will ignore unknown fields (AgentResponse is serialized to JSON in SSE events and the frontend only destructures what it needs), so this is backwards-compatible.

- [x] Task 2: Wire complexity data into BOTH `AgentResponse` emission sites
  - File 1: `backend/app/api/v1/endpoints/stream.py`
  - Action: Add `final_complexity_breakdown = None` and `final_complexity_score = None` variables alongside `final_nutritional_data` (line 67). In the state dict capture block (line 88), also extract `complexity_breakdown` and `complexity_score`. **CRITICAL**: Convert `complexity_breakdown` to dict before passing to `AgentResponse`: `cb = item.get("complexity_breakdown"); final_complexity_breakdown = cb.model_dump() if hasattr(cb, 'model_dump') else cb`. Pass both into the `AgentResponse` constructor at lines 92-100.
  - File 2: `backend/app/agent/nodes.py`
  - Action: In `finalize_log_streaming()` at lines 928-935, add `complexity_breakdown` and `complexity_score` from the state to the `AgentResponse` constructor. **CRITICAL**: Convert to dict first: `cb = state.get("complexity_breakdown"); complexity_dict = cb.model_dump() if hasattr(cb, 'model_dump') else cb`. Pass `complexity_breakdown=complexity_dict` and `complexity_score=state.get("complexity_score")` to `AgentResponse`.
  - Notes: The OracleRunner receives whichever `AgentResponse` arrives first and `break`s. Both sites must include complexity data. The `finalize_log_streaming` emission arrives first in practice. Without `.model_dump()`, Pydantic v2 validation will raise a `ValidationError` because `ComplexityBreakdown` is not a `dict`.

- [x] Task 3: Fix `_submit_answer` payload format
  - File: `backend/app/benchmarking/oracle_runner.py`
  - Action: In `_submit_answer()` (line 244), change the payload from `{"response": answer, "is_voice": False}` to `{"responses": [{"response": answer, "is_voice": False}]}` to match the `ClarifyRequest` schema expected by the clarify endpoint (`analysis.py:59-62`).
  - Notes: This is a pre-existing bug. Without this fix, clarification answer submission fails silently, meaning the agentic and naive-always-ask modes cannot function correctly.

- [x] Task 4: Await `_submit_answer` instead of fire-and-forget
  - File: `backend/app/benchmarking/oracle_runner.py`
  - Action: At line 197, change `asyncio.create_task(self._submit_answer(...))` to `await self._submit_answer(...)`. This ensures the clarification answer is confirmed received by the server before the OracleRunner processes the next SSE event.
  - Notes: For scientific validity of the three-mode comparison, the agent must have the answer context before re-running analysis. Fire-and-forget creates a race condition where the agent may re-analyze without the answer.

- [x] Task 5: Fix clarification question extraction
  - File: `backend/app/benchmarking/oracle_runner.py`
  - Action: At line 172 in `_process_loop()`, change `question = data.get("question", "")` to extract from the `questions` list in the `AgentClarification` payload. The payload structure is `{"questions": [{"item_name": "...", "question": "...", "options": [...]}], "context": {...}, "log_id": "..."}`. Extract: `questions_list = data.get("questions", []); question = questions_list[0]["question"] if questions_list else ""`. Also update the `clarification_history` append (line 187-194) to capture all questions if multiple are present.
  - Notes: Without this fix, `QuestionParser.parse()` receives an empty string and `lookup_answer()` returns a generic dish summary for every question, degrading the oracle's ability to provide targeted answers. This undermines the scientific validity of all clarification modes.

- [x] Task 6: Update existing tests for Tasks 3-5 and fix SSE mock format
  - File: `backend/tests/benchmarking/test_runner.py`
  - Action:
    1. Update the `_submit_answer` payload assertion at line 140 from `kwargs["json"]["response"]` to `kwargs["json"]["responses"][0]["response"]`.
    2. Add test case for clarification question extraction from `questions` list payload.
    3. Verify `_submit_answer` is awaited (not fire-and-forget).
    4. **Fix SSE mock format**: The existing test mocks use separate `event:` and `data:` lines (HTTP SSE format), but the actual server emits a single `data:` line containing a JSON wrapper with `{"event": "...", "data": {...}}`. Update all mock SSE data to match the actual server format. Verify by cross-referencing with `stream.py`'s `format_sse()` output.
  - Notes: Existing test will break after Task 3 changes the payload format. The mock format fix is critical — tests that pass with the wrong mock format give false confidence.

#### Stream Architecture Fix (blocking clarification modes)

- [x] Task 7: Restructure `_process_loop` into reconnection loop
  - File: `backend/app/benchmarking/oracle_runner.py`
  - Action: The current `_process_loop` assumes a single persistent SSE stream for multi-turn clarification. This is architecturally broken — the server terminates the stream after each clarification event (`graph.py:132-134`). Restructure as follows:
    1. Wrap the SSE stream consumption in an outer loop: `while not done:`
    2. Each iteration opens a NEW httpx async stream to `/api/v1/analysis/stream`
    3. On `agent.response` event: extract result, set `done = True`, break inner loop
    4. On `agent.clarification` event: extract question(s), generate oracle answer, `await self._submit_answer(log_id, answer)`, then continue outer loop (opens new stream with same `log_id` to continue conversation)
    5. On `agent.error` event: record failure, set `done = True`, break
    6. The first iteration sends the initial `stream_payload` (with image, force flags, etc.). Subsequent iterations send a continuation payload with `log_id` to resume the conversation after clarification.
    7. Track `turn_count` across reconnections (not per-stream).
    8. Add `max_reconnections: int = 10` safety limit to prevent infinite loops.
  - Notes: This is the most critical architectural change. Without it, `agentic` and `naive-always-ask` modes cannot complete multi-turn clarification. The `single-shot` mode may also need reconnection if the semantic gatekeeper fires (see Task 8).

- [x] Task 8: Handle semantic gatekeeper in single-shot mode
  - File: `backend/app/benchmarking/oracle_runner.py`
  - Action: The semantic gatekeeper (`graph.py:117-122`) runs BEFORE `route_by_confidence` (`graph.py:140`) and can emit clarification events even when `force_finalize=True`. In single-shot mode, if an `agent.clarification` event is received:
    1. Log a warning: `"Semantic gatekeeper fired in single-shot mode for dish {dish_id} — auto-answering"`
    2. Use the oracle to generate an answer (same as other modes)
    3. Submit the answer and reconnect (via Task 7's reconnection loop)
    4. The reconnected stream should still have `force_finalize=True`, so after the gatekeeper is satisfied, `route_by_confidence` will finalize.
    5. Track these events in per-dish results as `semantic_gatekeeper_fired: true` for analysis.
  - Notes: Do NOT skip the clarification or suppress the gatekeeper — it exists for food-safety reasons (e.g., ambiguous items that could be allergens). The agent needs the answer to produce valid nutritional estimates.

#### Core Feature: Multi-Mode Runner

- [x] Task 9: Add `mode` parameter to OracleRunner
  - File: `backend/app/benchmarking/oracle_runner.py`
  - Action: Add `mode: str = "agentic"` parameter to `__init__()` (line 19). Store as `self.mode`. Validate mode in `__init__` — raise `ValueError` if not one of `{"agentic", "single-shot", "naive-always-ask"}`. In the reconnection loop (Task 7), add `force_finalize` and `force_clarify` to the initial `stream_payload` based on mode:
    - `"agentic"`: both `False` (default behavior)
    - `"single-shot"`: `force_finalize=True`, `force_clarify=False`
    - `"naive-always-ask"`: `force_finalize=False`, `force_clarify=True`
  - Notes: Single-shot mode handles clarification events via Task 8 (semantic gatekeeper). For `naive-always-ask` mode, log a warning if a dish completes with 0 turns (see Codebase Patterns note on `force_clarify` limitation). Note: `single-shot` mode bypasses `mandatory_clarification` and clinical threshold routing (by design — we're measuring raw single-shot accuracy).

- [x] Task 10: Add `--mode` CLI flag to `run` subcommand only
  - File: `backend/app/benchmarking/cli.py`
  - Action: Add `--mode` argument to `bench_parser` (after `--resume`, around line 329) with `choices=["agentic", "single-shot", "naive-always-ask"]` and `default="agentic"`. Pass `args.mode` to `OracleRunner()` constructor at line 152. Include `mode` in checkpoint metadata dict (line 207). Filter `password` from `vars(args)` before persisting to experiment config: `config = {k: v for k, v in vars(args).items() if k != "password"}` (line 285).
  - Notes: Do NOT add `--mode` to `exp_parser`. The `experiment` subcommand uses `PromptOptimizer` which creates its own `OracleRunner` without `mode` support. Adding a silently-ignored flag is misleading. Mode support for `experiment` is deferred (see Out of Scope).

#### Long-Run Infrastructure

- [x] Task 11: Per-dish checkpoint saves with atomic writes and retry logic
  - File: `backend/app/benchmarking/cli.py`
  - Action:
    1. Change `save_checkpoint()` (line 44) to use atomic writes: write to `checkpoint_file.with_suffix('.tmp')`, then `os.replace(tmp, checkpoint_file)`. This prevents corruption if the process is killed mid-write.
    2. Move the checkpoint save call from batch-only (line 203) to per-dish: call `save_checkpoint()` after every dish result is appended.
    3. Add retry logic around `runner.run_dish()` at line 182: wrap in a for-loop of `args.retries + 1` attempts. On failure (exception or `result["success"] == False` with a retryable error like timeout/network), `await asyncio.sleep(2 ** attempt)` and retry. Log each retry attempt. After all retries exhausted, record the failure result.
    4. Add `--retries` CLI arg (default 2) to `bench_parser`.
    5. Add a `checkpoint_version: int = 2` field to checkpoint metadata. Version 1 = legacy (no `mode`), version 2 = current.
  - Notes: Keep batch logging for progress reporting — log every `batch_size` items. The `--delay` arg already provides inter-dish throttling.

- [x] Task 12: Add checkpoint resume parameter validation
  - File: `backend/app/benchmarking/cli.py`
  - Action: In `load_checkpoint()`, also return the metadata dict. After loading, check `checkpoint_version`:
    - If version 1 (or missing): warn that checkpoint predates mode support, treat as `mode="agentic"`. If `args.mode != "agentic"`, error out unless `--force-resume` is passed.
    - If version 2+: validate that `metadata["seed"]`, `metadata["complexity"]`, `metadata["mode"]`, `metadata["limit"]` match current `args`. If mismatch, error out unless `--force-resume` is passed.
  - Add `--force-resume` flag to `bench_parser` (default False).
  - Notes: Validates `limit` and `complexity` in addition to `seed` and `mode`. Prevents silent data corruption when resuming with different parameters that would produce a different dish set.

- [x] Task 13: Configurable timeout with server-side alignment
  - File 1: `backend/app/benchmarking/oracle_runner.py`
  - Action: Add `timeout: float = 180.0` parameter to `__init__()`. Use it in `httpx.AsyncClient` constructor (line 31) instead of hardcoded `timeout=120.0`.
  - File 2: `backend/app/benchmarking/cli.py`
  - Action: Add `--timeout` CLI arg to `bench_parser` (default 180). Pass to `OracleRunner()` constructor.
  - File 3: `backend/app/api/v1/endpoints/stream.py`
  - Action: Increase `PROCESSING_TIMEOUT` from 120 to 180 (line 24) to match the client-side default.
  - Notes: Both client and server timeouts must be aligned. The server-side change affects ALL users (including frontend), but 60s additional timeout headroom is low-risk — it only affects how long users wait when a request is genuinely hanging. Normal requests complete in 5-15s regardless.

#### Metrics Extensions

- [x] Task 14: Add per-stratum MAE aggregation
  - File: `backend/app/benchmarking/metrics.py`
  - Action: Add method `aggregate_mae_by_stratum(results: list[DishMAE], dish_complexity_map: dict[str, str]) -> dict[str, AggregateMAE]` to `MetricsCalculator`. Groups results by complexity label ("simple"/"complex"), calls `aggregate_mae()` on each group, returns `{"simple": AggregateMAE, "complex": AggregateMAE}`.
  - Notes: `dish_complexity_map` maps `dish_id` to complexity string ("simple" or "complex"). Caller builds this from `dishes_map` in `cli.py` via `{did: d.complexity for did, d in dishes_map.items()}`. Note: `within_10_pct_*` fields in `AggregateMAE` are always 0.0 (never populated) — this is a known limitation, not addressed in this spec.

- [x] Task 15: Add TNR/TPR calculation
  - File: `backend/app/benchmarking/metrics.py`
  - Action: Add method `calculate_routing_accuracy(per_dish_results: list[dict], dish_complexity_map: dict[str, str]) -> dict[str, float | int]` to `MetricsCalculator`. Classification logic:
    - True Negative (TN): simple dish + 0 turns (correctly suppressed)
    - False Positive (FP): simple dish + >0 turns (unnecessary clarification)
    - True Positive (TP): complex dish + >0 turns (correctly triggered)
    - False Negative (FN): complex dish + 0 turns (missed clarification)
    - TNR = TN / (TN + FP) if (TN + FP) > 0 else 0.0
    - TPR = TP / (TP + FN) if (TP + FN) > 0 else 0.0
  - Return: `{"tnr": float, "tpr": float, "tn": int, "fp": int, "tp": int, "fn": int}`
  - Notes: Only meaningful for `agentic` mode runs. For `single-shot` or `naive-always-ask` modes, skip calculation and return a dict with a `"skipped": True` flag and `"reason"` string.

- [x] Task 16: Add turn-reduction `[Y]%` calculation
  - File: `backend/app/benchmarking/metrics.py`
  - Action: Add method `calculate_turn_reduction(agentic_results: list[dict], naive_results: list[dict]) -> dict[str, float]`. Formula: `Y = (naive_total_turns - agentic_total_turns) / naive_total_turns * 100` if `naive_total_turns > 0`, else return `{"error": "naive baseline has 0 total turns -- cannot compute turn reduction"}`. Return: `{"turn_reduction_pct": float, "agentic_total_turns": int, "naive_total_turns": int}`.
  - Notes: Requires results from agentic and naive-always-ask modes for the same dish set. The `turns` key is present in both `run` and `experiment` result schemas.

#### CLI Integration

- [x] Task 17: Wire per-stratum metrics and routing accuracy into CLI report
  - File: `backend/app/benchmarking/cli.py`
  - Action: After aggregate MAE calculation (around line 272):
    1. Build `dish_complexity_map = {did: d.complexity for did, d in dishes_map.items()}`
    2. Call `stratum_mae = metrics_calc.aggregate_mae_by_stratum(mae_results, dish_complexity_map)`
    3. Call `routing_acc = metrics_calc.calculate_routing_accuracy(per_dish_results, dish_complexity_map)` (only if `args.mode == "agentic"`)
    4. Add both to `final_result.metrics` dict under keys `"stratum_mae"` (serialize each `AggregateMAE` via `.to_dict()`) and `"routing_accuracy"`
    5. Print per-stratum MAE and TNR/TPR in the report section (after line 300)
  - Notes: For non-agentic modes, skip routing accuracy and print a note explaining why.

- [x] Task 18: Add `compare` CLI subcommand for cross-mode analysis
  - File: `backend/app/benchmarking/cli.py`
  - Action: Add `compare` subparser with three required args: `--agentic-id`, `--single-shot-id`, `--naive-id` (all `required=True`). Implementation:
    1. Load per-dish results from each experiment JSON file in `benchmark_output/`. File path: `benchmark_output/experiment_{id}.json` (note: `run` subcommand IDs have `run_` prefix, e.g., `--agentic-id run_20260307_143022`).
    2. Validate that all experiments used the same `seed`, `limit`, AND `complexity` from their `config` dicts — error if mismatch unless `--force` flag is passed.
    3. Rebuild `dish_complexity_map` by re-loading dishes via `Nutrition5kLoader.load_dishes(seed=config_seed)`. This requires the Nutrition5k dataset to be locally available.
    4. Handle per-dish result schema divergence: normalize both `run` (has `mae` key) and `experiment` (has `final_data` key) schemas to extract `turns` and compute MAE. For `experiment` results, recompute MAE from `final_data` against ground truth (loaded from `dishes_map`). The `turns` key is present in both.
    5. Call `metrics_calc.calculate_turn_reduction(agentic_results, naive_results)`
    6. For each mode, compute per-stratum MAE
    7. Print comparison table: mode | simple MAE | complex MAE | total MAE | total turns
    8. Print TNR/TPR for agentic mode and turn-reduction `[Y]%`
  - Notes: All three `--*-id` flags are required. If partial comparison is needed (e.g., only agentic vs single-shot), that's a future enhancement. N=500 workflow: run 3 invocations (one per mode) WITHOUT `--complexity` filter, each producing 1000 dishes (500 simple + 500 complex). Per-stratum MAE is computed from the full mixed dataset by the compare command.

### Acceptance Criteria

- [x] AC 1: Given a benchmark run with `--mode single-shot`, when the agent processes a dish, then `force_finalize=True` is sent in the SSE stream payload and the agent returns a result with 0 clarification turns (unless the semantic gatekeeper fires — see AC 12).

- [x] AC 2: Given a benchmark run with `--mode naive-always-ask`, when the agent processes a dish, then `force_clarify=True` is sent in the SSE stream payload and the agent enters the clarification subgraph. If a dish unexpectedly completes with 0 turns (due to `_item_already_asked` filtering), the runner logs a warning including the dish_id.

- [x] AC 3: Given a benchmark run with `--mode agentic` (default), when the agent processes a dish, then neither force flag is set and routing follows normal confidence/complexity logic.

- [x] AC 4: Given a benchmark run of any mode, when the agent completes analysis, then the SSE `agent.response` event payload (from whichever emission site — `finalize_log_streaming` or `event_generator`) includes `complexity_breakdown` (dict with `score`, `dominant_factor`, `levels`, `weights`) and `complexity_score` (float), and the OracleRunner extracts both into per-dish results.

- [x] AC 5: Given a benchmark run with `--mode agentic` on a mixed simple+complex dataset, when the run completes, then the report includes per-stratum MAE (separate simple/complex calorie MAE) and routing accuracy (TNR, TPR with confusion matrix counts).

- [x] AC 6: Given a long benchmark run (N>=100), when a dish fails (network error, timeout), then the runner retries up to `--retries` times with exponential backoff (2s, 4s) before recording a failure, and all previously completed results are preserved in the checkpoint file via atomic writes.

- [x] AC 7: Given a long benchmark run is interrupted (Ctrl+C, crash), when the run is resumed with `--resume`, then previously processed dishes are skipped, checkpoint parameter validation errors if `--seed`/`--complexity`/`--mode` differ from the original run (unless `--force-resume`), and the run continues from where it left off.

- [x] AC 8: Given three completed experiments (agentic, single-shot, naive-always-ask) with the same seed and dish set, when `compare --agentic-id X --single-shot-id Y --naive-id Z` is run, then the output includes turn-reduction `[Y]%` and a per-stratum MAE comparison table.

- [x] AC 9: Given `--mode single-shot` is used, when the routing accuracy is calculated, then the calculation is skipped with a log message explaining it's only meaningful for agentic mode, and the metrics dict includes `{"skipped": true, "reason": "..."}`.

- [x] AC 10: Given the OracleRunner submits a clarification answer via `_submit_answer`, when the clarify endpoint processes it, then the payload matches the `ClarifyRequest` schema (`{"responses": [{"response": "...", "is_voice": false}]}`), the call is awaited (not fire-and-forget), and the next SSE event is only processed after confirmation.

- [x] AC 11: Given the OracleRunner receives an `agent.clarification` SSE event, when extracting the question, then it reads from `data["questions"][0]["question"]` (not `data["question"]`), and `QuestionParser` receives the actual question text for targeted oracle answering.

- [x] AC 12: Given a benchmark run in any mode where the semantic gatekeeper fires (emitting an `agent.clarification` event before `route_by_confidence`), when the OracleRunner detects the clarification, then it auto-answers via the oracle, submits the answer to the clarify endpoint, opens a NEW SSE stream (with `log_id`) to continue, and the per-dish result includes `semantic_gatekeeper_fired: true`. In single-shot mode, a warning is logged.

- [x] AC 13: Given a benchmark run in `agentic` or `naive-always-ask` mode where multi-turn clarification occurs, when the SSE stream terminates after a clarification event, then the OracleRunner submits the answer, opens a NEW SSE stream with the `log_id` to continue the conversation, and repeats until an `agent.response` event is received or `max_reconnections` (10) is reached.

## Additional Context

### Dependencies

- Nutrition5k dataset must have >= 500 dishes per stratum available (verify with `Nutrition5kLoader.load_dishes(complexity="simple")` and `complexity="complex"` without limit)
- Nutrition5k dataset must also be locally available for `compare` subcommand to rebuild `dish_complexity_map`
- Backend services (FastAPI + Supabase) must be running for OracleRunner SSE streaming
- Supabase auth required for OracleRunner login (TEST_EMAIL / TEST_PASSWORD env vars)
- No new Python packages required — all changes use existing dependencies

### Testing Strategy

**Unit Tests (existing files to update):**
- `backend/tests/benchmarking/test_runner.py`: Update `_submit_answer` payload assertion (line 140) for new `ClarifyRequest` format. Add test for clarification question extraction from `questions` list. Add test for mode parameter validation. Add test that `stream_payload` includes correct force flags for each mode. Verify `_submit_answer` is awaited. Fix SSE mock data format to match actual server output. Add tests for reconnection loop: mock a clarification→reconnect→response sequence. Add test for semantic gatekeeper handling in single-shot mode (clarification despite force_finalize). Add test for `max_reconnections` safety limit.
- `backend/tests/benchmarking/test_metrics.py`: Add tests for `aggregate_mae_by_stratum()` with mock dish data split across simple/complex. Add tests for `calculate_routing_accuracy()` with known TN/FP/TP/FN counts, including edge case where all dishes are same stratum. Add tests for `calculate_turn_reduction()` with mock cross-mode results, including edge case where `naive_total_turns` is 0.

**Unit Tests (new files to create):**
- `backend/tests/schemas/test_sse.py` (or add to existing schema tests): Test that `AgentResponse` serializes correctly with complexity fields present (as dict) and absent (None). Verify backwards compatibility — existing consumers that don't use complexity fields should not break.

**Integration Tests:**
- Verify end-to-end: run a small benchmark (N=3) in each mode and confirm force flags reach routing, complexity data appears in results, and per-stratum metrics are calculated.
- Verify clarification answer submission works end-to-end with the fixed `ClarifyRequest` payload format.
- Verify reconnection loop: run agentic mode on a dish that triggers clarification, confirm the runner reconnects and completes.

**Manual Verification:**
- Run N=5 per mode on simple stratum, confirm single-shot has 0 turns, naive-always-ask enters clarification subgraph for all dishes, agentic has mixed turns.
- Verify checkpoint file uses atomic writes (kill process mid-run, confirm checkpoint is not corrupted).
- Verify checkpoint resume validates matching parameters and errors on mismatch.

### Notes

- Turn-reduction formula: `[Y]% = (naive_total_turns - agentic_total_turns) / naive_total_turns * 100`
- N=500 means 500 per stratum (simple + complex), so 1000 total dishes per mode, 3000 total across all modes. Workflow: 3 CLI invocations (one per mode) WITHOUT `--complexity` filter. Per-stratum MAE is computed from the full mixed dataset by the `compare` command.
- complexity_breakdown dual emission root cause: `finalize_log_streaming` emits the first `AgentResponse` (which OracleRunner reads and breaks on), `event_generator` emits a second one. Both must include complexity data. Both must call `.model_dump()` on the `ComplexityBreakdown` Pydantic model.
- Risk: N=500 runs will take significant time (~7-14 hours per mode at ~10s/dish average). Robust checkpointing is critical.
- Risk: LLM API rate limits may cause failures during long runs — retry logic with backoff mitigates this.
- Risk: `force_clarify` does not guarantee >0 turns for every dish due to `_item_already_asked` filtering in `ampm_nodes.py`. The "naive-always-ask" baseline may have some 0-turn dishes. This should be logged and reported in metrics but is acceptable for the thesis — the baseline represents "always attempt clarification" not "always succeed at clarification."
- `experiment` CLI subcommand mode support is deferred — `PromptOptimizer` creates its own `OracleRunner` without `mode` and stores per-dish results in a different schema. Wiring mode through `PromptOptimizer` is a separate task. Note: `PromptOptimizer.suggest_improvements()` may access non-existent keys on experiment results — this is a pre-existing issue, not addressed here.
- `single-shot` mode bypasses `mandatory_clarification` and clinical threshold routing in `route_by_confidence()` — this is by design for benchmarking (measuring raw single-shot VLM accuracy without any safety routing). However, the semantic gatekeeper CAN still fire (see Task 8).
- `PROCESSING_TIMEOUT` increase from 120→180 affects all users. Normal requests complete in 5-15s, so the only observable effect is a longer wait on genuinely hanging requests before timeout error.
- `within_10_pct_*` fields in `AggregateMAE` are always 0.0 (never populated). Known limitation — not addressed in this spec.
- `vars(args)` password leak: filtered in Task 10 before persisting experiment config.

## Review Notes

- Adversarial review completed
- Findings: 6 total, 5 fixed, 1 skipped
  - **F1 (fixed):** `_submit_answer` silently swallowed exceptions — removed try/except, errors now propagate
  - **F2 (fixed):** Multi-question clarifications only parsed first question — now iterates all questions individually, renamed to `_submit_answers`
  - **F3 (fixed):** `calculate_routing_accuracy` counted failed dishes as routing decisions — added `success` filter
  - **F4 (fixed):** `_run_compare` silently skipped missing dishes — added warning log
  - **F5 (skipped):** Server already uses `log_id` for conversation state; no client-side reconnect token needed
  - **F6 (fixed):** Empty checkpoint metadata `{}` is falsy, bypassing validation — changed to `is not None` check
- Resolution approach: auto-fix
- All 47 tests pass, ruff lint clean
