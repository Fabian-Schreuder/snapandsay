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
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.benchmarking.experiment_log import ExperimentLog, ExperimentResult
from app.benchmarking.metrics import AggregateMAE, LatencyTracker, MetricsCalculator
from app.benchmarking.nutrition5k_loader import Nutrition5kLoader
from app.benchmarking.oracle_runner import OracleRunner
from app.benchmarking.prompt_optimizer import PromptOptimizer
from app.benchmarking.prompts import PromptRegistry
from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_checkpoint(checkpoint_file: Path) -> tuple[list[dict], set[str], dict]:
    """Load results and metadata from checkpoint file."""
    if not checkpoint_file.exists():
        return [], set(), {}

    with open(checkpoint_file) as f:
        data = json.load(f)

    results = data.get("results", [])
    metadata = data.get("metadata", {})
    processed_ids = {r["dish_id"] for r in results}
    logger.info(f"Loaded checkpoint with {len(processed_ids)} processed dishes")
    return results, processed_ids, metadata


def save_checkpoint(checkpoint_file: Path, results: list[dict], metadata: dict):
    """Save current results to checkpoint file with atomic writes."""
    data = {"metadata": metadata, "results": results}
    tmp_file = checkpoint_file.with_suffix(".tmp")
    with open(tmp_file, "w") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp_file, checkpoint_file)
    logger.info(f"Checkpoint saved: {len(results)} results")


