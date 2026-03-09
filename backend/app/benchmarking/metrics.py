"""
Metrics Module for Oracle Benchmarking.

Calculates Mean Absolute Error (MAE) against WFR ground truth
and tracks computational latency per dish.
"""

import logging
import math
import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from app.benchmarking.schemas import NutritionDish

logger = logging.getLogger(__name__)


@dataclass
class DishMAE:
    """MAE metrics for a single dish."""

    dish_id: str
    calories: float | None = None
    protein: float | None = None
    fat: float | None = None
    carbs: float | None = None
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "dish_id": self.dish_id,
            "calories": self.calories,
            "protein": self.protein,
            "fat": self.fat,
            "carbs": self.carbs,
            "success": self.success,
        }


@dataclass
class AggregateMAE:
    """Aggregate MAE metrics across all dishes."""

    # Mean MAE
    mean_calories: float = 0.0
    mean_protein: float = 0.0
    mean_fat: float = 0.0
    mean_carbs: float = 0.0

    # Standard deviation
    std_calories: float = 0.0
    std_protein: float = 0.0
    std_fat: float = 0.0
    std_carbs: float = 0.0

    # Percentage within ±10% of ground truth
    within_10_pct_calories: float = 0.0
    within_10_pct_protein: float = 0.0
    within_10_pct_fat: float = 0.0
    within_10_pct_carbs: float = 0.0

    # 95% confidence intervals
    ci_lower_calories: float | None = None
    ci_upper_calories: float | None = None
    ci_lower_protein: float | None = None
    ci_upper_protein: float | None = None
    ci_lower_fat: float | None = None
    ci_upper_fat: float | None = None
    ci_lower_carbs: float | None = None
    ci_upper_carbs: float | None = None

    # Count of valid samples
    sample_count: int = 0

    def to_dict(self) -> dict:
        result = {
            "mae": {
                "calories": round(self.mean_calories, 2),
                "protein": round(self.mean_protein, 2),
                "fat": round(self.mean_fat, 2),
                "carbs": round(self.mean_carbs, 2),
            },
            "std_dev": {
                "calories": round(self.std_calories, 2),
                "protein": round(self.std_protein, 2),
                "fat": round(self.std_fat, 2),
                "carbs": round(self.std_carbs, 2),
            },
            "within_10_percent": {
                "calories": round(self.within_10_pct_calories, 2),
                "protein": round(self.within_10_pct_protein, 2),
                "fat": round(self.within_10_pct_fat, 2),
                "carbs": round(self.within_10_pct_carbs, 2),
            },
            "sample_count": self.sample_count,
        }
        ci = {}
        for macro in ("calories", "protein", "fat", "carbs"):
            lower = getattr(self, f"ci_lower_{macro}")
            upper = getattr(self, f"ci_upper_{macro}")
            if lower is not None and upper is not None:
                ci[macro] = (round(lower, 2), round(upper, 2))
        if ci:
            result["confidence_interval_95"] = ci
        return result


@dataclass
class DishLatency:
    """Latency metrics for a single dish."""

    dish_id: str
    latency_seconds: float
    complexity: str = "unknown"


@dataclass
class AggregateLatency:
    """Aggregate latency metrics across all dishes."""

    mean_seconds: float = 0.0
    p50_seconds: float = 0.0
    p95_seconds: float = 0.0
    p99_seconds: float = 0.0
    simple_mean: float = 0.0
    complex_mean: float = 0.0
    sample_count: int = 0

    def to_dict(self) -> dict:
        return {
            "mean_seconds": round(self.mean_seconds, 2),
            "p50_seconds": round(self.p50_seconds, 2),
            "p95_seconds": round(self.p95_seconds, 2),
            "p99_seconds": round(self.p99_seconds, 2),
            "per_complexity": {
                "simple_mean": round(self.simple_mean, 2),
                "complex_mean": round(self.complex_mean, 2),
            },
            "sample_count": self.sample_count,
        }


