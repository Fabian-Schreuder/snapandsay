---
title: 'Benchmarking Integrity & Metrics Accuracy'
slug: 'benchmarking-integrity-metrics-accuracy'
created: '2026-03-09'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.12', 'FastAPI 0.115+', 'SQLAlchemy 2.0 (Async)', 'Supabase PostgreSQL 15+', 'LangGraph 1.0+', 'Pydantic v2', 'asyncpg']
files_to_modify:
  - 'backend/app/schemas/analysis.py'
  - 'backend/app/benchmarking/metrics.py'
  - 'backend/app/benchmarking/cli.py'
  - 'backend/app/benchmarking/oracle_runner.py'
  - 'backend/app/agent/routing.py'
  - 'backend/app/agent/constants.py'
  - 'backend/app/schemas/stream.py'
  - 'supabase/migrations/20260309124343_add_missing_columns.sql'
  - 'backend/tests/benchmarking/test_metrics.py'
  - 'backend/tests/agent/test_routing.py'
code_patterns:
  - 'Pydantic v2 dataclasses for metrics (DishMAE, AggregateMAE, ComplexityMetrics, AggregateLatency)'
  - 'statistics module for aggregation (mean, stdev)'
  - 'Async SQLAlchemy with NullPool for DB operations'
  - 'SSE streaming for agent communication'
  - 'Checkpoint-based resumable benchmark runs (JSON atomic writes)'
  - 'Deterministic seeded sampling via random.Random(seed)'
test_patterns:
  - 'Pytest with asyncio_mode=auto'
  - 'Tests in backend/tests/benchmarking/ mirroring app structure'
  - 'Tests in backend/tests/services/ and backend/tests/agent/'
  - 'Unit tests for metrics calculations, routing logic, complexity calculator'
  - 'Integration tests for complexity enrichment pipeline'
---

# Tech-Spec: Benchmarking Integrity & Metrics Accuracy

**Created:** 2026-03-09

## Overview

### Problem Statement

Benchmark results are unreliable and cannot support thesis claims. Three root issues:
1. **DB schema bug** — `clarification_count` column referenced in `models/log.py` doesn't exist in the database, causing 22% of dishes (11/50) to fail deterministically before the agent even processes them. This inflates failure rates and reduces effective sample size.
2. **Misleading complexity scale** — `analysis.py` documents `complexity_score` as 0.0-1.0, but the deterministic calculator (`C = Σ(w·L²) + P_sem`) produces unbounded values (0-32 theoretical max). Mean scores of 3.6-3.9 look wrong on a 0-1 scale but are valid on the actual scale. This creates confusion in metrics reporting.
3. **Insufficient sample size** — N=50 (with only 37-39 successes) is far below the N=500 thesis claim, and only 4 complex dishes make stratum comparisons statistically meaningless.

Additional concerns:
- Agentic mode underperforms single-shot (MAE 82.0 vs 56.8 kcal) — opposite of thesis claims
- TNR=54.3% vs claimed 92% — ~46% false positive rate on clarification triggering
- Latency 3-6x higher than claimed (21-43s vs 7.1s)

### Solution

Phase A (measurement fix): Fix the DB schema mismatch to eliminate deterministic failures, normalize or properly document complexity scales, improve metrics reporting with clear scale labeling, and scale to N=500 with proper statistical reporting (confidence intervals, effect sizes).

Phase B (system tuning): Investigate and tune the complexity threshold (currently 15.0) to reduce false positive clarification triggers, and investigate why agentic clarifications hurt accuracy on simple dishes.

### Scope

**In Scope:**
- DB migration to add `clarification_count` column to `dietary_logs` table
- Complexity score documentation fix or normalization in `analysis.py` and `complexity_calculator.py`
- Metrics reporting improvements (scale labels, confidence intervals, effect sizes)
- N=500 benchmark scaling (dataset loading, runner robustness, timeout handling)
- Threshold tuning investigation for complexity routing (Phase B)
- Analysis of why agentic mode degrades simple dish accuracy (Phase B)

