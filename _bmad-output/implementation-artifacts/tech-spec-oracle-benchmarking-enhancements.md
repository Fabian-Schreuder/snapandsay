---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
tech_stack: ['Python', 'FastAPI', 'Pandas', 'spaCy/NLP', 'NumPy/Statistics']
files_to_modify: ['backend/app/benchmarking/nutrition5k_loader.py', 'backend/app/benchmarking/oracle_runner.py', 'backend/app/benchmarking/schemas.py', 'backend/app/benchmarking/cli.py', 'backend/app/benchmarking/stratification.py', 'backend/app/benchmarking/question_parser.py', 'backend/app/benchmarking/metrics.py']
code_patterns: ['Strategy Pattern for Stratification', 'NLP Question Parsing', 'Batch Processing', 'WFR Ground Truth Comparison', 'Latency Tracking']
test_patterns: ['Statistical Validation', 'Regression Testing', 'Deterministic Seeds', 'MAE Accuracy Testing']
status: 'implemented'
---

# Tech Spec: Oracle Benchmarking Enhancements

## 1. Context & Goal

**Goal:** Bring the Oracle Benchmarking Component into full compliance with the research methodology requirements for medical-grade evaluation, specifically implementing the "Simulated User" protocol for technical accuracy assessment.

**Research Methodology Alignment:**
> "We assessed technical accuracy through artificial benchmarking against the Weighed Food Record (WFR) ground truth. This involved a 'Simulated User' protocol using the Nutrition5k dataset to measure Mean Absolute Error (MAE) and computational latency, isolating system performance from human behavioral variability."

**Problem:**
The current implementation has gaps that prevent it from meeting the methodology specification:
1. Sample size is limited (tested with 1-5 dishes instead of N=500)
2. Stratification uses only ingredient count, missing visual distinctiveness and ambiguity scoring
3. Oracle provides generic summary responses instead of question-specific answers
4. **No MAE calculation against WFR ground truth**
5. **No computational latency tracking**

**Solution:**
Enhance the benchmarking harness to:
- Support full N=500 sample evaluation with proper batch processing
- Implement multi-factor stratification (ingredient count + visual distinctiveness + caloric density)
- Add NLP-based question parsing for targeted Oracle responses
- **Calculate MAE against Nutrition5k WFR ground truth (actual weighed macros)**
- **Track and report computational latency per dish and aggregate**

**In Scope:**
- Enhanced stratification logic with configurable rules
- Question-aware Oracle response generation
- Batch execution with progress tracking and resumability
- Statistical reporting per complexity class
- **WFR ground truth comparison with MAE metrics**
- **Latency measurement (per-dish and aggregate p50/p95/p99)**

**Out of Scope:**
- Computer vision-based visual distinctiveness (use heuristics instead)
- Real-time dataset fetching (continue using cached data)
- UI integration (CLI only)

## 2. Investigation Findings

### Current Implementation Analysis

**Stratification (nutrition5k_loader.py:91):**
```python
complexity = "simple" if len(ingredients) <= 3 else "complex"
```
This is insufficient. The methodology requires:
- **Simple:** ≤3 ingredients AND high visual distinctiveness
- **Complex:** High ambiguity OR hidden caloric density

**Oracle Response (oracle_runner.py:130):**
```python
answer = dish.summary  # Always returns full summary
```
This doesn't match the requirement to "retrieve precise metadata" based on specific questions.

### Proposed Stratification Rules

| Factor | Simple | Complex |
|--------|--------|---------|
| Ingredient Count | ≤ 3 | > 3 |
| Visual Distinctiveness | High (single color profile, separate items) | Low (mixed, layered) |
| Caloric Density | Low (≤ 150 kcal/100g) | High (> 150 kcal/100g) |
| Ambiguity Score | Low (distinct ingredients) | High (sauces, mixed dishes) |

### Question-Answer Mapping Patterns

Based on typical agent clarification questions:

