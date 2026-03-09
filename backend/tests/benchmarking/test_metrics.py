"""
Unit tests for Metrics module (MAE Calculator and Latency Tracker).
"""

import pytest

from app.benchmarking.metrics import (
    AggregateLatency,
    AggregateMAE,
    ComplexityMetrics,
    DishLatency,
    DishMAE,
    LatencyTracker,
    MetricsCalculator,
    calculate_ci,
    calculate_cohens_d,
    calculate_wilson_ci,
)
from app.benchmarking.schemas import IngredientInfo, NutritionDish


@pytest.fixture
def metrics_calculator():
    return MetricsCalculator()


@pytest.fixture
def sample_ground_truth():
    """Ground truth dish with known values."""
    return NutritionDish(
        dish_id="gt_001",
        total_calories=500,
        total_mass=350,
        total_fat=20,
        total_carb=50,
        total_protein=30,
        ingredients=[
            IngredientInfo(id="1", name="chicken", grams=150),
            IngredientInfo(id="2", name="rice", grams=200),
        ],
        complexity="simple",
    )


@pytest.fixture
def perfect_prediction():
    """Prediction that exactly matches ground truth."""
    return {
        "title": "Chicken Rice",
        "items": [
            {"name": "chicken", "calories": 250, "protein": 30, "fats": 10, "carbs": 0},
            {"name": "rice", "calories": 250, "protein": 0, "fats": 10, "carbs": 50},
        ],
    }


@pytest.fixture
def imperfect_prediction():
    """Prediction with some error."""
    return {
        "title": "Chicken Rice",
        "items": [
            {"name": "chicken", "calories": 200, "protein": 25, "fats": 8, "carbs": 5},
            {"name": "rice", "calories": 200, "protein": 0, "fats": 8, "carbs": 40},
        ],
    }


class TestDishMAE:
    """Tests for DishMAE calculation."""

    def test_calculate_perfect_match(self, metrics_calculator, sample_ground_truth, perfect_prediction):
        """Perfect prediction should have zero MAE."""
        result = metrics_calculator.calculate_dish_mae(perfect_prediction, sample_ground_truth)

        assert result.dish_id == "gt_001"
        assert result.success is True
        assert result.calories == 0
        assert result.protein == 0
        assert result.fat == 0
        assert result.carbs == 0

    def test_calculate_with_errors(self, metrics_calculator, sample_ground_truth, imperfect_prediction):
        """Imperfect prediction should have positive MAE."""
        result = metrics_calculator.calculate_dish_mae(imperfect_prediction, sample_ground_truth)

        assert result.dish_id == "gt_001"
        assert result.success is True
        # Predicted: 400 cal, 25 prot, 16 fat, 45 carbs
        # GT: 500 cal, 30 prot, 20 fat, 50 carbs
        assert result.calories == 100  # |400 - 500|
        assert result.protein == 5  # |25 - 30|
        assert result.fat == 4  # |16 - 20|
        assert result.carbs == 5  # |45 - 50|

    def test_calculate_none_prediction(self, metrics_calculator, sample_ground_truth):
        """None prediction should return failed result."""
        result = metrics_calculator.calculate_dish_mae(None, sample_ground_truth)

        assert result.dish_id == "gt_001"
        assert result.success is False
        assert result.calories is None

    def test_calculate_empty_items(self, metrics_calculator, sample_ground_truth):
        """Empty items list should result in full ground truth as error."""
        prediction = {"title": "Empty", "items": []}
        result = metrics_calculator.calculate_dish_mae(prediction, sample_ground_truth)

        assert result.calories == 500  # |0 - 500|
        assert result.protein == 30
        assert result.fat == 20
        assert result.carbs == 50

    def test_to_dict(self):
        """DishMAE should serialize to dict."""
        mae = DishMAE(
            dish_id="test",
            calories=10.5,
            protein=2.3,
            fat=1.2,
            carbs=3.4,
            success=True,
        )
        d = mae.to_dict()
        assert d["dish_id"] == "test"
        assert d["calories"] == 10.5
        assert d["success"] is True