**Out of Scope:**
- Agent architecture changes (graph structure, node logic)
- New food class categories in the registry
- Frontend changes
- Deployment pipeline changes
- Thesis document writing/editing

## Context for Development

### Codebase Patterns

- Database schema managed by Supabase migrations, NOT SQLAlchemy `metadata.create_all`
- Two independent complexity systems that MUST NOT be confused:
  - **Stratification** (`stratification.py`): 0-1 weighted average of 4 factors, threshold ≥0.5 = "complex". Used for benchmarking ground truth classification only.
  - **Deterministic calculator** (`complexity_calculator.py`): `C = Σ(w_d · L_d²) + P_sem`, unbounded (0-~21.1 practical max). Used by agent at runtime for routing decisions.
- Benchmarking runner has 3 modes via `force_finalize`/`force_clarify` flags:
  - `agentic`: both False — agent decides via `route_by_confidence`
  - `single-shot`: `force_finalize=True` — bypasses all clarification
  - `naive-always-ask`: `force_clarify=True` — always triggers AMPM
- TNR/TPR metrics correctly use stratification string labels ("simple"/"complex"), not agent scores
- Agent routing decision tree (priority order): forced outcomes → safety cap (MAX_CLARIFICATIONS=2) → mandatory flag → clinical threshold (score > 15.0) → confidence gate (≥0.85) → default: AMPM_ENTRY
- Checkpoint-based resumable runs with atomic JSON writes and parameter validation on resume
- Metrics are purely descriptive (mean ± stdev) — no inferential statistics currently

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `backend/app/models/log.py:58` | DietaryLog model — `clarification_count` column definition |
| `backend/app/api/v1/endpoints/analysis.py:40-50` | Upload endpoint — INSERT fails at `db.commit()` due to missing column |
| `backend/app/schemas/analysis.py:48,69-75` | `ComplexityBreakdown.score` and `complexity_score` — documented as 0-1, actually unbounded |
| `backend/app/services/complexity_calculator.py:5-55` | Deterministic formula implementation — no normalization |
| `backend/app/benchmarking/metrics.py:129-164` | `calculate_dish_mae()` — per-dish MAE against Nutrition5K ground truth |
| `backend/app/benchmarking/metrics.py:166-201` | `aggregate_mae()` — mean + stdev, no CI or effect size |
| `backend/app/benchmarking/metrics.py:274-310` | `calculate_routing_accuracy()` — TNR/TPR based on turns > 0 |
| `backend/app/benchmarking/metrics.py:339-382` | `aggregate_complexity()` — reports unbounded scores without scale label |
| `backend/app/benchmarking/stratification.py:220-227` | `classify()` — 4-factor weighted classification, threshold ≥0.5 |
| `backend/app/benchmarking/oracle_runner.py:67-116` | `run_dish()` — image upload, SSE streaming, timing |
| `backend/app/benchmarking/cli.py:236-262` | Retry loop — retryable keywords: timeout/connection/network |
| `backend/app/benchmarking/cli.py:299-350` | Per-dish result assembly and metrics aggregation |
| `backend/app/benchmarking/nutrition5k_loader.py:18-60` | `load_dishes()` — ~5,004 dishes available, stratified sampling |
| `backend/app/agent/routing.py:12-59` | `route_by_confidence()` — full decision tree |
| `backend/app/agent/nodes.py:84-128` | `_enrich_with_complexity()` — LLM → registry → deterministic calc |
| `backend/app/agent/ampm_nodes.py:61-73` | Low-confidence item selection — returns ALL items if mandatory/score>threshold |
| `backend/app/agent/constants.py:78-80` | `CONFIDENCE_THRESHOLD=0.85`, `MAX_CLARIFICATIONS=2`, `CLARIFICATION_TIMEOUT_SECONDS=30` |
| `backend/app/agent/data/food_class_registry.yaml` | 3 mandatory-clarification classes: meat_analogue (P=4.0), dairy_analogue (P=3.5), stealth_carb (P=3.0) |
| `supabase/migrations/20260309124343_add_missing_columns.sql` | Migration fix — adds `clarification_count` + `ampm_data` columns |
| `backend/tests/benchmarking/test_metrics.py` | Comprehensive metric calculation tests |
| `backend/tests/agent/test_routing.py` | Routing decision tree tests (18 tests) |
| `backend/tests/services/test_complexity_calculator.py` | Calculator formula tests (5 tests) |