def _t_critical(df: int, confidence: float = 0.95) -> float:
    """Look up two-tailed t-critical value for given degrees of freedom.

    Uses a lookup table for df 1-30, falls back to z-score for df > 30.
    """
    # t-critical values for 95% confidence (two-tailed) by df
    t_table_95 = {
        1: 12.706,
        2: 4.303,
        3: 3.182,
        4: 2.776,
        5: 2.571,
        6: 2.447,
        7: 2.365,
        8: 2.306,
        9: 2.262,
        10: 2.228,
        11: 2.201,
        12: 2.179,
        13: 2.160,
        14: 2.145,
        15: 2.131,
        16: 2.120,
        17: 2.110,
        18: 2.101,
        19: 2.093,
        20: 2.086,
        21: 2.080,
        22: 2.074,
        23: 2.069,
        24: 2.064,
        25: 2.060,
        26: 2.056,
        27: 2.052,
        28: 2.048,
        29: 2.045,
        30: 2.042,
    }
    z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}

    if confidence == 0.95 and df <= 30:
        return t_table_95[df]
    # For large df or non-95% confidence, use z-approximation
    return z_scores.get(confidence, 1.96)


def calculate_ci(values: list[float], confidence: float = 0.95) -> tuple[float, float]:
    """Compute confidence interval for a list of values using t-distribution.

    Uses t-critical values for n <= 31 (df <= 30) and z-scores for larger samples.

    Args:
        values: Sample values.
        confidence: Confidence level (default 0.95).

    Returns:
        Tuple of (ci_lower, ci_upper). Returns (mean, mean) if n < 2.
    """
    if not values:
        return (0.0, 0.0)
    mean = statistics.mean(values)
    if len(values) < 2:
        return (mean, mean)
    n = len(values)
    se = statistics.stdev(values) / math.sqrt(n)
    t = _t_critical(n - 1, confidence)
    margin = t * se
    return (mean - margin, mean + margin)


