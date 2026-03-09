# Benchmarking & Prompt Optimization

This component provides a deterministic "Oracle" benchmarking harness to evaluate the Snap and Say agent's accuracy and an automated system for prompt engineering.

## Overview

The benchmarking system leverages the **Nutrition5K** dataset and a "Virtual User" (Oracle) to:
1. Initialize sessions with ground-truth images.
2. Simulate conversational clarification turns based on dataset metadata.
3. Calculate **Mean Absolute Error (MAE)** for nutritional estimations (overall and per-stratum).
4. Iteratively optimize prompts using LLM-based error analysis.
5. **Compare different LLM Providers** (OpenAI vs Google Gemini) to identify the best model for specific tasks.
6. **Run multi-mode evaluations** (agentic, single-shot, naive-always-ask) for thesis benchmarking.
7. **Compare modes** with per-stratum MAE, routing accuracy (TNR/TPR), and turn reduction metrics.

---

## 1. Setup

### Download Dataset
Use the provided script to download a sample of the Nutrition5k dataset:

```bash
uv run python scripts/download_nutrition5k.py --limit 50 --seed 42
```
This saves data to `data/nutrition5k`.

### API Access
Ensure the backend is running and you have a test user:
```bash
# ENV fallback or CLI args
export TEST_EMAIL="user@example.com"
export TEST_PASSWORD="password"
```

---

## 2. Usage

### Standard Benchmark
Run a deterministic benchmark with mode selection:
```bash
# Default agentic mode
uv run python -m app.benchmarking.cli run --limit 10 --complexity simple

# Single-shot mode (no clarification, force immediate finalization)
uv run python -m app.benchmarking.cli run --mode single-shot --limit 10

# Naive-always-ask mode (force clarification on every dish)
uv run python -m app.benchmarking.cli run --mode naive-always-ask --limit 10
```

#### Runner Modes

| Mode | Behaviour | Use Case |
| --- | --- | --- |
| `agentic` (default) | Agent decides whether to clarify based on complexity scoring | Production behaviour baseline |
| `single-shot` | Forces immediate finalization (`force_finalize=True`), no clarification | Measures raw VLM accuracy |
| `naive-always-ask` | Forces clarification on every dish (`force_clarify=True`) | Upper-bound baseline for turn reduction |

#### Additional Run Options

| Flag | Default | Description |
| --- | --- | --- |
| `--mode` | `agentic` | Runner mode |
| `--timeout` | `180.0` | Per-dish timeout in seconds |
| `--retries` | `2` | Max retries per dish on transient failure (timeout/connection) |
| `--resume` | — | Resume from checkpoint file |
| `--force-resume` | — | Resume even if checkpoint parameters don't match current args |
| `--batch-size` | `50` | Progress logging interval |
| `--delay` | `1.0` | Pause between dishes (rate limiting) |
| `--max-turns` | `3` | Max clarification rounds per dish |
| `--provider` | — | LLM provider (`openai`, `google`) |
| `--model` | — | Specific model name |

### Cross-Mode Comparison
After running benchmarks in all three modes, compare results:
```bash
uv run python -m app.benchmarking.cli compare \
  --agentic-id run_20260309_120000 \
  --single-shot-id run_20260309_140000 \
  --naive-id run_20260309_160000 \
  --seed 42
```

This outputs a comparison table with:
- **Per-stratum MAE** (simple vs complex) for each mode
- **Routing accuracy** (TNR/TPR) for the agentic mode
- **Turn reduction** percentage: `(naive_turns - agentic_turns) / naive_turns * 100`

Use `--force` to skip parameter validation between experiments.

### Prompt Experiments
Run a controlled experiment with a specific prompt version (defined in `backend/app/benchmarking/prompts/`):
```bash
uv run python -m app.benchmarking.cli experiment --prompt v2 --limit 5 --seed 42
```

### Multi-Model Benchmarking
You can specify the LLM provider and model for experiments or standard runs:
```bash
# Run with Google Gemini 2.0 Flash
uv run python -m app.benchmarking.cli experiment --prompt v2 --provider google --model gemini-3-flash-preview --limit 10

# Run standard benchmark with GPT-4o-mini
uv run python -m app.benchmarking.cli run --provider openai --model gpt-4o-mini --limit 10
```

Supported providers: `openai` (default), `google`.

### View History
See a markdown table of all recorded experiments:
```bash
uv run python -m app.benchmarking.cli history
```

### Auto-Optimization
Analyze the top errors from an experiment and get a suggested prompt revision:
```bash
uv run python -m app.benchmarking.cli optimize --experiment-id <ID> --provider google --model gemini-3-flash-preview
```

---

## 3. Prompt Registry

Prompts are externalized to YAML files for versioned tracking:

| File | Focus |
| --- | --- |
| `v0_baseline.yaml` | Initial simple prompt |
| `v1_methodology.yaml` | Verbose step-by-step guidance |
| `v2_caloric_density.yaml` | Explicit kcal/100g lookup tables |

To test a new prompt, create a `.yaml` file in `backend/app/benchmarking/prompts/` and reference its ID in the `experiment` command.

---

## 4. Architecture

### Oracle Runner
The `OracleRunner` class automates the SSE stream interaction using a reconnection-based loop. The server terminates the SSE stream after each clarification event — the runner submits oracle answers, then opens a new stream to continue until an `agent.response` or `agent.error` is received.

Key behaviours:
- **Question parsing**: Each clarification question is individually parsed and answered using ground-truth data from the dataset (`QuestionParser`).
- **Semantic gatekeeper**: In single-shot mode, if the semantic gatekeeper fires a clarification despite `force_finalize`, the runner auto-answers and reconnects.
- **Safety limits**: `max_turns` (per dish) and `max_reconnections=10` prevent infinite loops.

### Checkpointing
Long benchmark runs (N=500+) use atomic checkpoint saves after every dish:
- Checkpoint file: `benchmark_output/benchmark_checkpoint.json`
- Atomic writes via temp file + `os.replace` to prevent corruption on kill
- Checkpoint v2 stores `mode`, `seed`, `complexity`, `limit` — resume validates matching parameters
- Use `--force-resume` to override parameter mismatch validation

### Metrics

| Metric | Description |
| --- | --- |
| **MAE** (per macro) | Mean Absolute Error for calories, protein, fat, carbs |
| **Per-stratum MAE** | MAE grouped by dish complexity (simple/complex) |
| **Std Dev** | Standard deviation of absolute errors |
| **TNR** | True Negative Rate — simple dishes with 0 clarification turns |
| **TPR** | True Positive Rate — complex dishes with >0 clarification turns |
| **Turn Reduction** | `(naive_turns - agentic_turns) / naive_turns * 100` |
| **Complexity Stats** | Mean score, dominant factor distribution, clarification counts |
| **Latency** | Mean, P50, P95, P99, per-complexity breakdown |

### Experiment Log
Results are saved to `benchmark_output/experiments/` as structured JSON, enabling:
- Academic reproducibility.
- Trend analysis over iterations.
- Regression testing for new model versions.

### Propagation
Prompt overrides, provider selection, model configuration, and force flags are passed via:
`CLI` -> `OracleRunner` -> `SSE Stream API` -> `AgentState` -> `AgentNodes` -> `LLMService`.