class TestAggregateMAE:
    """Tests for aggregate MAE calculation."""

    def test_aggregate_single_result(self, metrics_calculator):
        """Single result should aggregate to itself."""
        results = [DishMAE(dish_id="1", calories=10, protein=2, fat=1, carbs=3, success=True)]
        agg = metrics_calculator.aggregate_mae(results)

        assert agg.mean_calories == 10
        assert agg.mean_protein == 2
        assert agg.mean_fat == 1
        assert agg.mean_carbs == 3
        assert agg.sample_count == 1

    def test_aggregate_multiple_results(self, metrics_calculator):
        """Multiple results should average."""
        results = [
            DishMAE(dish_id="1", calories=10, protein=2, fat=1, carbs=3, success=True),
            DishMAE(dish_id="2", calories=20, protein=4, fat=3, carbs=5, success=True),
        ]
        agg = metrics_calculator.aggregate_mae(results)

        assert agg.mean_calories == 15  # (10 + 20) / 2
        assert agg.mean_protein == 3  # (2 + 4) / 2
        assert agg.mean_fat == 2  # (1 + 3) / 2
        assert agg.mean_carbs == 4  # (3 + 5) / 2
        assert agg.sample_count == 2

    def test_aggregate_excludes_failures(self, metrics_calculator):
        """Failed results should be excluded from aggregation."""
        results = [
            DishMAE(dish_id="1", calories=10, protein=2, fat=1, carbs=3, success=True),
            DishMAE(dish_id="2", success=False),  # Failed
        ]
        agg = metrics_calculator.aggregate_mae(results)

        assert agg.mean_calories == 10
        assert agg.sample_count == 1

    def test_aggregate_empty_results(self, metrics_calculator):
        """Empty results should return zero aggregate."""
        agg = metrics_calculator.aggregate_mae([])

        assert agg.mean_calories == 0
        assert agg.sample_count == 0

    def test_aggregate_calculates_std_dev(self, metrics_calculator):
        """Should calculate standard deviation for multiple results."""
        results = [
            DishMAE(dish_id="1", calories=10, protein=2, fat=1, carbs=3, success=True),
            DishMAE(dish_id="2", calories=20, protein=4, fat=3, carbs=5, success=True),
            DishMAE(dish_id="3", calories=15, protein=3, fat=2, carbs=4, success=True),
        ]
        agg = metrics_calculator.aggregate_mae(results)

        assert agg.std_calories > 0
        assert agg.sample_count == 3

    def test_to_dict(self):
        """AggregateMAE should serialize to dict."""
        agg = AggregateMAE(
            mean_calories=45.2,
            mean_protein=3.1,
            mean_fat=2.8,
            mean_carbs=5.4,
            sample_count=100,
        )
        d = agg.to_dict()
        assert "mae" in d
        assert d["mae"]["calories"] == 45.2
        assert d["sample_count"] == 100


class TestWithinThreshold:
    """Tests for within threshold calculation."""

    def test_perfect_within_threshold(self, metrics_calculator, sample_ground_truth):
        """Perfect predictions should be within threshold."""
        results = [
            DishMAE(
                dish_id="gt_001",
                calories=0,
                protein=0,
                fat=0,
                carbs=0,
                success=True,
            )
        ]
        gt_map = {"gt_001": sample_ground_truth}
        within = metrics_calculator.calculate_within_threshold(results, gt_map, 0.10)

        assert within["calories"] == 1.0
        assert within["protein"] == 1.0

    def test_large_error_outside_threshold(self, metrics_calculator, sample_ground_truth):
        """Large errors should be outside threshold."""
        results = [
            DishMAE(
                dish_id="gt_001",
                calories=200,  # 40% error on 500 cal
                protein=10,  # 33% error on 30g
                fat=5,  # 25% error on 20g
                carbs=20,  # 40% error on 50g
                success=True,
            )
        ]
        gt_map = {"gt_001": sample_ground_truth}
        within = metrics_calculator.calculate_within_threshold(results, gt_map, 0.10)

        assert within["calories"] == 0.0
        assert within["protein"] == 0.0


