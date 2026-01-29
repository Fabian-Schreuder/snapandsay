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
from typing import Any

from app.benchmarking.experiment_log import ExperimentLog
from app.benchmarking.metrics import LatencyTracker, MetricsCalculator
from app.benchmarking.nutrition5k_loader import Nutrition5kLoader
from app.benchmarking.oracle_runner import OracleRunner
from app.benchmarking.prompt_optimizer import PromptOptimizer
from app.benchmarking.prompts import PromptRegistry
from app.benchmarking.schemas import NutritionDish
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


def generate_report(
    results: list[dict],
    dishes: list[NutritionDish],
    args: argparse.Namespace,
    latency_tracker: LatencyTracker,
) -> dict[str, Any]:
    """
    Generate comprehensive benchmark report with MAE and latency statistics.
    """
    # Build ground truth lookup
    ground_truth_map = {d.dish_id: d for d in dishes}

    # Calculate MAE metrics
    metrics_calc = MetricsCalculator()
    mae_results = []

    for result in results:
        dish_id = result["dish_id"]
        if dish_id in ground_truth_map and result.get("success"):
            gt = ground_truth_map[dish_id]
            dish_mae = metrics_calc.calculate_dish_mae(result.get("final_data"), gt)
            mae_results.append(dish_mae)

    aggregate_mae = metrics_calc.aggregate_mae(mae_results)
    within_threshold = metrics_calc.calculate_within_threshold(mae_results, ground_truth_map, 0.10)

    # Update aggregate with threshold percentages
    aggregate_mae.within_10_pct_calories = within_threshold.get("calories", 0.0)
    aggregate_mae.within_10_pct_protein = within_threshold.get("protein", 0.0)
    aggregate_mae.within_10_pct_fat = within_threshold.get("fat", 0.0)
    aggregate_mae.within_10_pct_carbs = within_threshold.get("carbs", 0.0)

    # Calculate latency statistics
    aggregate_latency = latency_tracker.aggregate()

    # Calculate accuracy metrics
    total = len(results)
    success_count = sum(1 for r in results if r.get("success"))
    total_turns = sum(r.get("turns", 0) for r in results)
    clarification_triggered = sum(1 for r in results if r.get("turns", 0) > 0)

    # Per-complexity breakdown
    simple_results = [
        r
        for r in results
        if ground_truth_map.get(
            r["dish_id"],
            NutritionDish(
                dish_id="",
                total_calories=0,
                total_mass=0,
                total_fat=0,
                total_carb=0,
                total_protein=0,
                ingredients=[],
                complexity="unknown",
            ),
        ).complexity
        == "simple"
    ]
    complex_results = [
        r
        for r in results
        if ground_truth_map.get(
            r["dish_id"],
            NutritionDish(
                dish_id="",
                total_calories=0,
                total_mass=0,
                total_fat=0,
                total_carb=0,
                total_protein=0,
                ingredients=[],
                complexity="unknown",
            ),
        ).complexity
        == "complex"
    ]

    simple_success = sum(1 for r in simple_results if r.get("success"))
    complex_success = sum(1 for r in complex_results if r.get("success"))

    report = {
        "metadata": {
            "timestamp": datetime.now(UTC).isoformat(),
            "seed": args.seed,
            "limit": args.limit,
            "complexity_filter": args.complexity,
            "total_dishes": total,
            "simple_dishes": len(simple_results),
            "complex_dishes": len(complex_results),
        },
        "accuracy": {
            "success_rate": success_count / total if total > 0 else 0.0,
            "success_rate_simple": simple_success / len(simple_results) if simple_results else 0.0,
            "success_rate_complex": complex_success / len(complex_results) if complex_results else 0.0,
            "total_clarification_turns": total_turns,
            "avg_clarification_turns": total_turns / total if total > 0 else 0.0,
            "clarification_trigger_rate": clarification_triggered / total if total > 0 else 0.0,
        },
        "wfr_comparison": aggregate_mae.to_dict(),
        "latency": aggregate_latency.to_dict(),
        "results": [],
    }

    # Add per-dish details
    for result in results:
        dish_id = result["dish_id"]
        gt = ground_truth_map.get(dish_id)

        dish_detail = {
            "dish_id": dish_id,
            "success": result.get("success"),
            "turns": result.get("turns", 0),
            "latency_seconds": round(result.get("latency_seconds", 0), 2),
            "log_id": result.get("log_id"),
            "error": result.get("error"),
        }

        if gt and result.get("success"):
            dish_detail["ground_truth"] = {
                "calories": gt.total_calories,
                "protein": gt.total_protein,
                "fat": gt.total_fat,
                "carbs": gt.total_carb,
            }

            # Extract predicted totals
            final_data = result.get("final_data", {})
            items = final_data.get("items", [])
            pred_calories = sum(item.get("calories", 0) or 0 for item in items)
            pred_protein = sum(item.get("protein", 0) or 0 for item in items)
            pred_fat = sum(item.get("fats", 0) or 0 for item in items)
            pred_carbs = sum(item.get("carbs", 0) or 0 for item in items)

            dish_detail["predicted"] = {
                "calories": pred_calories,
                "protein": pred_protein,
                "fat": pred_fat,
                "carbs": pred_carbs,
            }

            dish_detail["mae"] = {
                "calories": abs(pred_calories - gt.total_calories),
                "protein": abs(pred_protein - gt.total_protein),
                "fat": abs(pred_fat - gt.total_fat),
                "carbs": abs(pred_carbs - gt.total_carb),
            }

        report["results"].append(dish_detail)

    return report