| Question Pattern | Dataset Field | Response Template |
|------------------|---------------|-------------------|
| "What oil/fat was used?" | ingredients (fat type) | "I used {fat_name}" |
| "How much {ingredient}?" | ingredient.grams | "About {grams}g of {name}" |
| "What type of {category}?" | ingredient.name | "It's {specific_name}" |
| "Any dressing/sauce?" | ingredients (sauce check) | "Yes, {sauce}" or "No dressing" |
| Default/Unknown | dish.summary | Full summary |

## 3. High-Level Design

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI (cli.py)                         │
│  --limit 500 --complexity simple --batch-size 50 --resume   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Nutrition5kLoader (enhanced)                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              StratificationEngine                     │  │
│  │  - ingredient_count_score()                           │  │
│  │  - visual_distinctiveness_score()                     │  │
│  │  - caloric_density_score()                            │  │
│  │  - ambiguity_score()                                  │  │
│  │  - classify() → "simple" | "complex"                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               OracleRunner (enhanced)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              QuestionParser                           │  │
│  │  - parse_question(question: str) → QuestionIntent     │  │
│  │  - lookup_answer(intent, dish) → str                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              BatchExecutor                            │  │
│  │  - run_batch(dishes, batch_size) → BatchResult        │  │
│  │  - resume_from_checkpoint(file)                       │  │
│  │  - save_checkpoint(results)                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **CLI** receives `--limit 500 --complexity simple`
2. **Loader** applies `StratificationEngine` to classify all dishes
3. **OracleRunner** processes dishes in batches with checkpointing
4. **QuestionParser** intercepts clarifications and returns targeted answers
5. **LatencyTracker** records timing for each dish processing
6. **MAE Calculator** compares predicted macros against WFR ground truth
7. **Results** aggregated with per-complexity-class statistics, MAE, and latency metrics

### WFR Ground Truth Comparison

The Nutrition5k dataset provides **Weighed Food Record (WFR)** ground truth:
- `total_calories` — Actual measured calories
- `total_protein` — Actual measured protein (g)
- `total_fat` — Actual measured fat (g)
- `total_carb` — Actual measured carbohydrates (g)

For each dish, we compare the agent's predictions against these ground truth values:

```
MAE_calories = |predicted_calories - ground_truth_calories|
MAE_protein  = |predicted_protein - ground_truth_protein|
MAE_fat      = |predicted_fat - ground_truth_fat|
MAE_carbs    = |predicted_carbs - ground_truth_carbs|
```

Aggregate MAE is the mean across all N dishes.

## 4. Implementation Plan

### Phase 1: Enhanced Stratification

- [ ] **Task 1: Create Stratification Engine**
  - **File:** `backend/app/benchmarking/stratification.py` [NEW]
  - **Action:** Implement `StratificationEngine` class with scoring methods:
    - `ingredient_count_score(dish)` → 0.0 (simple) to 1.0 (complex)
    - `visual_distinctiveness_score(dish)` → heuristic based on ingredient variety
    - `caloric_density_score(dish)` → based on `total_calories / total_mass`
    - `ambiguity_score(dish)` → based on ingredient name patterns (sauces, mixed, etc.)
    - `classify(dish)` → "simple" or "complex" using weighted average
  - **Heuristics for Visual Distinctiveness:**
    - High: Ingredient names suggest separate items (fruit, vegetables, protein)
    - Low: Ingredient names suggest mixing (sauce, dressing, casserole, stew)

- [ ] **Task 2: Integrate Stratification into Loader**
  - **File:** `backend/app/benchmarking/nutrition5k_loader.py` [MODIFY]
  - **Action:** Replace simple ingredient count logic with `StratificationEngine.classify()`
  - **Backward Compatibility:** Keep `complexity` parameter behavior unchanged

---

### Phase 2: Question-Aware Oracle

- [ ] **Task 3: Create Question Parser**
  - **File:** `backend/app/benchmarking/question_parser.py` [NEW]
  - **Action:** Implement `QuestionParser` class:
    - Pattern matching for common question types (oil, quantity, type, dressing)
    - Entity extraction for ingredient references
    - `parse(question: str) → QuestionIntent`
    - `lookup_answer(intent: QuestionIntent, dish: NutritionDish) → str`