### Technical Decisions

- Complexity score remains on the unbounded scale (the formula `C = Σ(w·L²) + P` is intentional and thesis-documented) — fix documentation in `analysis.py` to reflect actual range
- DB migration already exists (`20260309124343`), needs to be verified as applied
- Metrics module needs 95% confidence intervals (`mean ± 1.96 * SE`) and Cohen's d for cross-mode comparisons
- N=500 scaling is feasible (~10% of dataset) — CLI default is 250 (`--limit`), so N=500 must be passed explicitly via `--limit 500`
- Timeout failures (1-2%) need better retry handling — current retry only catches keyword-matched errors
- TNR false positive problem (54% vs 92%) likely caused by routing default fallback: confidence < 0.85 → AMPM_ENTRY even for simple dishes that don't benefit from clarification

## Implementation Plan

### Phase A: Measurement Integrity

#### Story A1: Fix DB Schema & Eliminate Deterministic Failures

- [x] Task 1: Verify and apply the Supabase migration
  - File: `supabase/migrations/20260309124343_add_missing_columns.sql`
  - Action: Apply the pending migration using `supabase migration up` (NOT `supabase db push` — `db push` compares full schemas and can be destructive). This applies pending migration files sequentially. The migration adds `clarification_count INTEGER NOT NULL DEFAULT 0` and `ampm_data JSONB` to `dietary_logs`.
  - Notes: Verify the migration exists and is correct. Confirm the column types match `models/log.py:58-59`. The `NOT NULL DEFAULT 0` is safe for existing rows — PostgreSQL backfills the default. After applying, run a smoke test: upload a single dish through `/api/v1/analysis/upload` and confirm the INSERT succeeds. If using a remote Supabase instance, run `supabase db push --linked` instead, but verify the diff preview before confirming.

- [ ] Task 2: Validate the 11 previously-failing dishes now succeed
  - File: `backend/app/benchmarking/cli.py`
  - Action: First, verify the failing dish IDs by checking the most recent experiment run files in `backend/benchmark_output/experiment_run_*.json` — filter for entries with `"success": false` and error message containing "Er is een fout opgetreden" (the Dutch analysis error from `constants.py:57`). These should be the 11 deterministic failures with latency ~1.2-1.4s and 0 turns. Then run a targeted benchmark with those dish IDs to confirm they now process successfully.
  - Notes: Source of the 11 dish IDs: `backend/benchmark_output/experiment_run_20260309_150700.json` (most recent run) and confirmed consistent across all 3 runs in that directory. If the experiment files have been overwritten, re-derive the list by running N=50 seed=42 and checking for instant failures. If any still fail after migration, the root cause is different from the schema bug and needs separate investigation.

#### Story A2: Fix Complexity Score Documentation