async def main_async(args):
    """Main async benchmark execution."""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize components
    prompts_dir = Path(__file__).parent / "prompts"
    prompt_registry = PromptRegistry(prompts_dir)
    experiment_log = ExperimentLog(output_dir / "experiments")
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
        detail_file = output_dir / "experiments" / f"experiment_{experiment_id}.json"

        if not detail_file.exists():
            print(f"Experiment detail not found: {experiment_id}")
            await optimizer.close()
            return

        with open(detail_file) as f:
            from app.benchmarking.experiment_log import ExperimentResult

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

    # 6. Generate Comprehensive Report
    # Recreate latency tracker from results if resuming
    latency_tracker = LatencyTracker()
    dishes_map = {d.dish_id: d for d in all_dishes}
    for r in results:
        dish = dishes_map.get(r["dish_id"])
        complexity = dish.complexity if dish else "unknown"
        latency_tracker.record(r["dish_id"], r.get("latency_seconds", 0), complexity)

    report = generate_report(results, all_dishes, args, latency_tracker)

    # 7. Print Summary
    print("\n" + "=" * 60)
    print("ORACLE BENCHMARKING REPORT")
    print("=" * 60)
    print(f"\nTimestamp: {report['metadata']['timestamp']}")
    print(f"Seed: {report['metadata']['seed']}")
    print(f"Total Dishes: {report['metadata']['total_dishes']}")
    print(f"  Simple: {report['metadata']['simple_dishes']}")
    print(f"  Complex: {report['metadata']['complex_dishes']}")

    print("\n--- Accuracy ---")
    acc = report["accuracy"]
    print(f"Success Rate: {acc['success_rate']:.1%}")
    print(f"  Simple: {acc['success_rate_simple']:.1%}")
    print(f"  Complex: {acc['success_rate_complex']:.1%}")
    print(f"Avg Clarification Turns: {acc['avg_clarification_turns']:.2f}")
    print(f"Clarification Trigger Rate: {acc['clarification_trigger_rate']:.1%}")

    print("\n--- WFR Ground Truth Comparison (MAE) ---")
    wfr = report["wfr_comparison"]
    mae = wfr["mae"]
    print(f"Calories MAE: {mae['calories']:.1f} kcal")
    print(f"Protein MAE: {mae['protein']:.1f} g")
    print(f"Fat MAE: {mae['fat']:.1f} g")
    print(f"Carbs MAE: {mae['carbs']:.1f} g")
    within = wfr["within_10_percent"]
    print("\nWithin ±10% of Ground Truth:")
    print(f"  Calories: {within['calories']:.1%}")
    print(f"  Protein: {within['protein']:.1%}")
    print(f"  Fat: {within['fat']:.1%}")
    print(f"  Carbs: {within['carbs']:.1%}")

    print("\n--- Latency ---")
    lat = report["latency"]
    print(f"Mean: {lat['mean_seconds']:.1f}s")
    print(f"p50: {lat['p50_seconds']:.1f}s")
    print(f"p95: {lat['p95_seconds']:.1f}s")
    print(f"p99: {lat['p99_seconds']:.1f}s")
    print(f"  Simple Mean: {lat['per_complexity']['simple_mean']:.1f}s")
    print(f"  Complex Mean: {lat['per_complexity']['complex_mean']:.1f}s")

    # 8. Save Full Report
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f"benchmark_report_{ts}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n✓ Full report saved to: {report_file.absolute()}")

    # Also save summary separately for easy access
    summary_file = output_dir / f"benchmark_summary_{ts}.json"
    summary = {k: v for k, v in report.items() if k != "results"}
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"✓ Summary saved to: {summary_file.absolute()}")


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