- [ ] **Task 4: Update Oracle Runner with Question Parsing**
  - **File:** `backend/app/benchmarking/oracle_runner.py` [MODIFY]
  - **Action:** Replace `answer = dish.summary` with:
    ```python
    parser = QuestionParser()
    intent = parser.parse(question)
    answer = parser.lookup_answer(intent, dish)
    ```

---

### Phase 3: Batch Execution & Scaling

- [ ] **Task 5: Implement Batch Executor**
  - **File:** `backend/app/benchmarking/oracle_runner.py` [MODIFY]
  - **Action:** Add `BatchExecutor` class or methods:
    - Process dishes in configurable batch sizes (default 50)
    - Save checkpoint after each batch to `benchmark_checkpoint.json`
    - Support `--resume` flag to continue from last checkpoint
    - Add progress bar (optional, using `tqdm`)

- [ ] **Task 6: Enhance CLI for Full Benchmark**
  - **File:** `backend/app/benchmarking/cli.py` [MODIFY]
  - **Action:** Add new arguments:
    - `--batch-size` (default 50)
    - `--resume` (resume from checkpoint)
    - `--output-dir` (directory for results and checkpoints)
  - **Update Default:** Change `--limit` default from 10 to 250 per complexity class

---

### Phase 4: WFR Ground Truth Comparison & MAE Calculation

- [ ] **Task 7: Implement MAE Calculator**
  - **File:** `backend/app/benchmarking/metrics.py` [NEW]
  - **Action:** Create `MetricsCalculator` class:
    - `calculate_dish_mae(predicted: dict, ground_truth: NutritionDish) → DishMAE`
    - `aggregate_mae(results: list[DishMAE]) → AggregateMAE`
    - Handle missing predictions gracefully (count as failure, exclude from MAE)
  - **Metrics per dish:**
    - `mae_calories`: Absolute error in kcal
    - `mae_protein`: Absolute error in grams
    - `mae_fat`: Absolute error in grams
    - `mae_carbs`: Absolute error in grams
  - **Aggregate metrics:**
    - Mean MAE per macro across all dishes
    - Standard deviation of errors
    - Percentage within ±10% of ground truth

- [ ] **Task 8: Implement Latency Tracker**
  - **File:** `backend/app/benchmarking/metrics.py` [MODIFY]
  - **Action:** Add `LatencyTracker` class:
    - Record `start_time` and `end_time` for each dish
    - Calculate per-dish latency in seconds
    - Aggregate: mean, p50, p95, p99 latencies
  - **Integration:** Wrap `run_dish()` with timing context manager

---

### Phase 5: Statistical Reporting

- [ ] **Task 9: Add Comprehensive Statistical Summary**
  - **File:** `backend/app/benchmarking/cli.py` [MODIFY]
  - **Action:** Generate detailed report at end of benchmark:
    - Success rate by complexity class
    - Average clarification turns by complexity
    - Clarification trigger rate
    - **MAE against WFR ground truth (per-macro breakdown)**
    - **Latency statistics (mean, p50, p95, p99)**
    - **Percentage of predictions within ±10% of ground truth**

---

### Phase 6: Testing & Validation

- [ ] **Task 10: Unit Tests for Stratification**
  - **File:** `backend/tests/benchmarking/test_stratification.py` [NEW]
  - **Action:** Test cases for each scoring function and edge cases

- [ ] **Task 11: Unit Tests for Question Parser**
  - **File:** `backend/tests/benchmarking/test_question_parser.py` [NEW]
  - **Action:** Test pattern matching and entity extraction

- [ ] **Task 12: Unit Tests for MAE & Latency Metrics**
  - **File:** `backend/tests/benchmarking/test_metrics.py` [NEW]
  - **Action:** Test MAE calculation accuracy and latency tracking

- [ ] **Task 13: Integration Test with N=50 Sample**
  - **File:** `backend/tests/benchmarking/test_full_benchmark.py` [NEW]
  - **Action:** End-to-end test with small sample to verify pipeline including MAE and latency