async def _run_sweep(args, output_dir: Path):
    """Run threshold sweep experiment."""
    logger.info("Initializing Loader for sweep...")
    loader = Nutrition5kLoader()
    dishes = loader.load_dishes(seed=args.seed, complexity=args.complexity, limit=args.limit)
    if not dishes:
        print("No dishes found.")
        return

    clinical_thresholds = [5.0, 8.0, 10.0, 12.0, 15.0, 20.0]
    confidence_thresholds = [0.70, 0.75, 0.80, 0.85, 0.90]

    sweep_results = []

    print("\nStarting Threshold Sweep (Grid Search)")
    print(f"Dishes: {len(dishes)}")
    print(f"Clinical Thresholds: {clinical_thresholds}")
    print(f"Confidence Thresholds: {confidence_thresholds}")

    runner = OracleRunner(
        api_url=args.api_url,
        email=args.email,
        password=args.password,
        max_turns=3,
        mode="agentic",
        timeout=180.0,
    )
    await runner.login()

    for c_thresh in clinical_thresholds:
        for conf_thresh in confidence_thresholds:
            print(f"\nTesting combo: clinical_threshold={c_thresh}, confidence_threshold={conf_thresh}")
            combo_results = []
            for dish in dishes:
                for attempt in range(getattr(args, "retries", 3) + 1):
                    try:
                        res = await runner.run_dish(
                            dish,
                            provider=args.provider,
                            model=args.model,
                            clinical_threshold=c_thresh,
                            confidence_threshold=conf_thresh,
                        )
                        combo_results.append(res)
                        break
                    except Exception as e:
                        if attempt == getattr(args, "retries", 3):
                            logger.error(f"Failed {dish.dish_id}: {e}")

            metrics_calc = MetricsCalculator()
            metrics = metrics_calc.calculate_all(
                combo_results,
                [d.dish_id for d in dishes if d.complexity == "simple"],
                [d.dish_id for d in dishes if d.complexity == "complex"],
            )

            mae = metrics["mae_metrics"]["total"]
            ra = metrics.get("routing_accuracy", {})
            tnr_str = f"{ra.get('tnr', 0):.3f}" if not ra.get("skipped") else "N/A"
            tpr_str = f"{ra.get('tpr', 0):.3f}" if not ra.get("skipped") else "N/A"
            mae_str = f"{mae.mean_calories:.2f}" if mae.sample_count > 0 else "N/A"
            fp_count = ra.get("fp", 0)

            print(f"  TNR={tnr_str}, TPR={tpr_str}, MAE={mae_str}, FP={fp_count}")
            sweep_results.append(
                {"clinical_threshold": c_thresh, "confidence_threshold": conf_thresh, "metrics": metrics}
            )

    sweep_file = output_dir / "sweep_results.json"
    with open(sweep_file, "w") as f:
        json.dump(sweep_results, f, indent=2, default=str)
    print(f"\nSweep completed. Results saved to {sweep_file}")
    await runner.close()


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

    if args.command == "compare":
        await _run_compare(args, output_dir)
        return

    if args.command == "sweep":
        await _run_sweep(args, output_dir)
        return

    # Original benchmark flow...
    checkpoint_file = output_dir / "benchmark_checkpoint.json"
    results = []
    processed_ids: set[str] = set()
    mode = getattr(args, "mode", "agentic")

    # Load checkpoint if resuming
    if args.resume:
        results, processed_ids, ckpt_metadata = load_checkpoint(checkpoint_file)
        if ckpt_metadata is not None:
            ckpt_version = ckpt_metadata.get("checkpoint_version", 1)
            force_resume = getattr(args, "force_resume", False)

            if ckpt_version < 2:
                # Legacy checkpoint — no mode info
                if mode != "agentic" and not force_resume:
                    logger.error(
                        f"Checkpoint predates mode support (version {ckpt_version}). "
                        f"Cannot resume with --mode {mode}. Use --force-resume to override."
                    )
                    sys.exit(1)
                if mode != "agentic":
                    logger.warning("Checkpoint predates mode support. Forcing resume as requested.")
            else:
                # Validate parameters match
                mismatches = []
                for key in ("seed", "complexity", "mode", "limit"):
                    ckpt_val = ckpt_metadata.get(key)
                    arg_val = getattr(args, key, None)
                    if ckpt_val is not None and arg_val is not None and ckpt_val != arg_val:
                        mismatches.append(f"{key}: checkpoint={ckpt_val}, current={arg_val}")

                if mismatches and not force_resume:
                    logger.error(
                        f"Checkpoint parameter mismatch: {'; '.join(mismatches)}. "
                        f"Use --force-resume to override."
                    )
                    sys.exit(1)
                if mismatches:
                    logger.warning(f"Forcing resume despite parameter mismatches: {'; '.join(mismatches)}")

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
            mode=mode,
            timeout=getattr(args, "timeout", 180.0),
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

        # Checkpoint metadata
        ckpt_meta = {
            "seed": args.seed,
            "complexity": args.complexity,
            "batch_size": args.batch_size,
            "mode": mode,
            "limit": args.limit,
            "checkpoint_version": 2,
        }

        retries = getattr(args, "retries", 3)

        # 5. Run Loop with Batching and Retry
        run_start_time = time.perf_counter()
        dishes_processed_this_run = 0
        try:
            for _i, dish in enumerate(dishes):
                batch_idx = (len(results) // args.batch_size) + 1
                in_batch_idx = (len(results) % args.batch_size) + 1

                logger.info(
                    f"--- Batch {batch_idx}, Item {in_batch_idx}/{args.batch_size} | "
                    f"Overall {len(results)+1}/{len(all_dishes)}: {dish.dish_id} ---"
                )

                # Retry loop
                result = None
                for attempt in range(retries + 1):
                    try:
                        result = await runner.run_dish(
                            dish,
                            provider=args.provider,
                            model=args.model,
                            dish_timeout_seconds=getattr(args, "timeout", 120.0),
                        )
                        # Check for retryable failures
                        if result["success"] or attempt >= retries:
                            break
                        error = result.get("error", "")
                        keyword_retryable = any(
                            kw in error.lower() for kw in ("timeout", "connection", "network")
                        )
                        http_retryable = any(
                            f"status code {code}" in error.lower()
                            or f" {code} " in error
                            or error.strip().endswith(str(code))
                            for code in (429, 500, 502, 503, 504)
                        )
                        if not (keyword_retryable or http_retryable):
                            break
                        logger.warning(
                            f"[{dish.dish_id}] Retryable failure (attempt {attempt+1}/{retries+1}): {error}"
                        )
                        await asyncio.sleep(2**attempt)
                    except (TimeoutError, httpx.TimeoutException) as e:
                        logger.warning(f"[{dish.dish_id}] Timeout on attempt {attempt+1}/{retries+1}: {e}")
                        if attempt >= retries:
                            result = {
                                "dish_id": dish.dish_id,
                                "success": False,
                                "error": f"timeout: {e}",
                                "turns": 0,
                                "log_id": None,
                            }
                        else:
                            await asyncio.sleep(2**attempt)
                    except Exception as e:
                        logger.error(f"[{dish.dish_id}] Exception on attempt {attempt+1}: {e}")
                        if attempt >= retries:
                            result = {
                                "dish_id": dish.dish_id,
                                "success": False,
                                "error": str(e),
                                "turns": 0,
                                "log_id": None,
                            }
                        else:
                            await asyncio.sleep(2**attempt)

                results.append(result)
                dishes_processed_this_run += 1

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

                # Per-dish checkpoint save (atomic)
                save_checkpoint(checkpoint_file, results, ckpt_meta)

                # Batch progress logging
                if len(results) % args.batch_size == 0:
                    logger.info(f"Batch {batch_idx} complete ({len(results)} total)")

                # Progress reporting every 50 dishes
                if dishes_processed_this_run % 50 == 0 and dishes_processed_this_run > 0:
                    elapsed = time.perf_counter() - run_start_time
                    success_count = sum(1 for r in results if r.get("success", False))
                    success_rate = (success_count / len(results)) * 100
                    avg_per_dish = elapsed / dishes_processed_this_run
                    remaining_dishes = len(all_dishes) - len(results)
                    remaining = remaining_dishes * avg_per_dish
                    logger.info(
                        f"Progress: {len(results)}/{len(all_dishes)} dishes "
                        f"({success_rate:.1f}% success, elapsed: {elapsed:.0f}s, "
                        f"ETA: {remaining:.0f}s)"
                    )

                # Brief pause to avoid rate limiting
                await asyncio.sleep(args.delay)

        finally:
            await runner.close()
            # Final checkpoint save
            save_checkpoint(checkpoint_file, results, ckpt_meta)

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
                "clarification_history": result.get("clarification_history", []),
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
                    "clarification_history": result.get("clarification_history", []),
                }
            )

    aggregate_mae = metrics_calc.aggregate_mae(mae_results)
    aggregate_latency = latency_tracker.aggregate()
    complexity_stats = metrics_calc.aggregate_complexity(per_dish_results)

    # Per-stratum MAE
    dish_complexity_map = {did: d.complexity for did, d in dishes_map.items()}
    stratum_mae = metrics_calc.aggregate_mae_by_stratum(mae_results, dish_complexity_map)

    # Routing accuracy (only meaningful for agentic mode)
    routing_accuracy = None
    if mode == "agentic":
        routing_accuracy = metrics_calc.calculate_routing_accuracy(per_dish_results, dish_complexity_map)

    # Build metrics dict
    metrics_dict = {
        **aggregate_mae.to_dict()["mae"],
        "complexity_stats": complexity_stats.to_dict(),
        "stratum_mae": {k: v.to_dict() for k, v in stratum_mae.items()},
    }
    if routing_accuracy is not None:
        metrics_dict["routing_accuracy"] = routing_accuracy

    # Create ExperimentResult — filter password from config
    experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    config = {k: v for k, v in vars(args).items() if k != "password"}
    final_result = ExperimentResult(
        experiment_id=f"run_{experiment_id}",
        prompt_version="baseline_run",
        timestamp=datetime.now(UTC).isoformat(),
        metrics=metrics_dict,
        latency_stats=aggregate_latency.to_dict(),
        per_dish_results=per_dish_results,
        config=config,
    )

    experiment_log.log_experiment(final_result)

    # 7. Print Summary
    print("\n" + "=" * 60)
    print("ORACLE BENCHMARKING REPORT")
    print("=" * 60)
    print(f"\nTimestamp: {final_result.timestamp}")
    print(f"Mode: {mode}")
    print(f"Total Dishes: {len(results)}")

    print("\n--- WFR Ground Truth Comparison (MAE) ---")
    mae = final_result.metrics
    print(f"Calories MAE: {mae['calories']:.1f} kcal")
    print(f"Protein MAE: {mae['protein']:.1f} g")

    # Per-stratum MAE
    if stratum_mae:
        print("\n--- Per-Stratum MAE ---")
        for stratum, agg in sorted(stratum_mae.items()):
            agg_dict = agg.to_dict()["mae"]
            print(f"  {stratum}: Calories={agg_dict['calories']:.1f}, Protein={agg_dict['protein']:.1f}")

    # Routing accuracy
    if routing_accuracy and not routing_accuracy.get("skipped"):
        print("\n--- Routing Accuracy (Agentic Mode) ---")
        ra = routing_accuracy
        print(
            f"  TNR: {ra['tnr']:.3f} [{ra.get('tnr_ci_lower', 0):.3f}, "
            f"{ra.get('tnr_ci_upper', 0):.3f}] (TN={ra['tn']}, FP={ra['fp']})"
        )
        print(
            f"  TPR: {ra['tpr']:.3f} [{ra.get('tpr_ci_lower', 0):.3f}, "
            f"{ra.get('tpr_ci_upper', 0):.3f}] (TP={ra['tp']}, FN={ra['fn']})"
        )
    elif mode != "agentic":
        print(f"\n  Routing accuracy skipped (only meaningful for agentic mode, current: {mode})")

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


