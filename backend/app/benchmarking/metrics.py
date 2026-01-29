"""
Metrics Module for Oracle Benchmarking.

Calculates Mean Absolute Error (MAE) against WFR ground truth
and tracks computational latency per dish.
"""

import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from app.benchmarking.schemas import NutritionDish


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

    # Count of valid samples
    sample_count: int = 0

    def to_dict(self) -> dict:
        return {
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

    def aggregate_mae(self, results: list[DishMAE]) -> AggregateMAE:
        """
        Aggregate MAE metrics across all successfully processed dishes.
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

        if protein_errors:
            agg.mean_protein = statistics.mean(protein_errors)
            agg.std_protein = statistics.stdev(protein_errors) if len(protein_errors) > 1 else 0.0

        if fat_errors:
            agg.mean_fat = statistics.mean(fat_errors)
            agg.std_fat = statistics.stdev(fat_errors) if len(fat_errors) > 1 else 0.0

        if carbs_errors:
            agg.mean_carbs = statistics.mean(carbs_errors)
            agg.std_carbs = statistics.stdev(carbs_errors) if len(carbs_errors) > 1 else 0.0

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
