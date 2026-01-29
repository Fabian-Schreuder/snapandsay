# Benchmarking & Prompt Optimization

This component provides a deterministic "Oracle" benchmarking harness to evaluate the Snap and Say agent's accuracy and an automated system for prompt engineering.

## Overview

The benchmarking system leverages the **Nutrition5K** dataset and a "Virtual User" (Oracle) to:
1.  Initialize sessions with ground-truth images.
2.  Simulate conversational clarification turns based on dataset metadata.
3.  Calculate **Mean Absolute Error (MAE)** for nutritional estimations.
4.  Iteratively optimize prompts using LLM-based error analysis.
12. **Compare different LLM Providers** (OpenAI vs Google Gemini) to identify the best model for specific tasks.

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

### Standard Benchmark (Legacy)
Run a standard deterministic benchmark:
```bash
uv run python -m app.benchmarking.cli run --limit 10 --complexity simple
```

### Prompt Experiments
Run a controlled experiment with a specific prompt version (defined in `backend/app/benchmarking/prompts/`):
```bash
uv run python -m app.benchmarking.cli experiment --prompt v2 --limit 5 --seed 42
```

### Multi-Model Benchmarking
You can specify the LLM provider and model for experiments or standard runs:
```bash
# Run with Google Gemini 2.0 Flash
uv run python -m app.benchmarking.cli experiment --prompt v2 --provider google --model gemini-3.0-flash --limit 10

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
uv run python -m app.benchmarking.cli optimize --experiment-id <ID> --provider google --model gemini-3.0-flash
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
The `OracleRunner` class automates the SSE stream interaction, parsing agent questions and providing facts from the dataset ground truth until the agent produces a final log.

### Experiment Log
Results are saved to `benchmark_output/experiments/` as structured JSON, enabling:
- Academic reproducibility.
- Trend analysis over iterations.
- Regression testing for new model versions.

### Propagation
Prompt overrides, provider selection, and model configuration are passed via:
`CLI` -> `OracleRunner` -> `SSE Stream API` -> `AgentState` -> `AgentNodes` -> `LLMService`.