- [x] Task 3: Update all misleading field documentation in schemas
  - File: `backend/app/schemas/analysis.py`
  - Action: Fix three fields with incorrect range documentation:
    1. `complexity_score` (line 69-75): Change from `"Meal complexity from 0.0 (simple, single item) to 1.0 (complex, multi-component)..."` to `"Deterministic meal complexity score (C = Σ(w·L²) + P_sem). Range 0.0-~21.1 depending on food class risk profile. Higher values indicate greater ambiguity requiring clarification. Clinical routing threshold default: 15.0."`
    2. `ComplexityBreakdown.score` (line 48): Change from `"Calculated complexity score (0.0 to 1.0)"` to `"Calculated complexity score (0.0 to ~21.1, unbounded deterministic scale)"`
    3. `ComplexityBreakdown.semantic_penalty` (line 46): Change from `"Penalty for ambiguity (0.0 to 1.0)"` to `"Semantic penalty from food class risk profile (0.0-4.0, see food_class_registry.yaml)"`
  - Notes: All three fields share the same misleading 0-1 documentation. The registry defines penalties up to 4.0 (meat_analogue). Max theoretical score is 21.1 (meat_analogue with all L=3: 0.9×9 + 0.7×9 + 0.3×9 + 4.0)

- [x] Task 4: Update `aggregate_complexity()` to label the scale in output
  - File: `backend/app/benchmarking/metrics.py:339-382`
  - Action: Add a `score_scale` field to `ComplexityMetrics` dataclass (e.g., `score_scale: str = "deterministic_unbounded_0_to_21"`) so metrics output is self-documenting. Add `score_min` and `score_max` fields to track observed range.
  - Notes: This makes it impossible for a reader to misinterpret the scale

#### Story A3: Add Inferential Statistics to Metrics

- [x] Task 5: Add confidence interval calculation utility
  - File: `backend/app/benchmarking/metrics.py`
  - Action: Add a helper function `calculate_ci(values: list[float], confidence: float = 0.95) -> tuple[float, float]` that computes `mean ± z * (stdev / sqrt(n))` where z=1.96 for 95% CI. Use the `statistics` module (already imported).
  - Notes: Return `(ci_lower, ci_upper)`. Handle edge case where n < 2 by returning `(mean, mean)`.