async def _run_compare(args, output_dir: Path):
    """Cross-mode comparison: per-stratum MAE table, TNR/TPR, turn reduction."""
    metrics_calc = MetricsCalculator()

    mode_ids = {
        "agentic": args.agentic_id,
        "single-shot": args.single_shot_id,
        "naive-always-ask": args.naive_id,
    }

    # Load experiment data
    mode_data: dict[str, dict] = {}
    for mode_name, exp_id in mode_ids.items():
        exp_file = output_dir / f"experiment_{exp_id}.json"
        if not exp_file.exists():
            logger.error(f"Experiment file not found: {exp_file}")
            sys.exit(1)
        with open(exp_file) as f:
            mode_data[mode_name] = json.load(f)

    # Validate matching parameters
    if not args.force:
        configs = {m: d.get("config", {}) for m, d in mode_data.items()}
        ref = configs["agentic"]
        for mode_name, cfg in configs.items():
            for key in ("seed", "limit", "complexity"):
                ref_val = ref.get(key)
                cfg_val = cfg.get(key)
                if ref_val is not None and cfg_val is not None and ref_val != cfg_val:
                    logger.error(
                        f"Parameter mismatch between agentic and {mode_name}: "
                        f"{key}={ref_val} vs {cfg_val}. Use --force to override."
                    )
                    sys.exit(1)

    # Load dishes for ground truth and complexity map
    seed = args.seed
    loader = Nutrition5kLoader()
    all_dishes = loader.load_dishes(seed=seed)
    dishes_map = {d.dish_id: d for d in all_dishes}
    dish_complexity_map = {did: d.complexity for did, d in dishes_map.items()}

    # Normalize per-dish results and compute MAE for each mode
    mode_mae_results: dict[str, list] = {}
    mode_per_dish: dict[str, list[dict]] = {}

    for mode_name, data in mode_data.items():
        per_dish = data.get("per_dish_results", [])
        mae_results = []
        for r in per_dish:
            dish_id = r["dish_id"]
            dish = dishes_map.get(dish_id)
            if not dish:
                logger.warning(f"[{mode_name}] Dish {dish_id} not found in dataset — skipping")
                continue

            # Handle schema divergence: run results have "mae" key, experiment has "final_data"
            if r.get("success") and "mae" in r:
                # Already computed MAE — reconstruct DishMAE from stored dict
                from app.benchmarking.metrics import DishMAE

                mae_dict = r["mae"]
                mae_results.append(
                    DishMAE(
                        dish_id=dish_id,
                        calories=mae_dict.get("calories"),
                        protein=mae_dict.get("protein"),
                        fat=mae_dict.get("fat"),
                        carbs=mae_dict.get("carbs"),
                        success=True,
                    )
                )
            elif r.get("success") and "final_data" in r:
                # Recompute MAE from final_data
                mae_results.append(metrics_calc.calculate_dish_mae(r["final_data"], dish))

        mode_mae_results[mode_name] = mae_results
        mode_per_dish[mode_name] = per_dish

    # Per-stratum MAE for each mode
    mode_stratum_mae: dict[str, dict[str, AggregateMAE]] = {}
    mode_total_mae: dict[str, AggregateMAE] = {}
    for mode_name, mae_results in mode_mae_results.items():
        mode_stratum_mae[mode_name] = metrics_calc.aggregate_mae_by_stratum(mae_results, dish_complexity_map)
        mode_total_mae[mode_name] = metrics_calc.aggregate_mae(mae_results)

    # TNR/TPR for agentic mode
    routing_acc = metrics_calc.calculate_routing_accuracy(mode_per_dish["agentic"], dish_complexity_map)

    # Turn reduction
    turn_reduction = metrics_calc.calculate_turn_reduction(
        mode_per_dish["agentic"], mode_per_dish["naive-always-ask"]
    )

    # Total turns per mode
    mode_turns = {m: sum(r.get("turns", 0) for r in per_dish) for m, per_dish in mode_per_dish.items()}

    # Print comparison table
    print("\n" + "=" * 70)
    print("CROSS-MODE COMPARISON")
    print("=" * 70)

    header = f"{'Mode':<22} {'Simple MAE':>12} {'Complex MAE':>12} {'Total MAE':>12} {'Turns':>8}"
    print(f"\n{header}")
    print("-" * 70)

    for mode_name in ["agentic", "single-shot", "naive-always-ask"]:
        simple_mae = mode_stratum_mae[mode_name].get("simple")
        complex_mae = mode_stratum_mae[mode_name].get("complex")
        total_mae = mode_total_mae[mode_name]

        simple_cal = (
            f"{simple_mae.mean_calories:.1f}" if simple_mae and simple_mae.sample_count > 0 else "N/A"
        )
        complex_cal = (
            f"{complex_mae.mean_calories:.1f}" if complex_mae and complex_mae.sample_count > 0 else "N/A"
        )
        total_cal = f"{total_mae.mean_calories:.1f}" if total_mae.sample_count > 0 else "N/A"
        turns = mode_turns[mode_name]

        print(f"{mode_name:<22} {simple_cal:>12} {complex_cal:>12} {total_cal:>12} {turns:>8}")

    # TNR/TPR
    if routing_acc and not routing_acc.get("skipped"):
        print(f"\nRouting Accuracy (agentic): " f"TNR={routing_acc['tnr']:.3f}, TPR={routing_acc['tpr']:.3f}")
        ra = routing_acc
        print(f"  TN={ra['tn']}, FP={ra['fp']}, TP={ra['tp']}, FN={ra['fn']}")

    # Turn reduction
    if "error" not in turn_reduction:
        print(f"\nTurn Reduction: {turn_reduction['turn_reduction_pct']:.1f}%")
        print(
            f"  Agentic turns: {turn_reduction['agentic_total_turns']}, "
            f"Naive turns: {turn_reduction['naive_total_turns']}"
        )
    else:
        print(f"\nTurn Reduction: {turn_reduction['error']}")

    # Cross-mode statistical comparison (agentic vs single-shot)
    if mode_mae_results.get("agentic") and mode_mae_results.get("single-shot"):
        comparison = metrics_calc.compare_modes(mode_mae_results["agentic"], mode_mae_results["single-shot"])
        print("\n--- Effect Size Analysis (Agentic vs Single-Shot) ---")
        print(f"  {comparison['summary']}")
        for macro, d in comparison["effect_sizes_cohens_d"].items():
            d_str = f"{d:.3f}" if d is not None else "N/A"
            print(f"  {macro}: Cohen's d = {d_str}")


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
    bench_parser.add_argument(
        "--force-resume", action="store_true", help="Resume even if parameters mismatch"
    )
    bench_parser.add_argument("--delay", type=float, default=1.0)
    bench_parser.add_argument("--max-turns", type=int, default=3)
    bench_parser.add_argument(
        "--mode",
        choices=["agentic", "single-shot", "naive-always-ask"],
        default="agentic",
        help="Runner mode: agentic (default), single-shot, or naive-always-ask",
    )
    bench_parser.add_argument("--timeout", type=float, default=180.0, help="Per-dish timeout in seconds")
    bench_parser.add_argument(
        "--retries",
        type=int,
        default=3,
        choices=range(0, 11),
        metavar="N",
        help="Max retries per dish on failure (0-10, default: 3)",
    )
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

    # compare command
    compare_parser = subparsers.add_parser("compare", help="Compare results across modes")
    compare_parser.add_argument("--agentic-id", type=str, required=True, help="Agentic mode experiment ID")
    compare_parser.add_argument(
        "--single-shot-id", type=str, required=True, help="Single-shot mode experiment ID"
    )
    compare_parser.add_argument(
        "--naive-id", type=str, required=True, help="Naive-always-ask mode experiment ID"
    )
    compare_parser.add_argument("--force", action="store_true", help="Skip parameter validation")
    compare_parser.add_argument("--seed", type=int, default=42, help="Seed for dish loading")

    # sweep command
    sweep_parser = subparsers.add_parser("sweep", help="Run threshold parameter sweep analysis")
    sweep_parser.add_argument("--limit", type=int, default=50)
    sweep_parser.add_argument("--complexity", choices=["simple", "complex"])
    sweep_parser.add_argument("--seed", type=int, default=42)
    sweep_parser.add_argument("--provider", type=str, help="LLM provider (openai, google)")
    sweep_parser.add_argument("--model", type=str, help="Specific model name")

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