class TestLatencyTracker:
    """Tests for latency tracking."""

    def test_record_single_latency(self):
        """Should record single latency."""
        tracker = LatencyTracker()
        tracker.record("dish_001", 3.5, "simple")

        latencies = tracker.get_latencies()
        assert len(latencies) == 1
        assert latencies[0].dish_id == "dish_001"
        assert latencies[0].latency_seconds == 3.5
        assert latencies[0].complexity == "simple"

    def test_record_multiple_latencies(self):
        """Should record multiple latencies."""
        tracker = LatencyTracker()
        tracker.record("dish_001", 3.0, "simple")
        tracker.record("dish_002", 5.0, "complex")
        tracker.record("dish_003", 4.0, "simple")

        latencies = tracker.get_latencies()
        assert len(latencies) == 3

    def test_aggregate_mean(self):
        """Should calculate correct mean latency."""
        tracker = LatencyTracker()
        tracker.record("1", 2.0, "simple")
        tracker.record("2", 4.0, "simple")
        tracker.record("3", 6.0, "simple")

        agg = tracker.aggregate()
        assert agg.mean_seconds == 4.0  # (2 + 4 + 6) / 3

    def test_aggregate_percentiles(self):
        """Should calculate percentiles."""
        tracker = LatencyTracker()
        # 10 values: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
        for i in range(1, 11):
            tracker.record(str(i), float(i), "simple")

        agg = tracker.aggregate()
        assert agg.p50_seconds == 5.5  # Median of 1-10
        assert agg.p95_seconds >= 9.0
        assert agg.p99_seconds >= 9.5

    def test_aggregate_per_complexity(self):
        """Should calculate mean per complexity class."""
        tracker = LatencyTracker()
        tracker.record("1", 2.0, "simple")
        tracker.record("2", 3.0, "simple")
        tracker.record("3", 6.0, "complex")
        tracker.record("4", 8.0, "complex")

        agg = tracker.aggregate()
        assert agg.simple_mean == 2.5  # (2 + 3) / 2
        assert agg.complex_mean == 7.0  # (6 + 8) / 2

    def test_aggregate_empty(self):
        """Empty tracker should return zero aggregate."""
        tracker = LatencyTracker()
        agg = tracker.aggregate()

        assert agg.mean_seconds == 0.0
        assert agg.sample_count == 0

    def test_reset(self):
        """Reset should clear all latencies."""
        tracker = LatencyTracker()
        tracker.record("1", 3.0, "simple")
        tracker.record("2", 4.0, "complex")

        tracker.reset()
        assert len(tracker.get_latencies()) == 0

    def test_context_manager(self):
        """Context manager should track latency."""
        tracker = LatencyTracker()

        with tracker.track("dish_001", "simple"):
            # Simulate work
            import time

            time.sleep(0.1)

        latencies = tracker.get_latencies()
        assert len(latencies) == 1
        assert latencies[0].latency_seconds >= 0.1

    def test_to_dict(self):
        """AggregateLatency should serialize to dict."""
        agg = AggregateLatency(
            mean_seconds=4.2,
            p50_seconds=3.8,
            p95_seconds=8.5,
            p99_seconds=12.1,
            simple_mean=3.5,
            complex_mean=4.9,
            sample_count=100,
        )
        d = agg.to_dict()
        assert d["mean_seconds"] == 4.2
        assert d["p50_seconds"] == 3.8
        assert d["per_complexity"]["simple_mean"] == 3.5


