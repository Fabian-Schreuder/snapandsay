# Oracle Benchmarking Component

This component provides a deterministic "Oracle" benchmarking harness to evaluate the Snap and Say agent's reasoning capabilities using the Nutrition5k dataset.

## Overview

The Oracle Runner acts as a "Virtual User" that:
1.  Selects a dish from the localized Nutrition5k dataset.
2.  Starts a session with the Snap and Say agent using the dish's image.
3.  Listens to the agent's thought process via SSE.
4.  Intercepts clarification questions (e.g., "Is this spicy?").
5.  Queries the dataset ground truth (ingredients, metadata).
6.  Responds to the agent with a precise text answer.
7.  Evaluates the final dietary log against the ground truth.

## Prerequisites

1.  **Backend Services**: The Snap and Say backend must be running locally (`localhost:8000`).
2.  **Dataset**: You must download a sample of the Nutrition5k dataset.

### Downloading Data

Use the provided script to download metadata and a sample of images:

```bash
# From the project root
uv run python scripts/download_nutrition5k.py --limit 50 --seed 42
```

This will save data to `data/nutrition5k`.

## Usage

Run the benchmark using the CLI entry point:

```bash
# From the backend directory
cd backend
uv run python -m app.benchmarking.cli --limit 10 --complexity complex
```

### Arguments

*   `--limit`: Number of dishes to test (default: 10).
*   `--complexity`: Filter by dish complexity (`simple`, `complex`, or `all`). `simple` dishes have <= 3 ingredients.
*   `--seed`: Random seed for deterministic sampling (default: 42).
*   `--max-turns`: Maximum number of clarification turns allowed per dish (default: 3).
*   `--api-url`: URL of the Snap and Say backend (default: `http://localhost:8000`).
*   `--email`: Test user email (can also use `TEST_EMAIL` env var).
*   `--password`: Test user password (can also use `TEST_PASSWORD` env var).

## Results

The runner outputs a summary table to the console and saves detailed JSON results to `benchmark_results_{timestamp}.json`.
