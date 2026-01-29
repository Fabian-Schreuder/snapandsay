
stepsCompleted: [1, 2, 3, 4, 5]
tech_stack: ['Python', 'FastAPI', 'Pandas', 'Requests/Httpx']
files_to_modify: ['backend/app/benchmarking/oracle_runner.py', 'scripts/download_nutrition5k.py', 'backend/app/benchmarking/schemas.py', 'backend/app/benchmarking/nutrition5k_loader.py', 'backend/app/services/llm_service.py', 'backend/app/benchmarking/cli.py']
code_patterns: ['External Runner Pattern', 'State Re-hydration', 'Data URI Image Injection', 'Server-Side Image Proxy']
test_patterns: ['End-to-End Simulation', 'Statistical Evaluation', 'Deterministic Seeds']
status: 'implemented'
---

# Tech Spec: Oracle Benchmarking Component

## 1. Context & Goal

**Goal:** Create a deterministic "Oracle" benchmarking harness to evaluate the Snap and Say agent's reasoning capabilities using the Nutrition5k dataset.

**Problem:**
Reliably testing the agent's "Reason -> Clarify -> Log" loop is difficult with human testers due to behavioral variability. We need a ground-truth based system to measure accuracy and confidence gating in isolation.

**Solution:**
Build an external benchmarking runner that acts as a "Virtual User". It uses the Nutrition5k dataset to simulate meals. When the agent asks for clarification, the Oracle queries the dataset metadata (ingredients, calories) and responds with a precise text transcript. To ensure reliability with external image sources (like Nutrition5k's GCS bucket), the backend acts as a proxy, downloading and base64-encoding images before sending them to the LLM.

**In Scope:**
-   **Data Acquisition:** Script to download/parse Nutrition5k dataset (`metadata.csv`, `dishes.csv`).
-   **Stratification:** Logic to classify dishes as "Simple" (<=3 ingredients, distinct) or "Complex" (Ambiguous, dense).
-   **Oracle Runner:** An external harness (not a graph node) that orchestrates the `AgentGraph`. It injects an initial image/transcript, intercepts `EVENT_CLARIFICATION`, and supplies the ground truth answer.
-   **Metrics:** Track success rate, clarification triggering rate, and final logging accuracy.

**Out of Scope:**
-   **Audio Synthesis:** We will use text transcripts to simulate voice input.
-   **UI Integration:** This is a backend CLI/script tool only.
-   **Real-time fetching:** Data will be cached locally, not fetched on-the-fly execution.

## 2. Investigation Findings

### Core Architecture Decisions
-   **Pattern:** External Orchestrator (Harness).
-   **Harness Logic:**
    1.  `Loader` picks a Nutrition5k dish.
    2.  `Runner` invokes `AgentGraph` with `image_url` (from dataset) + empty transcript.
    3.  **Image Handling Update:** The `llm_service` detects external URLs (like GCS), downloads them server-side, and converts to Base64 to prevent LLM provider timeouts/auth issues.
    4.  `Runner` listens to SSE stream.
    5.  If `EVENT_CLARIFICATION` received:
        -   Parse question.
        -   `Oracle` logic finds answer in dataset.
        -   `Runner` re-invokes `AgentGraph` with answer as text transcript.
    6.  Collect final `DietaryLog` result and compare with ground truth.

### Data Source
-   Git Clone from `https://github.com/google-research-datasets/Nutrition5k`
-   We need `metadata.csv` (IDs, macros) and `ingredients_metadata.csv` (detailed components).

## 3. High-Level Design

### Core Components
1.  **Nutrition5k Loader:** Parses the dataset and filters based on complexity rules.
2.  **Oracle Node:** Replaces the human user in the graph. It intercepts agent questions and responds based on dataset metadata.
3.  **Benchmarking Runner:** Orchestrates the test, effectively replacing the standard `app.main` entry point for these runs.

### Data Flow
`Runner` -> `Loader (Get Sample)` -> `Agent (Start)` -> `LLM Service (Download & Encode Image)` -> `Agent (Ask Question)` -> `Oracle (Lookup Answer)` -> `Agent (Receive Answer)`

## 4. Implementation Plan

#### Phase 1: Data Acquisition & Schemas
- [x] **Task 1: Define Benchmarking Schemas**
  - **File:** `backend/app/benchmarking/schemas.py`
  - **Action:** Create `NutritionDish` and `OracleConfig` Pydantic models.
- [x] **Task 2: Implement Nutrition5k Downloader**
  - **File:** `scripts/download_nutrition5k.py`
  - **Action:** Script to fetch `metadata.csv` files and a limited sample of images.
  - **Notes:** Used robust retry logic and limited sample size.
- [x] **Task 3: Implement Nutrition5k Loader**
  - **File:** `backend/app/benchmarking/nutrition5k_loader.py`
  - **Action:** Class to load CSVs and return `NutritionDish` objects.
  - **Notes:** Implemented deterministic shuffling with `random_seed`.

#### Phase 2: Oracle Runner Core
- [x] **Task 4: Implement Oracle Runner Harness**
  - **File:** `backend/app/benchmarking/oracle_runner.py`
  - **Action:** Create `OracleRunner` class.
    - **Auth:** Implemented `sign_in_with_password` using Supabase client to retrieve JWT.
    - **Stream:** correctly parses JSON-embedded SSE events (`agent.thought`, `agent.response`, etc.).
    - **Retry:** Implemented reliable image downloading in `llm_service.py`.

#### Phase 3: CLI & Execution
- [x] **Task 5: Create CLI Entry Point**
  - **File:** `backend/app/benchmarking/cli.py`
  - **Action:** `uv run python -m app.benchmarking.cli`
  - **Args Implemented:** `--limit`, `--complexity`, `--seed`, `--max-turns`, `--email`, `--password`, `--api-url`.

#### Phase 4: Verification & Testing
- [x] **Task 6: Unit & Integration Tests**
  - **File:** `backend/tests/benchmarking/test_loader.py`, `backend/tests/benchmarking/test_runner.py`
  - **Action:** Verify data loading determinism and runner flow logic.
  - **Status:** All tests passing. Integration test succeeded against live backend.

### Acceptance Criteria

- [x] **AC 1: Data Loading & Reproducibility**
  - Validated: `seed=42` returns consistent dish order.
- [x] **AC 2: End-to-End Simulation (Happy Path)**
  - Validated: Runner successfully logs a meal (`dish_1562086595`) with 0 clarification turns (direct success).
- [x] **AC 3: Clarification Logic**
  - Validated: Logic exists to intercept `agent.clarification` and respond (though sample dish succeeded without it).
- [x] **AC 4: Auth & Security**
  - Validated: Runner authenticates via Supabase before starting session.

### Testing Strategy

- **Manual Verification:** Run the `oracle_runner` script against a local running backend (`localhost:8000`) and watch the logs.
- **Automated Check:** The runner itself defines success/failure stats.
- **Unit Tests:** `tests/benchmarking/test_loader.py` to verify CSV parsing logic and seed determinism.
