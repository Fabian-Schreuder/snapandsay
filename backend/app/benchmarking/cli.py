"""
Oracle Benchmarking CLI.

Enhanced CLI with batch processing, checkpointing, MAE calculation,
and latency tracking for research-grade benchmark execution.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.benchmarking.experiment_log import ExperimentLog, ExperimentResult
from app.benchmarking.metrics import LatencyTracker, MetricsCalculator
from app.benchmarking.nutrition5k_loader import Nutrition5kLoader
from app.benchmarking.oracle_runner import OracleRunner
from app.benchmarking.prompt_optimizer import PromptOptimizer
from app.benchmarking.prompts import PromptRegistry
from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_checkpoint(checkpoint_file: Path) -> tuple[list[dict], set[str]]:
    """Load results from checkpoint file."""
    if not checkpoint_file.exists():
        return [], set()

    with open(checkpoint_file) as f:
        data = json.load(f)

    results = data.get("results", [])
    processed_ids = {r["dish_id"] for r in results}
    logger.info(f"Loaded checkpoint with {len(processed_ids)} processed dishes")
    return results, processed_ids


def save_checkpoint(checkpoint_file: Path, results: list[dict], metadata: dict):
    """Save current results to checkpoint file."""
    data = {"metadata": metadata, "results": results}
    with open(checkpoint_file, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Checkpoint saved: {len(results)} results")


async def main_async(args):
    """Main async benchmark execution."""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize components
    prompts_dir = Path(__file__).parent / "prompts"
    prompt_registry = PromptRegistry(prompts_dir)
    experiment_log = ExperimentLog(output_dir)
    optimizer = PromptOptimizer(
        prompt_registry=prompt_registry,
        experiment_log=experiment_log,
        api_url=args.api_url,
        email=args.email,
        password=args.password,
    )

    if args.command == "experiment":
        result = await optimizer.run_experiment(
            prompt_id=args.prompt,
            limit=args.limit,
            complexity=args.complexity,
            seed=args.seed,
            provider=args.provider,
            model=args.model,
        )
        experiment_log.log_experiment(result)
        print(f"\nExperiment {result.experiment_id} completed.")
        print(f"Calories MAE: {result.metrics['calories']:.2f}")
        await optimizer.close()
        return

    if args.command == "history":
        print(experiment_log.export_markdown())
        await optimizer.close()
        return

    if args.command == "optimize":
        history = experiment_log.get_history()
        if not history:
            print("No experiments found. Run an experiment first.")
            await optimizer.close()
            return

        experiment_id = args.experiment_id or history[-1]["experiment_id"]
        detail_file = output_dir / f"experiment_{experiment_id}.json"

        if not detail_file.exists():
            print(f"Experiment detail not found: {experiment_id}")
            await optimizer.close()
            return

        with open(detail_file) as f:
            data = json.load(f)
            result = ExperimentResult(
                experiment_id=data["experiment_id"],
                prompt_version=data["prompt_version"],
                timestamp=data["timestamp"],
                metrics=data["metrics"],
                latency_stats=data["latency_stats"],
                per_dish_results=data["per_dish_results"],
                config=data["config"],
            )

        suggestion = await optimizer.suggest_improvements(result, provider=args.provider, model=args.model)
        print("\n" + "=" * 40)
        print("PROMPT IMPROVEMENT SUGGESTION")
        print("=" * 40)
        print(suggestion)
        await optimizer.close()
        return

    # Original benchmark flow...
    checkpoint_file = output_dir / "benchmark_checkpoint.json"
    results = []
    processed_ids: set[str] = set()

    # Load checkpoint if resuming
    if args.resume:
        results, processed_ids = load_checkpoint(checkpoint_file)

    # 1. Load Data
    logger.info("Initializing Loader...")
    loader = Nutrition5kLoader()

    logger.info(f"Loading dishes (Limit: {args.limit}, Complexity: {args.complexity}, Seed: {args.seed})")
    all_dishes = loader.load_dishes(seed=args.seed, complexity=args.complexity, limit=args.limit)

    if not all_dishes:
        logger.error("No dishes loaded. Ensure you have run 'scripts/download_nutrition5k.py' successfully.")
        sys.exit(1)

    # Filter out already processed dishes
    dishes = [d for d in all_dishes if d.dish_id not in processed_ids]
    logger.info(f"Loaded {len(all_dishes)} dishes, {len(dishes)} remaining to process.")

    if not dishes:
        logger.info("All dishes already processed. Generating report from checkpoint.")
    else:
        # 2. Init Runner
        runner = OracleRunner(
            api_url=args.api_url,
            email=args.email,
            password=args.password,
            max_turns=args.max_turns,
        )

        # 3. Login
        try:
            logger.info(f"Logging in as {args.email} to {args.api_url}...")
            await runner.login()
        except Exception as e:
            logger.error(f"Login failed: {e}")
            await runner.close()
            sys.exit(1)

        # 4. Latency Tracker
        latency_tracker = LatencyTracker()

        # 5. Run Loop with Batching
        try:
            for _i, dish in enumerate(dishes):
                batch_idx = (len(results) // args.batch_size) + 1
                in_batch_idx = (len(results) % args.batch_size) + 1

                logger.info(
                    f"--- Batch {batch_idx}, Item {in_batch_idx}/{args.batch_size} | "
                    f"Overall {len(results)+1}/{len(all_dishes)}: {dish.dish_id} ---"
                )

                result = await runner.run_dish(dish, provider=args.provider, model=args.model)
                results.append(result)

                # Record latency
                latency_tracker.record(
                    dish.dish_id,
                    result.get("latency_seconds", 0),
                    dish.complexity,
                )

                if result["success"]:
                    logger.info(
                        f"SUCCESS: {dish.dish_id} (Turns: {result['turns']}, "
                        f"Latency: {result.get('latency_seconds', 0):.1f}s)"
                    )
                    if result.get("final_data"):
                        logger.info(f"  Title: {result['final_data'].get('title')}")
                else:
                    logger.error(f"FAILURE: {dish.dish_id} - {result.get('error')}")

                # Save checkpoint after each batch
                if len(results) % args.batch_size == 0:
                    save_checkpoint(
                        checkpoint_file,
                        results,
                        {"seed": args.seed, "complexity": args.complexity, "batch_size": args.batch_size},
                    )

                # Brief pause to avoid rate limiting
                await asyncio.sleep(args.delay)

        finally:
            await runner.close()
            # Final checkpoint save
            save_checkpoint(
                checkpoint_file,
                results,
                {"seed": args.seed, "complexity": args.complexity, "batch_size": args.batch_size},
            )

    # 6. Generate Report/Result
    # Calculate MAE metrics
    metrics_calc = MetricsCalculator()
    mae_results = []

    # Recreate latency tracker and calculate MAE
    # We re-instantiate and re-populate from 'results' to ensure we capture
    # metrics for ALL dishes (including those loaded from checkpoints)
    latency_tracker = LatencyTracker()
    dishes_map = {d.dish_id: d for d in all_dishes}

    per_dish_results = []

    for result in results:
        dish_id = result["dish_id"]
        dish = dishes_map.get(dish_id)

        # Latency
        complexity = dish.complexity if dish else "unknown"
        latency_tracker.record(dish_id, result.get("latency_seconds", 0), complexity)

        # MAE
        if dish and result.get("success"):
            dish_mae = metrics_calc.calculate_dish_mae(result.get("final_data"), dish)
            mae_results.append(dish_mae)

            # Add detailed result
            dish_result = {
                "dish_id": dish_id,
                "success": True,
                "mae": dish_mae.to_dict(),
                "latency": result.get("latency_seconds", 0),
                "turns": result.get("turns", 0),
                "complexity_breakdown": result.get("complexity_breakdown"),
                "complexity_score": result.get("complexity_score"),
            }
            per_dish_results.append(dish_result)
        else:
            per_dish_results.append(
                {
                    "dish_id": dish_id,
                    "success": False,
                    "error": result.get("error"),
                    "latency": result.get("latency_seconds", 0),
                    "turns": result.get("turns", 0),
                    "complexity_breakdown": result.get("complexity_breakdown"),
                    "complexity_score": result.get("complexity_score"),
                }
            )

    aggregate_mae = metrics_calc.aggregate_mae(mae_results)
    aggregate_latency = latency_tracker.aggregate()
    complexity_stats = metrics_calc.aggregate_complexity(per_dish_results)

    # Create ExperimentResult
    experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_result = ExperimentResult(
        experiment_id=f"run_{experiment_id}",
        prompt_version="baseline_run",
        timestamp=datetime.now(UTC).isoformat(),
        metrics={**aggregate_mae.to_dict()["mae"], "complexity_stats": complexity_stats.to_dict()},
        latency_stats=aggregate_latency.to_dict(),
        per_dish_results=per_dish_results,
        config=vars(args),
    )

    experiment_log.log_experiment(final_result)

    # 7. Print Summary
    print("\n" + "=" * 60)
    print("ORACLE BENCHMARKING REPORT")
    print("=" * 60)
    print(f"\nTimestamp: {final_result.timestamp}")
    print(f"Total Dishes: {len(results)}")

    print("\n--- WFR Ground Truth Comparison (MAE) ---")
    mae = final_result.metrics
    print(f"Calories MAE: {mae['calories']:.1f} kcal")
    print(f"Protein MAE: {mae['protein']:.1f} g")

    # Complexity metrics summary
    cs = mae.get("complexity_stats", {})
    if cs.get("total_scored", 0) > 0:
        print("\n--- Complexity Scoring Metrics ---")
        print(f"Dishes Scored:        {cs['total_scored']}")
        print(f"Mean Complexity:      {cs['mean_score']:.4f}")
        print(f"Clarifications:       {cs['clarification_triggered_count']}")
        print(f"Total Questions:      {cs.get('total_questions_asked', 0)}")
        dist = cs.get("dominant_factor_distribution", {})
        if dist:
            print("Dominant Factor Distribution:")
            for factor, count in sorted(dist.items(), key=lambda x: -x[1]):
                print(f"  {factor}: {count}")

    print(f"\n✓ Result saved to: {output_dir / f'experiment_run_{experiment_id}.json'}")


def main():
    parser = argparse.ArgumentParser(description="Snap and Say Oracle Benchmark")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to run")

    # benchmark command (legacy)
    bench_parser = subparsers.add_parser("run", help="Run standard benchmark")
    bench_parser.add_argument("--limit", type=int, default=250)
    bench_parser.add_argument("--complexity", choices=["simple", "complex"])
    bench_parser.add_argument("--seed", type=int, default=42)
    bench_parser.add_argument("--batch-size", type=int, default=50)
    bench_parser.add_argument("--resume", action="store_true")
    bench_parser.add_argument("--delay", type=float, default=1.0)
    bench_parser.add_argument("--max-turns", type=int, default=3)
    bench_parser.add_argument("--provider", type=str, help="LLM provider (openai, google)")
    bench_parser.add_argument("--model", type=str, help="Specific model name")

    # experiment command
    exp_parser = subparsers.add_parser("experiment", help="Run prompt experiment")
    exp_parser.add_argument("--prompt", type=str, required=True, help="Prompt version ID (e.g. v2)")
    exp_parser.add_argument("--limit", type=int, default=5)
    exp_parser.add_argument("--complexity", choices=["simple", "complex"], default="simple")
    exp_parser.add_argument("--seed", type=int, default=42)
    exp_parser.add_argument("--provider", type=str, help="LLM provider (openai, google)")
    exp_parser.add_argument("--model", type=str, help="Specific model name")

    # history command
    subparsers.add_parser("history", help="View experiment history")

    # optimize command
    opt_parser = subparsers.add_parser("optimize", help="Suggest improvements")
    opt_parser.add_argument("--experiment-id", type=str, help="Experiment ID to analyze")
    opt_parser.add_argument("--provider", type=str, help="LLM provider (openai, google)")
    opt_parser.add_argument("--model", type=str, help="Specific model name")

    # Global args
    parser.add_argument("--output-dir", type=str, default="benchmark_output")
    parser.add_argument("--api-url", type=str, default=settings.FRONTEND_URL.replace(":3000", ":8000"))
    parser.add_argument("--email", type=str, help="Test user email (or ENV: TEST_EMAIL)")
    parser.add_argument("--password", type=str, help="Test user password (or ENV: TEST_PASSWORD)")

    args = parser.parse_args()

    # Env / Settings fallback
    args.email = args.email or settings.TEST_EMAIL or os.getenv("TEST_EMAIL")
    args.password = args.password or settings.TEST_PASSWORD or os.getenv("TEST_PASSWORD")
    if not args.email:
        args.email = os.getenv("TEST_EMAIL")
    if not args.password:
        args.password = os.getenv("TEST_PASSWORD")

    if not args.email or not args.password:
        parser.error("Email and password are required.")

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