class TestDishLatency:
    """Tests for DishLatency dataclass."""

    def test_creation(self):
        """Should create DishLatency."""
        dl = DishLatency(dish_id="test", latency_seconds=3.5, complexity="simple")
        assert dl.dish_id == "test"
        assert dl.latency_seconds == 3.5
        assert dl.complexity == "simple"

    def test_default_complexity(self):
        """Default complexity should be 'unknown'."""
        dl = DishLatency(dish_id="test", latency_seconds=3.5)
        assert dl.complexity == "unknown"


class TestAggregateMAEByStratum:
    """Tests for per-stratum MAE aggregation."""

    def test_splits_by_complexity(self, metrics_calculator):
        results = [
            DishMAE(dish_id="s1", calories=10, protein=2, fat=1, carbs=3, success=True),
            DishMAE(dish_id="s2", calories=20, protein=4, fat=3, carbs=5, success=True),
            DishMAE(dish_id="c1", calories=50, protein=8, fat=6, carbs=10, success=True),
        ]
        complexity_map = {"s1": "simple", "s2": "simple", "c1": "complex"}

        stratum_mae = metrics_calculator.aggregate_mae_by_stratum(results, complexity_map)

        assert "simple" in stratum_mae
        assert "complex" in stratum_mae
        assert stratum_mae["simple"].mean_calories == 15  # (10+20)/2
        assert stratum_mae["simple"].sample_count == 2
        assert stratum_mae["complex"].mean_calories == 50
        assert stratum_mae["complex"].sample_count == 1

    def test_all_same_stratum(self, metrics_calculator):
        results = [
            DishMAE(dish_id="s1", calories=10, protein=2, fat=1, carbs=3, success=True),
            DishMAE(dish_id="s2", calories=20, protein=4, fat=3, carbs=5, success=True),
        ]
        complexity_map = {"s1": "simple", "s2": "simple"}

        stratum_mae = metrics_calculator.aggregate_mae_by_stratum(results, complexity_map)

        assert "simple" in stratum_mae
        assert "complex" not in stratum_mae

    def test_empty_results(self, metrics_calculator):
        stratum_mae = metrics_calculator.aggregate_mae_by_stratum([], {})
        assert stratum_mae == {}


class TestRoutingAccuracy:
    """Tests for TNR/TPR calculation."""

    def test_known_counts(self, metrics_calculator):
        per_dish = [
            {"dish_id": "s1", "turns": 0, "success": True},  # TN
            {"dish_id": "s2", "turns": 1, "success": True},  # FP
            {"dish_id": "c1", "turns": 2, "success": True},  # TP
            {"dish_id": "c2", "turns": 0, "success": True},  # FN
        ]
        complexity_map = {"s1": "simple", "s2": "simple", "c1": "complex", "c2": "complex"}

        result = metrics_calculator.calculate_routing_accuracy(per_dish, complexity_map)

        assert result["tn"] == 1
        assert result["fp"] == 1
        assert result["tp"] == 1
        assert result["fn"] == 1
        assert result["tnr"] == 0.5  # 1/(1+1)
        assert result["tpr"] == 0.5  # 1/(1+1)

    def test_perfect_routing(self, metrics_calculator):
        per_dish = [
            {"dish_id": "s1", "turns": 0, "success": True},  # TN
            {"dish_id": "s2", "turns": 0, "success": True},  # TN
            {"dish_id": "c1", "turns": 1, "success": True},  # TP
            {"dish_id": "c2", "turns": 2, "success": True},  # TP
        ]
        complexity_map = {"s1": "simple", "s2": "simple", "c1": "complex", "c2": "complex"}

        result = metrics_calculator.calculate_routing_accuracy(per_dish, complexity_map)

        assert result["tnr"] == 1.0
        assert result["tpr"] == 1.0

    def test_excludes_failed_dishes(self, metrics_calculator):
        """Failed dishes should not count as routing decisions."""
        per_dish = [
            {"dish_id": "s1", "turns": 0, "success": True},  # TN
            {"dish_id": "s2", "turns": 0, "success": False},  # Failed — excluded
            {"dish_id": "c1", "turns": 0, "success": False},  # Failed — excluded
            {"dish_id": "c2", "turns": 1, "success": True},  # TP
        ]
        complexity_map = {"s1": "simple", "s2": "simple", "c1": "complex", "c2": "complex"}

        result = metrics_calculator.calculate_routing_accuracy(per_dish, complexity_map)

        assert result["tn"] == 1  # Only s1
        assert result["fp"] == 0
        assert result["tp"] == 1  # Only c2
        assert result["fn"] == 0

    def test_empty_results(self, metrics_calculator):
        result = metrics_calculator.calculate_routing_accuracy([], {})
        assert result["tnr"] == 0.0
        assert result["tpr"] == 0.0