- [x] Task 6: Add Cohen's d effect size calculation
  - File: `backend/app/benchmarking/metrics.py`
  - Action: Add `calculate_cohens_d(group1: list[float], group2: list[float]) -> float | None` using pooled standard deviation formula: `d = (mean1 - mean2) / sqrt(((n1-1)*s1² + (n2-1)*s2²) / (n1+n2-2))`. Handle edge cases:
    - Identical groups → 0.0
    - Zero pooled variance → return `None` (not NaN — NaN breaks JSON serialization)
    - Either group has n < 2 → return `None` (pooled SD undefined with single observation)
    - Highly unequal group sizes (ratio > 2:1) → log a warning that pooled SD may be biased, but still compute (Welch's correction is out of scope for this spec, but the warning alerts the reader)
  - Notes: This enables cross-mode comparison (agentic vs single-shot) with effect size reporting. Minimum recommended sample per group: n ≥ 30 for meaningful interpretation.

- [x] Task 7: Integrate CI into `AggregateMAE` and wire up dead `within_10_pct` fields
  - File: `backend/app/benchmarking/metrics.py:166-201`
  - Action: Two changes:
    1. Extend `AggregateMAE` dataclass with `ci_lower_calories`, `ci_upper_calories` (and same for protein, fat, carbs) fields. Populate them in `aggregate_mae()` using `calculate_ci()`.
    2. The `AggregateMAE` dataclass already has `within_10_pct_calories`, `within_10_pct_protein`, `within_10_pct_fat`, `within_10_pct_carbs` fields (lines 55-59), but `aggregate_mae()` never populates them — they are always 0.0. Wire these up by calling the existing `calculate_within_threshold()` function inside `aggregate_mae()` and assigning the results to these fields.
  - Notes: Keep backward compatibility — new CI fields should have defaults of `None` so existing serialized results don't break. The `within_10_pct` fields already exist with defaults of 0.0, so wiring them up is non-breaking.

- [x] Task 8: Add cross-mode comparison report function
  - File: `backend/app/benchmarking/metrics.py`
  - Action: Add `compare_modes(agentic_results: list[DishMAE], single_shot_results: list[DishMAE]) -> dict` that computes per-macro Cohen's d between the two modes, overall MAE difference with 95% CI, and a plain-text summary.
  - Notes: This is the key function for thesis claims about agentic vs single-shot improvement

- [x] Task 9: Add CI to routing accuracy metrics
  - File: `backend/app/benchmarking/metrics.py:274-310`
  - Action: Add Wilson score interval for TNR and TPR (proportion CI, better than normal approximation for small samples). Add fields `tnr_ci_lower`, `tnr_ci_upper`, `tpr_ci_lower`, `tpr_ci_upper` to routing accuracy output.
  - Notes: Wilson interval formula: `(p + z²/2n ± z*sqrt(p(1-p)/n + z²/4n²)) / (1 + z²/n)` where z=1.96

#### Story A4: Improve Runner Robustness for N=500

- [x] Task 10: Broaden retry logic for transient failures
  - File: `backend/app/benchmarking/cli.py:236-262`
  - Action: Expand retryable error detection beyond keyword matching. Add HTTP status code checks (429, 500, 502, 503, 504) and `asyncio.TimeoutError` as retryable conditions. Increase default retries from 2 to 3 for N=500 runs.
  - Notes: Current retry only catches "timeout", "connection", "network" in error string — misses structured HTTP errors

- [x] Task 11: Add per-dish timeout configuration for both upload and processing phases
  - File: `backend/app/benchmarking/oracle_runner.py:67-116`
  - Action: Add a configurable `dish_timeout_seconds` parameter (default 120s) to `run_dish()`. Apply timeouts to both phases:
    1. **Upload phase** (line 94, `self.client.post(...)`): The `httpx.AsyncClient` has a global timeout (default 180s) which is too generous. Set an explicit `timeout=30` on the upload POST request to fail fast on unresponsive uploads.
    2. **Processing phase** (`_process_loop()`): Wrap the call with `asyncio.wait_for(self._process_loop(...), timeout=dish_timeout_seconds - 30)` to cap total processing time. The remaining budget after upload ensures the total per-dish time stays within `dish_timeout_seconds`.
  - Notes: Current timeout failures show latencies of 200-232s. Without explicit upload timeout, a dish could silently block for 180s on upload alone before the processing timeout even starts.

- [x] Task 12: Add progress reporting for long runs
  - File: `backend/app/benchmarking/cli.py`
  - Action: Add periodic progress logging: every 50 dishes, log `"Progress: {completed}/{total} dishes ({success_rate}% success, elapsed: {elapsed})"`. Also log estimated time remaining based on average per-dish latency.
  - Notes: N=500 runs at ~30s/dish = ~4+ hours. Progress feedback prevents confusion about whether the run is stuck.

#### Story A5: Validate Oracle Quality Before Scaling

- [ ] Task 13: Audit oracle answer quality on a sample
  - File: `backend/app/benchmarking/question_parser.py`
  - Action: Run a mini agentic benchmark (N=50, seed=42) and capture all clarification Q&A pairs from `clarification_history` in the per-dish results. For each Q&A pair, log: the question text, parsed intent, oracle answer, and ground truth ingredient data. Export to a CSV/JSON file (`benchmark_output/oracle_audit.json`). Manually review a sample of 20-30 Q&A pairs to grade oracle answer accuracy (correct / partially correct / wrong / unparseable).
  - Notes: If the oracle gives bad answers, agentic mode benchmarks are measuring oracle quality, not system quality. This must be validated before spending ~12.5 hours of API credits on N=500. If >20% of oracle answers are wrong, the `question_parser.py` regex patterns need fixing before scaling. Common failure modes: unrecognized question formats falling to UNKNOWN intent, missing ingredient lookups, portion size answers that don't match the actual dish.

#### Story A6: Run N=500 Benchmark and Capture Honest Results

- [ ] Task 14: Execute N=500 benchmark across all 3 modes
  - File: `backend/app/benchmarking/cli.py`
  - Action: Run three benchmark executions:
    1. `python -m app.benchmarking.cli benchmark --mode agentic --limit 500 --seed 42`
    2. `python -m app.benchmarking.cli benchmark --mode single-shot --limit 500 --seed 42`
    3. `python -m app.benchmarking.cli benchmark --mode naive-always-ask --limit 500 --seed 42`
  - Notes: Same seed ensures identical dish selection across modes for paired comparison. Checkpoint resumability handles interruptions.

- [ ] Task 15: Generate cross-mode comparison report
  - File: `backend/app/benchmarking/cli.py`
  - Action: After all 3 runs complete, use the new `compare_modes()` function to generate a comparison table with MAE (with 95% CI), Cohen's d effect sizes, TNR/TPR (with Wilson CI), turn reduction %, and latency percentiles. Output as both JSON and markdown.
  - Notes: This is the deliverable — honest, defensible numbers with proper statistical backing

### Phase B: System Tuning (After Phase A Data)

#### Story B1: Investigate and Tune Routing Threshold

- [ ] Task 16: Analyze Phase A data to understand false positive pattern
  - File: `backend/app/benchmarking/metrics.py`
  - Action: Add `analyze_false_positives(per_dish_results: list[dict]) -> dict` that for each FP dish (simple + turns > 0) reports: complexity_score, dominant_factor, confidence values, and whether clarification improved or degraded the final MAE. This reveals whether FPs are a threshold problem or a confidence-gate problem.
  - Notes: The routing default fallback (confidence < 0.85 → AMPM) may be the primary FP driver, not the clinical threshold

- [ ] Task 17: Implement threshold sweep experiment
  - File: `backend/app/benchmarking/cli.py`
  - Action: Add a `sweep` subcommand that runs the agentic benchmark with varying `clinical_threshold` values (e.g., 5.0, 8.0, 10.0, 12.0, 15.0, 20.0) and varying `CONFIDENCE_THRESHOLD` values (e.g., 0.70, 0.75, 0.80, 0.85, 0.90). For each combo, report TNR, TPR, overall MAE. Output as a grid/heatmap.
  - Notes: This identifies the Pareto-optimal threshold combination. Can use a smaller N (e.g., 100) for the sweep since we're comparing relative performance.

- [ ] Task 18: Apply optimal thresholds based on sweep results
  - File: `backend/app/agent/constants.py:78-80`
  - Action: Update `CONFIDENCE_THRESHOLD` and the default `clinical_threshold` in `StreamAnalysisRequest` to the optimal values identified by the sweep. Document the rationale.
  - Notes: Only change after Phase A data confirms the optimal values. The thesis should report both the original and tuned thresholds with their respective metrics.

### Acceptance Criteria

#### Phase A — Measurement Integrity

- [ ] AC 1: Given the migration `20260309124343` is applied, when running a benchmark with the 11 previously-failing dish IDs, then all 11 dishes process successfully (0% deterministic failure rate)
- [ ] AC 2: Given the `complexity_score` schema documentation is updated, when a developer reads `analysis.py`, then the field description accurately states the unbounded deterministic scale and its practical range (0-~21.1)
- [ ] AC 3: Given `aggregate_complexity()` is updated, when complexity metrics are reported, then the output includes `score_scale`, `score_min`, and `score_max` fields that self-document the scale
- [ ] AC 4: Given a benchmark run completes with N≥30, when `aggregate_mae()` is called, then the result includes 95% confidence intervals for all macronutrient MAE values
- [ ] AC 5: Given two mode results (agentic + single-shot), when `compare_modes()` is called, then it returns Cohen's d effect sizes for each macronutrient and an overall MAE comparison with 95% CI
- [ ] AC 6: Given TNR/TPR is computed for a benchmark run, when routing accuracy is reported, then Wilson score confidence intervals are included for both TNR and TPR
- [ ] AC 7: Given a dish exceeds `dish_timeout_seconds` during a benchmark, when the timeout fires, then the dish is marked as failed with error "timeout" and the runner proceeds to the next dish without blocking
- [ ] AC 8: Given a transient HTTP 429/500/502/503/504 error during a benchmark dish, when the retry logic evaluates it, then the dish is retried up to 3 times with exponential backoff
- [ ] AC 9: Given a benchmark run with `--limit 500 --seed 42`, when completed across all 3 modes, then results are reproducible (same dishes selected) and include all new statistical measures (CI, effect size, Wilson intervals)

#### Phase B — System Tuning

- [ ] AC 10: Given Phase A agentic results, when `analyze_false_positives()` is called, then it returns per-FP-dish breakdown showing complexity_score, dominant_factor, confidence, and MAE impact of clarification
- [ ] AC 11: Given a threshold sweep is run, when results are compared, then the output shows a grid of TNR/TPR/MAE for each threshold combination, identifying the Pareto-optimal configuration
- [ ] AC 12: Given optimal thresholds are identified, when applied to constants, then a re-run at N=500 shows a statistically significant improvement in TNR (95% Wilson CI lower bound must exceed the pre-tuning TNR point estimate of 54.3%) without the TPR 95% CI lower bound falling below the pre-tuning TPR point estimate

## Additional Context

### Dependencies

- **Supabase CLI** for database migration application (`supabase migration up` for local; `supabase db push --linked` for remote — never use `db push` without reviewing the diff)
- **Nutrition5K dataset** (~5,004 dishes) accessible via Google Cloud Storage URLs for benchmark image loading
- **LLM API** (Google Gemini) availability and quota for N=500 runs (~1,500 API calls across 3 modes)
- **Python `statistics` module** (stdlib) — already imported in `metrics.py`
- No new external packages required — all statistical calculations use stdlib

### Testing Strategy

**Unit Tests (extend existing):**
- `backend/tests/benchmarking/test_metrics.py`: Add tests for `calculate_ci()`, `calculate_cohens_d()`, `compare_modes()`, `analyze_false_positives()`, Wilson interval calculation, and extended `AggregateMAE` with CI fields
- `backend/tests/benchmarking/test_metrics.py`: Add tests for `ComplexityMetrics` with new `score_scale`/`score_min`/`score_max` fields
- `backend/tests/services/test_complexity_calculator.py`: No changes needed — existing tests already validate the formula

**Integration Tests:**
- Verify the full upload → analysis → finalization flow succeeds after migration (manual smoke test)
- Run a mini benchmark (N=10) across all 3 modes to verify metrics pipeline end-to-end

**Manual Testing:**
- Apply migration, then run N=50 benchmark to compare against previous results (same seed)
- Verify the 11 previously-failing dishes now succeed
- Review generated comparison report for correctness and clarity

### Notes

- **Risk: LLM API quota** — N=500 × 3 modes = ~1,500 dish analyses. At ~30s each, that's ~12.5 hours total runtime. Consider running modes in parallel on separate machines or staggering overnight.
- **Risk: Dataset bias** — Nutrition5K skews toward simple cafeteria meals. Only ~15-20% of dishes classify as "complex" via stratification. N=500 should yield ~75-100 complex dishes — statistically adequate but not large.
- **Risk: Non-deterministic LLM output** — Same dish may get different complexity scores across runs. The seed controls dish selection, not LLM behavior. Consider multiple runs for variance estimation.
- **Limitation: Oracle answer quality** — The `question_parser.py` uses regex-based intent classification. Some clarification answers may be poor quality, degrading agentic mode accuracy. Task 13 (oracle audit) must be completed before N=500 scaling to validate oracle fitness. If >20% of answers are wrong, fix `question_parser.py` before proceeding.
- **Future consideration:** Phase B threshold tuning may reveal that the routing default fallback (confidence < 0.85 → AMPM) is the primary driver of false positives, not the clinical threshold. If so, the fix is changing the default from AMPM_ENTRY to FINALIZE_LOG — but that's an architecture change and out of scope for this spec.