def calculate_cohens_d(group1: list[float], group2: list[float]) -> float | None:
    """Compute Cohen's d effect size between two groups using pooled SD.

    Args:
        group1: First group values.
        group2: Second group values.

    Returns:
        Cohen's d, or None if calculation is not meaningful.
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return None

    mean1 = statistics.mean(group1)
    mean2 = statistics.mean(group2)

    if mean1 == mean2:
        return 0.0

    var1 = statistics.variance(group1)
    var2 = statistics.variance(group2)
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)

    if pooled_var == 0:
        return None

    # Warn about unequal group sizes
    ratio = max(n1, n2) / min(n1, n2)
    if ratio > 2.0:
        logger.warning(
            "Group size ratio %.1f:1 exceeds 2:1 — pooled SD may be biased (n1=%d, n2=%d)",
            ratio,
            n1,
            n2,
        )

    return (mean1 - mean2) / math.sqrt(pooled_var)


def calculate_wilson_ci(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    """Compute Wilson score confidence interval for a proportion.

    Better than normal approximation for small samples and extreme proportions.

    Args:
        successes: Number of successes.
        total: Total trials.
        confidence: Confidence level (default 0.95).

    Returns:
        Tuple of (ci_lower, ci_upper).
    """
    if total == 0:
        return (0.0, 0.0)

    z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_scores.get(confidence, 1.96)
    z2 = z * z

    p = successes / total
    denominator = 1 + z2 / total
    centre = p + z2 / (2 * total)
    spread = z * math.sqrt((p * (1 - p) + z2 / (4 * total)) / total)

    lower = (centre - spread) / denominator
    upper = (centre + spread) / denominator

    return (max(0.0, lower), min(1.0, upper))


class MetricsCalculator:
    """
    Calculates MAE metrics by comparing predicted nutritional data
    against Nutrition5k WFR (Weighed Food Record) ground truth.
    """

    def calculate_dish_mae(self, predicted: dict[str, Any] | None, ground_truth: NutritionDish) -> DishMAE:
        """
        Calculate MAE for a single dish.

        Args:
            predicted: Agent's predicted nutritional data (from final_data)
            ground_truth: Nutrition5k ground truth dish

        Returns:
            DishMAE with absolute errors for each macro
        """
        if predicted is None:
            return DishMAE(dish_id=ground_truth.dish_id, success=False)

        # Extract predicted totals from items
        pred_calories = 0.0
        pred_protein = 0.0
        pred_fat = 0.0
        pred_carbs = 0.0

        items = predicted.get("items", [])
        for item in items:
            pred_calories += item.get("calories", 0) or 0
            pred_protein += item.get("protein", 0) or 0
            pred_fat += item.get("fats", 0) or 0
            pred_carbs += item.get("carbs", 0) or 0

        # Calculate absolute errors
        return DishMAE(
            dish_id=ground_truth.dish_id,
            calories=abs(pred_calories - ground_truth.total_calories),
            protein=abs(pred_protein - ground_truth.total_protein),
            fat=abs(pred_fat - ground_truth.total_fat),
            carbs=abs(pred_carbs - ground_truth.total_carb),
            success=True,
        )

    def aggregate_mae(
        self,
        results: list[DishMAE],
        ground_truths: dict[str, NutritionDish] | None = None,
    ) -> AggregateMAE:
        """Aggregate MAE metrics across all successfully processed dishes.

        Args:
            results: List of per-dish MAE results.
            ground_truths: Optional mapping of dish_id to ground truth for within-threshold calc.
        """
        # Filter to successful results with valid values
        valid_results = [r for r in results if r.success and r.calories is not None]

        if not valid_results:
            return AggregateMAE()

        # Extract values
        calories_errors = [r.calories for r in valid_results if r.calories is not None]
        protein_errors = [r.protein for r in valid_results if r.protein is not None]
        fat_errors = [r.fat for r in valid_results if r.fat is not None]
        carbs_errors = [r.carbs for r in valid_results if r.carbs is not None]

        # Calculate means
        agg = AggregateMAE(sample_count=len(valid_results))

        if calories_errors:
            agg.mean_calories = statistics.mean(calories_errors)
            agg.std_calories = statistics.stdev(calories_errors) if len(calories_errors) > 1 else 0.0
            agg.ci_lower_calories, agg.ci_upper_calories = calculate_ci(calories_errors)

        if protein_errors:
            agg.mean_protein = statistics.mean(protein_errors)
            agg.std_protein = statistics.stdev(protein_errors) if len(protein_errors) > 1 else 0.0
            agg.ci_lower_protein, agg.ci_upper_protein = calculate_ci(protein_errors)

        if fat_errors:
            agg.mean_fat = statistics.mean(fat_errors)
            agg.std_fat = statistics.stdev(fat_errors) if len(fat_errors) > 1 else 0.0
            agg.ci_lower_fat, agg.ci_upper_fat = calculate_ci(fat_errors)

        if carbs_errors:
            agg.mean_carbs = statistics.mean(carbs_errors)
            agg.std_carbs = statistics.stdev(carbs_errors) if len(carbs_errors) > 1 else 0.0
            agg.ci_lower_carbs, agg.ci_upper_carbs = calculate_ci(carbs_errors)

        # Wire up within_10_pct fields if ground truths provided
        if ground_truths:
            within = self.calculate_within_threshold(results, ground_truths)
            agg.within_10_pct_calories = within["calories"]
            agg.within_10_pct_protein = within["protein"]
            agg.within_10_pct_fat = within["fat"]
            agg.within_10_pct_carbs = within["carbs"]

        return agg

    def calculate_within_threshold(
        self,
        results: list[DishMAE],
        ground_truths: dict[str, NutritionDish],
        threshold_pct: float = 0.10,
    ) -> dict[str, float]:
        """
        Calculate percentage of predictions within ±threshold of ground truth.

        Args:
            results: List of DishMAE results
            ground_truths: Mapping of dish_id to ground truth NutritionDish
            threshold_pct: Threshold percentage (default 10% = 0.10)

        Returns:
            Dictionary with percentage within threshold for each macro
        """
        within = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
        total = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}

        for result in results:
            if not result.success or result.dish_id not in ground_truths:
                continue

            gt = ground_truths[result.dish_id]

            # Calories
            if result.calories is not None and gt.total_calories > 0:
                total["calories"] += 1
                if result.calories <= gt.total_calories * threshold_pct:
                    within["calories"] += 1

            # Protein
            if result.protein is not None and gt.total_protein > 0:
                total["protein"] += 1
                if result.protein <= gt.total_protein * threshold_pct:
                    within["protein"] += 1

            # Fat
            if result.fat is not None and gt.total_fat > 0:
                total["fat"] += 1
                if result.fat <= gt.total_fat * threshold_pct:
                    within["fat"] += 1

            # Carbs
            if result.carbs is not None and gt.total_carb > 0:
                total["carbs"] += 1
                if result.carbs <= gt.total_carb * threshold_pct:
                    within["carbs"] += 1

        return {macro: (within[macro] / total[macro] if total[macro] > 0 else 0.0) for macro in within}

    def aggregate_mae_by_stratum(
        self, results: list[DishMAE], dish_complexity_map: dict[str, str]
    ) -> dict[str, AggregateMAE]:
        """Aggregate MAE metrics grouped by complexity stratum (simple/complex).

        Args:
            results: List of DishMAE results.
            dish_complexity_map: Mapping of dish_id to complexity string.

        Returns:
            Dict mapping stratum label to AggregateMAE.
        """
        groups: dict[str, list[DishMAE]] = {}
        for r in results:
            stratum = dish_complexity_map.get(r.dish_id, "unknown")
            groups.setdefault(stratum, []).append(r)

        return {stratum: self.aggregate_mae(group) for stratum, group in groups.items()}

    def calculate_routing_accuracy(
        self, per_dish_results: list[dict], dish_complexity_map: dict[str, str]
    ) -> dict[str, Any]:
        """Calculate TNR/TPR for clarification routing decisions.

        Classification:
        - TN: simple dish + 0 turns (correctly suppressed)
        - FP: simple dish + >0 turns (unnecessary clarification)
        - TP: complex dish + >0 turns (correctly triggered)
        - FN: complex dish + 0 turns (missed clarification)

        Only meaningful for agentic mode. Returns skipped flag for other modes.
        """
        tn = fp = tp = fn = 0
        for r in per_dish_results:
            # Skip failed dishes — they don't represent routing decisions
            if not r.get("success", False):
                continue
            dish_id = r.get("dish_id", "")
            complexity = dish_complexity_map.get(dish_id, "unknown")
            turns = r.get("turns", 0)

            if complexity == "simple":
                if turns == 0:
                    tn += 1
                else:
                    fp += 1
            elif complexity == "complex":
                if turns > 0:
                    tp += 1
                else:
                    fn += 1

        tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        # Wilson score confidence intervals
        tnr_ci_lower, tnr_ci_upper = calculate_wilson_ci(tn, tn + fp)
        tpr_ci_lower, tpr_ci_upper = calculate_wilson_ci(tp, tp + fn)

        return {
            "tnr": tnr,
            "tpr": tpr,
            "tn": tn,
            "fp": fp,
            "tp": tp,
            "fn": fn,
            "tnr_ci_lower": tnr_ci_lower,
            "tnr_ci_upper": tnr_ci_upper,
            "tpr_ci_lower": tpr_ci_lower,
            "tpr_ci_upper": tpr_ci_upper,
        }

    def analyze_false_positives(
        self, per_dish_results: list[dict], dish_complexity_map: dict[str, str]
    ) -> dict[str, Any]:
        """Analyze false positive routing decisions to identify patterns.

        Args:
            per_dish_results: List of per-dish results.
            dish_complexity_map: Mapping of dish_id to complexity string.

        Returns:
            Dict containing false positive analysis.
        """
        fps = []
        for r in per_dish_results:
            if not r.get("success", False):
                continue
            dish_id = r.get("dish_id", "")
            complexity = dish_complexity_map.get(dish_id, "unknown")
            turns = r.get("turns", 0)

            if complexity == "simple" and turns > 0:
                breakdown = r.get("complexity_breakdown", {}) or {}
                conf = 0.0
                if r.get("final_data") and "items" in r["final_data"]:
                    items = r["final_data"]["items"]
                    if items:
                        conf = sum(i.get("confidence", 0) for i in items) / len(items)

                # We report what we know about the FP
                fps.append(
                    {
                        "dish_id": dish_id,
                        "complexity_score": r.get("complexity_score"),
                        "dominant_factor": breakdown.get("dominant_factor"),
                        "confidence": conf,
                        "turns": turns,
                    }
                )

        return {"false_positive_count": len(fps), "false_positives": fps}

    def calculate_turn_reduction(
        self, agentic_results: list[dict], naive_results: list[dict]
    ) -> dict[str, Any]:
        """Calculate turn reduction percentage between agentic and naive-always-ask modes.

        Formula: Y = (naive_total_turns - agentic_total_turns) / naive_total_turns * 100

        Args:
            agentic_results: Per-dish results from agentic mode.
            naive_results: Per-dish results from naive-always-ask mode.

        Returns:
            Dict with turn_reduction_pct, agentic_total_turns, naive_total_turns.
        """
        agentic_total = sum(r.get("turns", 0) for r in agentic_results)
        naive_total = sum(r.get("turns", 0) for r in naive_results)

        if naive_total == 0:
            return {"error": "naive baseline has 0 total turns -- cannot compute turn reduction"}

        reduction = (naive_total - agentic_total) / naive_total * 100
        return {
            "turn_reduction_pct": reduction,
            "agentic_total_turns": agentic_total,
            "naive_total_turns": naive_total,
        }

    def compare_modes(
        self, agentic_results: list[DishMAE], single_shot_results: list[DishMAE]
    ) -> dict[str, Any]:
        """Compute cross-mode comparison with effect sizes and confidence intervals.

        Args:
            agentic_results: Per-dish MAE from agentic mode.
            single_shot_results: Per-dish MAE from single-shot mode.

        Returns:
            Dict with per-macro Cohen's d, MAE differences with 95% CI, and summary.
        """

        def extract_values(results: list[DishMAE], attr: str) -> list[float]:
            return [getattr(r, attr) for r in results if r.success and getattr(r, attr) is not None]

        macros = ["calories", "protein", "fat", "carbs"]
        effect_sizes: dict[str, float | None] = {}
        mae_comparison: dict[str, dict] = {}

        for macro in macros:
            ag_vals = extract_values(agentic_results, macro)
            ss_vals = extract_values(single_shot_results, macro)

            d = calculate_cohens_d(ag_vals, ss_vals)
            effect_sizes[macro] = round(d, 4) if d is not None else None

            ag_mean = statistics.mean(ag_vals) if ag_vals else 0.0
            ss_mean = statistics.mean(ss_vals) if ss_vals else 0.0
            diff = ag_mean - ss_mean

            # Per-group CIs (not CI on the difference — use Cohen's d for significance)
            ag_ci = calculate_ci(ag_vals) if ag_vals else (0.0, 0.0)
            ss_ci = calculate_ci(ss_vals) if ss_vals else (0.0, 0.0)

            mae_comparison[macro] = {
                "agentic_mae": round(ag_mean, 2),
                "single_shot_mae": round(ss_mean, 2),
                "difference": round(diff, 2),
                "agentic_group_ci_95": (round(ag_ci[0], 2), round(ag_ci[1], 2)),
                "single_shot_group_ci_95": (round(ss_ci[0], 2), round(ss_ci[1], 2)),
            }

        # Plain-text summary
        cal_diff = mae_comparison["calories"]["difference"]
        cal_d = effect_sizes["calories"]
        direction = "worse" if cal_diff > 0 else "better"
        d_label = f"d={cal_d:.2f}" if cal_d is not None else "d=N/A"
        summary = (
            f"Agentic mode is {abs(cal_diff):.1f} kcal {direction} than single-shot "
            f"on calories MAE ({d_label}). "
            f"Agentic: {mae_comparison['calories']['agentic_mae']} kcal, "
            f"Single-shot: {mae_comparison['calories']['single_shot_mae']} kcal."
        )

        return {
            "effect_sizes_cohens_d": effect_sizes,
            "mae_comparison": mae_comparison,
            "summary": summary,
        }

    def aggregate_complexity(self, per_dish_results: list[dict]) -> "ComplexityMetrics":
        """
        Aggregate complexity metrics from per-dish benchmark results.

        Args:
            per_dish_results: List of per-dish result dicts, each potentially
                              containing 'complexity_breakdown' and 'complexity_score'.

        Returns:
            ComplexityMetrics with distribution of dominant factors and counts.
        """
        total_scored = 0
        score_sum = 0.0
        score_min = float("inf")
        score_max = float("-inf")
        clarification_triggered_count = 0
        total_questions_asked = 0
        dominant_factor_distribution: dict[str, int] = {}

        for result in per_dish_results:
            breakdown = result.get("complexity_breakdown")
            if breakdown is None or not isinstance(breakdown, dict):
                continue

            total_scored += 1
            score = breakdown.get("score", 0.0)
            score_sum += score
            score_min = min(score_min, score)
            score_max = max(score_max, score)

            factor = breakdown.get("dominant_factor") or "none"
            dominant_factor_distribution[factor] = dominant_factor_distribution.get(factor, 0) + 1

            # A clarification was triggered if there were turns > 0
            turns = result.get("turns", 0)
            if turns > 0:
                clarification_triggered_count += 1

            total_questions_asked += turns

        mean_score = score_sum / total_scored if total_scored > 0 else 0.0

        return ComplexityMetrics(
            total_scored=total_scored,
            mean_score=round(mean_score, 4),
            clarification_triggered_count=clarification_triggered_count,
            total_questions_asked=total_questions_asked,
            dominant_factor_distribution=dominant_factor_distribution,
            score_scale="deterministic_unbounded_0_to_21",
            score_min=round(score_min, 4) if total_scored > 0 else 0.0,
            score_max=round(score_max, 4) if total_scored > 0 else 0.0,
        )


@dataclass
class ComplexityMetrics:
    """Aggregate complexity metrics across benchmark dishes."""

    total_scored: int = 0
    mean_score: float = 0.0
    clarification_triggered_count: int = 0
    total_questions_asked: int = 0
    dominant_factor_distribution: dict[str, int] | None = None
    score_scale: str = "deterministic_unbounded_0_to_21"
    score_min: float = 0.0
    score_max: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_scored": self.total_scored,
            "mean_score": round(self.mean_score, 4),
            "clarification_triggered_count": self.clarification_triggered_count,
            "total_questions_asked": self.total_questions_asked,
            "dominant_factor_distribution": self.dominant_factor_distribution or {},
            "score_scale": self.score_scale,
            "score_min": round(self.score_min, 4),
            "score_max": round(self.score_max, 4),
        }


class LatencyTracker:
    """
    Tracks computational latency for each dish processing.
    """

    def __init__(self):
        self._latencies: list[DishLatency] = []

    @contextmanager
    def track(self, dish_id: str, complexity: str = "unknown"):
        """
        Context manager to track latency for a dish.

        Usage:
            with tracker.track("dish_123", "simple"):
                await runner.run_dish(dish)
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            latency = end_time - start_time
            self._latencies.append(
                DishLatency(dish_id=dish_id, latency_seconds=latency, complexity=complexity)
            )

    def record(self, dish_id: str, latency_seconds: float, complexity: str = "unknown"):
        """Manually record a latency measurement."""
        self._latencies.append(
            DishLatency(dish_id=dish_id, latency_seconds=latency_seconds, complexity=complexity)
        )

    def get_latencies(self) -> list[DishLatency]:
        """Get all recorded latencies."""
        return self._latencies.copy()

    def aggregate(self) -> AggregateLatency:
        """Calculate aggregate latency statistics."""
        if not self._latencies:
            return AggregateLatency()

        all_latencies = [lat.latency_seconds for lat in self._latencies]
        simple_latencies = [lat.latency_seconds for lat in self._latencies if lat.complexity == "simple"]
        complex_latencies = [lat.latency_seconds for lat in self._latencies if lat.complexity == "complex"]

        # Sort for percentile calculation
        sorted_latencies = sorted(all_latencies)
        n = len(sorted_latencies)

        def percentile(data: list[float], pct: float) -> float:
            if not data:
                return 0.0
            k = (len(data) - 1) * pct
            f = int(k)
            c = f + 1 if f + 1 < len(data) else f
            return data[f] + (data[c] - data[f]) * (k - f) if c != f else data[f]

        return AggregateLatency(
            mean_seconds=statistics.mean(all_latencies),
            p50_seconds=percentile(sorted_latencies, 0.50),
            p95_seconds=percentile(sorted_latencies, 0.95),
            p99_seconds=percentile(sorted_latencies, 0.99),
            simple_mean=statistics.mean(simple_latencies) if simple_latencies else 0.0,
            complex_mean=statistics.mean(complex_latencies) if complex_latencies else 0.0,
            sample_count=n,
        )

    def reset(self):
        """Clear all recorded latencies."""
        self._latencies.clear()