class TestTurnReduction:
    """Tests for turn reduction calculation."""

    def test_basic_reduction(self, metrics_calculator):
        agentic = [{"turns": 1}, {"turns": 0}, {"turns": 2}]  # total=3
        naive = [{"turns": 3}, {"turns": 2}, {"turns": 3}]  # total=8

        result = metrics_calculator.calculate_turn_reduction(agentic, naive)

        assert "turn_reduction_pct" in result
        assert result["agentic_total_turns"] == 3
        assert result["naive_total_turns"] == 8
        assert result["turn_reduction_pct"] == pytest.approx(62.5)  # (8-3)/8*100

    def test_zero_naive_turns(self, metrics_calculator):
        agentic = [{"turns": 0}]
        naive = [{"turns": 0}]

        result = metrics_calculator.calculate_turn_reduction(agentic, naive)

        assert "error" in result

    def test_no_reduction(self, metrics_calculator):
        agentic = [{"turns": 5}]
        naive = [{"turns": 5}]

        result = metrics_calculator.calculate_turn_reduction(agentic, naive)

        assert result["turn_reduction_pct"] == 0.0


class TestCalculateCI:
    """Tests for confidence interval calculation."""

    def test_basic_ci(self):
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        lower, upper = calculate_ci(values)
        mean = 30.0
        assert lower < mean
        assert upper > mean
        # Symmetric around the mean
        assert abs((upper - mean) - (mean - lower)) < 0.01

    def test_single_value(self):
        lower, upper = calculate_ci([42.0])
        assert lower == 42.0
        assert upper == 42.0

    def test_empty_list(self):
        lower, upper = calculate_ci([])
        assert lower == 0.0
        assert upper == 0.0

    def test_identical_values(self):
        lower, upper = calculate_ci([5.0, 5.0, 5.0])
        assert lower == 5.0
        assert upper == 5.0

    def test_large_sample_narrow_ci(self):
        """Larger samples should produce narrower CI."""
        small = [10.0, 20.0, 30.0]
        large = [10.0, 15.0, 20.0, 25.0, 30.0, 12.0, 18.0, 22.0, 28.0, 14.0]
        _, small_upper = calculate_ci(small)
        small_lower, _ = calculate_ci(small)
        _, large_upper = calculate_ci(large)
        large_lower, _ = calculate_ci(large)
        small_width = small_upper - small_lower
        large_width = large_upper - large_lower
        assert large_width < small_width