## 5. Acceptance Criteria

- [ ] **AC 1: Stratification Accuracy**
  - Multi-factor stratification correctly classifies dishes
  - Visual distinctiveness and caloric density are factored into classification

- [ ] **AC 2: Question-Aware Responses**
  - Oracle returns targeted answers for common question patterns
  - Falls back to summary for unknown patterns

- [ ] **AC 3: N=500 Execution**
  - CLI can run 500-dish benchmark without crashes
  - Checkpointing allows resumption after failures
  - Total execution completes within reasonable time (~2-3 hours)

- [ ] **AC 4: WFR Ground Truth Comparison**
  - MAE calculated against Nutrition5k ground truth macros
  - Per-macro breakdown (calories, protein, fat, carbs)
  - Report includes percentage within ±10% accuracy threshold

- [ ] **AC 5: Computational Latency Metrics**
  - Per-dish latency tracked in seconds
  - Aggregate statistics: mean, p50, p95, p99
  - Report includes latency breakdown by complexity class

- [ ] **AC 6: Statistical Reporting (Comprehensive)**
  - Output includes per-class success rates
  - Output includes clarification trigger rates
  - Output includes macro prediction accuracy (MAE)
  - Output includes latency metrics
  - Output matches research paper reporting format

## 6. Verification Plan

### Automated Tests
```bash
# Unit tests for new modules
cd backend && uv run pytest tests/benchmarking/test_stratification.py -v
cd backend && uv run pytest tests/benchmarking/test_question_parser.py -v

# Integration test (small sample)
cd backend && uv run pytest tests/benchmarking/test_full_benchmark.py -v
```

### Manual Verification
```bash
# Run full benchmark (N=500)
cd backend
uv run python -m app.benchmarking.cli --limit 250 --complexity simple --seed 42 --batch-size 50
uv run python -m app.benchmarking.cli --limit 250 --complexity complex --seed 42 --batch-size 50
```

### Expected Output Structure
```json
{
  "metadata": {
    "timestamp": "2026-01-29T14:30:00Z",
    "seed": 42,
    "total_dishes": 500,
    "simple_dishes": 250,
    "complex_dishes": 250
  },
  "accuracy": {
    "success_rate": 0.92,
    "success_rate_simple": 0.95,
    "success_rate_complex": 0.89,
    "avg_clarification_turns": 0.7,
    "clarification_trigger_rate": 0.35
  },
  "wfr_comparison": {
    "mae": {
      "calories": 45.2,
      "protein": 3.1,
      "fat": 2.8,
      "carbs": 5.4
    },
    "std_dev": {
      "calories": 32.1,
      "protein": 2.2,
      "fat": 1.9,
      "carbs": 4.1
    },
    "within_10_percent": {
      "calories": 0.78,
      "protein": 0.85,
      "fat": 0.82,
      "carbs": 0.80
    }
  },
  "latency": {
    "mean_seconds": 4.2,
    "p50_seconds": 3.8,
    "p95_seconds": 8.5,
    "p99_seconds": 12.1,
    "per_complexity": {
      "simple_mean": 3.5,
      "complex_mean": 4.9
    }
  },
  "results": [
    {
      "dish_id": "dish_1234567890",
      "success": true,
      "turns": 1,
      "latency_seconds": 3.8,
      "ground_truth": {
        "calories": 350,
        "protein": 25,
        "fat": 12,
        "carbs": 35
      },
      "predicted": {
        "calories": 340,
        "protein": 22,
        "fat": 14,
        "carbs": 32
      },
      "mae": {
        "calories": 10,
        "protein": 3,
        "fat": 2,
        "carbs": 3
      }
    }
  ]
}
```

## 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Full N=500 run takes too long | Medium | Medium | Batch processing + checkpointing |
| Heuristic stratification doesn't match human judgment | Medium | High | Calibrate against manual sample labels |
| Question patterns don't cover all agent questions | High | Low | Graceful fallback to summary |
| API rate limits during long benchmark | Low | High | Add configurable delay between requests |