class TestCalculateCohensD:
    """Tests for Cohen's d effect size calculation."""

    def test_identical_groups(self):
        g1 = [10.0, 20.0, 30.0]
        d = calculate_cohens_d(g1, g1.copy())
        assert d == 0.0

    def test_large_effect(self):
        g1 = [10.0, 12.0, 11.0, 13.0, 10.5]
        g2 = [50.0, 52.0, 51.0, 53.0, 50.5]
        d = calculate_cohens_d(g1, g2)
        assert d is not None
        assert abs(d) > 2.0  # Very large effect

    def test_too_small_groups(self):
        d = calculate_cohens_d([10.0], [20.0])
        assert d is None

    def test_equal_means_returns_zero(self):
        """Equal means returns 0.0 regardless of variance."""
        d = calculate_cohens_d([5.0, 5.0], [5.0, 5.0])
        assert d == 0.0

    def test_zero_pooled_variance_different_means(self):
        """Zero pooled variance with different means returns None."""
        d = calculate_cohens_d([5.0, 5.0], [10.0, 10.0])
        assert d is None  # Zero pooled variance

    def test_sign_direction(self):
        g1 = [10.0, 12.0, 11.0]
        g2 = [20.0, 22.0, 21.0]
        d = calculate_cohens_d(g1, g2)
        assert d is not None
        assert d < 0  # g1 < g2


class TestCalculateWilsonCI:
    """Tests for Wilson score confidence interval."""

    def test_perfect_proportion(self):
        lower, upper = calculate_wilson_ci(10, 10)
        assert lower > 0.5
        assert upper == 1.0

    def test_zero_proportion(self):
        lower, upper = calculate_wilson_ci(0, 10)
        assert lower == 0.0
        assert upper < 0.5

    def test_half_proportion(self):
        lower, upper = calculate_wilson_ci(50, 100)
        assert lower < 0.5
        assert upper > 0.5

    def test_empty_total(self):
        lower, upper = calculate_wilson_ci(0, 0)
        assert lower == 0.0
        assert upper == 0.0

    def test_small_sample(self):
        """Wilson should handle small samples better than normal approximation."""
        lower, upper = calculate_wilson_ci(1, 3)
        assert 0.0 <= lower < 0.5
        assert 0.3 < upper <= 1.0


class TestAggregateMAEWithCI:
    """Tests for CI integration in aggregate_mae."""

    def test_ci_populated_for_multiple_results(self):
        calc = MetricsCalculator()
        results = [
            DishMAE(dish_id="1", calories=10, protein=2, fat=1, carbs=3, success=True),
            DishMAE(dish_id="2", calories=20, protein=4, fat=3, carbs=5, success=True),
            DishMAE(dish_id="3", calories=30, protein=6, fat=5, carbs=7, success=True),
        ]
        agg = calc.aggregate_mae(results)

        assert agg.ci_lower_calories is not None
        assert agg.ci_upper_calories is not None
        assert agg.ci_lower_calories < agg.mean_calories
        assert agg.ci_upper_calories > agg.mean_calories

    def test_ci_single_result(self):
        calc = MetricsCalculator()
        results = [DishMAE(dish_id="1", calories=10, protein=2, fat=1, carbs=3, success=True)]
        agg = calc.aggregate_mae(results)

        # Single result: CI collapses to the mean
        assert agg.ci_lower_calories == agg.mean_calories
        assert agg.ci_upper_calories == agg.mean_calories

    def test_ci_in_to_dict(self):
        calc = MetricsCalculator()
        results = [
            DishMAE(dish_id="1", calories=10, protein=2, fat=1, carbs=3, success=True),
            DishMAE(dish_id="2", calories=20, protein=4, fat=3, carbs=5, success=True),
        ]
        agg = calc.aggregate_mae(results)
        d = agg.to_dict()

        assert "confidence_interval_95" in d
        assert "calories" in d["confidence_interval_95"]


class TestRoutingAccuracyWilsonCI:
    """Tests for Wilson CI in routing accuracy."""

    def test_wilson_ci_present(self):
        calc = MetricsCalculator()
        per_dish = [
            {"dish_id": "s1", "turns": 0, "success": True},
            {"dish_id": "s2", "turns": 1, "success": True},
            {"dish_id": "c1", "turns": 1, "success": True},
            {"dish_id": "c2", "turns": 0, "success": True},
        ]
        complexity_map = {"s1": "simple", "s2": "simple", "c1": "complex", "c2": "complex"}

        result = calc.calculate_routing_accuracy(per_dish, complexity_map)

        assert "tnr_ci_lower" in result
        assert "tnr_ci_upper" in result
        assert "tpr_ci_lower" in result
        assert "tpr_ci_upper" in result
        assert result["tnr_ci_lower"] <= result["tnr"]
        assert result["tnr_ci_upper"] >= result["tnr"]


class TestCompareModes:
    """Tests for cross-mode comparison."""

    def test_basic_comparison(self):
        calc = MetricsCalculator()
        agentic = [
            DishMAE(dish_id="1", calories=80, protein=5, fat=3, carbs=8, success=True),
            DishMAE(dish_id="2", calories=90, protein=6, fat=4, carbs=9, success=True),
            DishMAE(dish_id="3", calories=70, protein=4, fat=2, carbs=7, success=True),
        ]
        single_shot = [
            DishMAE(dish_id="1", calories=60, protein=4, fat=2, carbs=6, success=True),
            DishMAE(dish_id="2", calories=50, protein=3, fat=2, carbs=5, success=True),
            DishMAE(dish_id="3", calories=55, protein=3, fat=2, carbs=6, success=True),
        ]

        result = calc.compare_modes(agentic, single_shot)

        assert "effect_sizes_cohens_d" in result
        assert "mae_comparison" in result
        assert "summary" in result
        assert "calories" in result["effect_sizes_cohens_d"]
        assert result["mae_comparison"]["calories"]["agentic_mae"] > 0
        assert result["mae_comparison"]["calories"]["single_shot_mae"] > 0

    def test_identical_results(self):
        calc = MetricsCalculator()
        results = [
            DishMAE(dish_id="1", calories=50, protein=5, fat=3, carbs=8, success=True),
            DishMAE(dish_id="2", calories=60, protein=6, fat=4, carbs=9, success=True),
        ]

        result = calc.compare_modes(results, results)

        assert result["effect_sizes_cohens_d"]["calories"] == 0.0
        assert result["mae_comparison"]["calories"]["difference"] == 0.0

    def test_all_failed_results(self):
        """All-failed results should not raise and should return zeroed comparison."""
        calc = MetricsCalculator()
        failed = [
            DishMAE(dish_id="1", success=False),
            DishMAE(dish_id="2", success=False),
        ]

        result = calc.compare_modes(failed, failed)

        assert result["effect_sizes_cohens_d"]["calories"] is None
        assert result["mae_comparison"]["calories"]["agentic_mae"] == 0.0
        assert result["mae_comparison"]["calories"]["difference"] == 0.0


class TestComplexityMetricsScale:
    """Tests for ComplexityMetrics scale fields."""

    def test_scale_fields_in_to_dict(self):
        cm = ComplexityMetrics(
            total_scored=5,
            mean_score=3.6,
            score_scale="deterministic_unbounded_0_to_21",
            score_min=1.2,
            score_max=8.4,
        )
        d = cm.to_dict()

        assert d["score_scale"] == "deterministic_unbounded_0_to_21"
        assert d["score_min"] == 1.2
        assert d["score_max"] == 8.4

    def test_aggregate_complexity_populates_scale(self):
        calc = MetricsCalculator()
        per_dish = [
            {"complexity_breakdown": {"score": 2.0, "dominant_factor": "hidden_ingredients"}, "turns": 0},
            {"complexity_breakdown": {"score": 5.5, "dominant_factor": "invisible_prep"}, "turns": 1},
            {"complexity_breakdown": {"score": 3.2, "dominant_factor": "hidden_ingredients"}, "turns": 0},
        ]

        result = calc.aggregate_complexity(per_dish)

        assert result.score_scale == "deterministic_unbounded_0_to_21"
        assert result.score_min == 2.0
        assert result.score_max == 5.5
        assert result.total_scored == 3
