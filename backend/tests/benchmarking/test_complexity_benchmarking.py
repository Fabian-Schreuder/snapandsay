"""
Tests for Story 7.7: Complexity benchmarking metrics, SSE extraction, and reporting.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.benchmarking.experiment_log import ExperimentLog, ExperimentResult
from app.benchmarking.metrics import ComplexityMetrics, MetricsCalculator

# ── Fixtures ──────────────────────────────────────────────────────

SAMPLE_BREAKDOWN = {
    "levels": {"hidden_ingredients": 2, "invisible_prep": 1, "portion_ambiguity": 3},
    "weights": {"ingredients": 0.8, "prep": 0.6, "volume": 0.3},
    "semantic_penalty": 3.0,
    "dominant_factor": "volume",
    "score": 0.75,
}

SAMPLE_BREAKDOWN_INGREDIENTS = {
    "levels": {"hidden_ingredients": 3, "invisible_prep": 0, "portion_ambiguity": 1},
    "weights": {"ingredients": 0.8, "prep": 0.6, "volume": 0.3},
    "semantic_penalty": 0.0,
    "dominant_factor": "ingredients",
    "score": 0.55,
}


@pytest.fixture
def metrics_calculator():
    return MetricsCalculator()


@pytest.fixture
def per_dish_results_with_complexity():
    """Per-dish results with varied complexity breakdowns."""
    return [
        {
            "dish_id": "d1",
            "success": True,
            "turns": 1,
            "complexity_breakdown": SAMPLE_BREAKDOWN,
            "complexity_score": 0.7,
        },
        {
            "dish_id": "d2",
            "success": True,
            "turns": 0,
            "complexity_breakdown": SAMPLE_BREAKDOWN_INGREDIENTS,
            "complexity_score": 0.5,
        },
        {
            "dish_id": "d3",
            "success": True,
            "turns": 2,
            "complexity_breakdown": {
                **SAMPLE_BREAKDOWN,
                "dominant_factor": "prep",
                "score": 0.9,
            },
            "complexity_score": 0.8,
        },
    ]


@pytest.fixture
def per_dish_results_no_complexity():
    """Per-dish results without complexity data (backward compat)."""
    return [
        {
            "dish_id": "d1",
            "success": True,
            "turns": 0,
            "complexity_breakdown": None,
            "complexity_score": None,
        },
        {
            "dish_id": "d2",
            "success": False,
            "turns": 0,
            "complexity_breakdown": None,
            "complexity_score": None,
        },
    ]


# ── Test 5.1: aggregate_complexity ───────────────────────────────


class TestAggregateComplexity:
    """Tests for MetricsCalculator.aggregate_complexity()."""

    def test_basic_aggregation(self, metrics_calculator, per_dish_results_with_complexity):
        """Should correctly aggregate complexity metrics across dishes."""
        stats = metrics_calculator.aggregate_complexity(per_dish_results_with_complexity)

        assert isinstance(stats, ComplexityMetrics)
        assert stats.total_scored == 3
        # (0.75 + 0.55 + 0.9) / 3 = 0.7333
        assert abs(stats.mean_score - 0.7333) < 0.01
        # d1 has turns=1, d3 has turns=2 → 2 clarifications triggered
        assert stats.clarification_triggered_count == 2
        # d1(1) + d2(0) + d3(2) = 3 total questions
        assert stats.total_questions_asked == 3
        assert stats.dominant_factor_distribution == {
            "volume": 1,
            "ingredients": 1,
            "prep": 1,
        }

    def test_empty_results(self, metrics_calculator):
        """Empty results should return zeroed metrics."""
        stats = metrics_calculator.aggregate_complexity([])
        assert stats.total_scored == 0
        assert stats.mean_score == 0.0
        assert stats.clarification_triggered_count == 0
        assert stats.total_questions_asked == 0

    def test_none_breakdowns_skipped(self, metrics_calculator, per_dish_results_no_complexity):
        """Dishes without complexity_breakdown should be skipped."""
        stats = metrics_calculator.aggregate_complexity(per_dish_results_no_complexity)
        assert stats.total_scored == 0
        assert stats.clarification_triggered_count == 0

    def test_mixed_results(self, metrics_calculator):
        """Mix of dishes with and without complexity data."""
        results = [
            {"dish_id": "d1", "turns": 1, "complexity_breakdown": SAMPLE_BREAKDOWN},
            {"dish_id": "d2", "turns": 0, "complexity_breakdown": None},
        ]
        stats = metrics_calculator.aggregate_complexity(results)
        assert stats.total_scored == 1
        assert stats.mean_score == 0.75
        assert stats.clarification_triggered_count == 1

    def test_to_dict(self, metrics_calculator, per_dish_results_with_complexity):
        """ComplexityMetrics.to_dict() should serialize correctly."""
        stats = metrics_calculator.aggregate_complexity(per_dish_results_with_complexity)
        d = stats.to_dict()

        assert d["total_scored"] == 3
        assert "mean_score" in d
        assert "clarification_triggered_count" in d
        assert "total_questions_asked" in d
        assert d["total_questions_asked"] == 3
        assert "dominant_factor_distribution" in d
        assert isinstance(d["dominant_factor_distribution"], dict)

    def test_none_dominant_factor_maps_to_none_key(self, metrics_calculator):
        """dominant_factor=None should be counted as 'none'."""
        results = [
            {
                "dish_id": "d1",
                "turns": 0,
                "complexity_breakdown": {
                    "score": 0.1,
                    "dominant_factor": None,
                },
            }
        ]
        stats = metrics_calculator.aggregate_complexity(results)
        assert stats.dominant_factor_distribution == {"none": 1}


# ── Test 5.2: SSE payload complexity_breakdown extraction ────────


class TestSSEComplexityExtraction:
    """Tests that OracleRunner extracts complexity from SSE payload."""

    @pytest.mark.asyncio
    async def test_complexity_extracted_from_response(self):
        """agent.response SSE event should populate complexity_breakdown and complexity_score."""
        from app.benchmarking.schemas import IngredientInfo, NutritionDish

        dish = NutritionDish(
            dish_id="dish_cx",
            total_calories=500.0,
            total_mass=200.0,
            total_fat=20.0,
            total_carb=30.0,
            total_protein=40.0,
            ingredients=[IngredientInfo(id="1", name="Chicken", grams=100.0)],
            complexity="simple",
        )

        response_payload = {
            "type": "agent.response",
            "payload": {
                "status": "success",
                "nutritional_data": {"title": "Chicken", "items": []},
                "complexity_breakdown": SAMPLE_BREAKDOWN,
                "complexity_score": 0.7,
            },
        }

        lines = [
            b"event: agent.response",
            f"data: {json.dumps(response_payload)}".encode(),
            b"",
        ]

        class MockStream:
            status_code = 200

            async def aiter_lines(self):
                for line in lines:
                    yield line.decode("utf-8")

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        with (
            patch("app.benchmarking.oracle_runner.settings") as mock_settings,
            patch("app.benchmarking.oracle_runner.create_client"),
        ):
            mock_settings.SUPABASE_URL = "http://supabase.test"
            mock_settings.SUPABASE_ANON_KEY = "anon-key"

            from app.benchmarking.oracle_runner import OracleRunner

            runner = OracleRunner(
                api_url="http://test.local",
                email="test@test.com",
                password="pass",  # noqa: S106
            )
            runner.supabase = MagicMock()
            runner.access_token = "fake-token"

            mock_upload = MagicMock()
            mock_upload.status_code = 200
            mock_upload.json.return_value = {"log_id": "log_cx"}

            with (
                patch.object(runner.client, "post", return_value=mock_upload),
                patch.object(runner.client, "stream", return_value=MockStream()),
            ):
                result = await runner.run_dish(dish)

        assert result["success"] is True
        assert result["complexity_breakdown"] == SAMPLE_BREAKDOWN
        assert result["complexity_score"] == 0.7

    @pytest.mark.asyncio
    async def test_complexity_none_when_absent(self):
        """When agent.response has no complexity data, fields should be None."""
        from app.benchmarking.schemas import IngredientInfo, NutritionDish

        dish = NutritionDish(
            dish_id="dish_old",
            total_calories=300.0,
            total_mass=150.0,
            total_fat=10.0,
            total_carb=20.0,
            total_protein=25.0,
            ingredients=[IngredientInfo(id="1", name="Rice", grams=150.0)],
            complexity="simple",
        )

        # No complexity_breakdown or complexity_score in payload
        response_payload = {
            "type": "agent.response",
            "payload": {
                "status": "success",
                "nutritional_data": {"title": "Rice", "items": []},
            },
        }

        lines = [
            b"event: agent.response",
            f"data: {json.dumps(response_payload)}".encode(),
            b"",
        ]

        class MockStream:
            status_code = 200

            async def aiter_lines(self):
                for line in lines:
                    yield line.decode("utf-8")

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        with (
            patch("app.benchmarking.oracle_runner.settings") as mock_settings,
            patch("app.benchmarking.oracle_runner.create_client"),
        ):
            mock_settings.SUPABASE_URL = "http://supabase.test"
            mock_settings.SUPABASE_ANON_KEY = "anon-key"

            from app.benchmarking.oracle_runner import OracleRunner

            runner = OracleRunner(
                api_url="http://test.local",
                email="test@test.com",
                password="pass",  # noqa: S106
            )
            runner.supabase = MagicMock()
            runner.access_token = "fake-token"

            mock_upload = MagicMock()
            mock_upload.status_code = 200
            mock_upload.json.return_value = {"log_id": "log_old"}

            with (
                patch.object(runner.client, "post", return_value=mock_upload),
                patch.object(runner.client, "stream", return_value=MockStream()),
            ):
                result = await runner.run_dish(dish)

        assert result["success"] is True
        assert result["complexity_breakdown"] is None
        assert result["complexity_score"] is None


# ── Test 5.3: export_markdown score comparison table ─────────────


class TestExportMarkdownScoreComparison:
    """Tests for ExperimentLog.export_markdown() score comparison."""

    def test_score_comparison_section_rendered(self):
        """export_markdown should include Score Comparison table when complexity data exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = ExperimentLog(Path(tmpdir))

            result = ExperimentResult(
                experiment_id="test_001",
                prompt_version="v1",
                timestamp="2026-02-17T12:00:00",
                metrics={"calories": 50.0, "protein": 5.0},
                latency_stats={"mean_seconds": 3.0},
                per_dish_results=[
                    {
                        "dish_id": "d1",
                        "success": True,
                        "complexity_score": 0.7,
                        "complexity_breakdown": SAMPLE_BREAKDOWN,
                    },
                    {
                        "dish_id": "d2",
                        "success": True,
                        "complexity_score": 0.5,
                        "complexity_breakdown": SAMPLE_BREAKDOWN_INGREDIENTS,
                    },
                ],
                config={},
            )
            log.log_experiment(result)

            md = log.export_markdown()
            assert "Score Comparison (Old vs New)" in md
            assert "d1" in md
            assert "0.700" in md  # old score
            assert "0.750" in md  # new score from breakdown
            assert "volume" in md
            assert "ingredients" in md

    def test_no_comparison_when_no_complexity(self):
        """export_markdown should NOT include comparison table when no complexity data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = ExperimentLog(Path(tmpdir))

            result = ExperimentResult(
                experiment_id="test_002",
                prompt_version="v1",
                timestamp="2026-02-17T12:00:00",
                metrics={"calories": 50.0},
                latency_stats={"mean_seconds": 3.0},
                per_dish_results=[
                    {"dish_id": "d1", "success": True},
                ],
                config={},
            )
            log.log_experiment(result)

            md = log.export_markdown()
            assert "Score Comparison" not in md


# ── Test 5.4: Backward compatibility ────────────────────────────


class TestBackwardCompatibility:
    """Tests ensuring backward compat when complexity_breakdown is None."""

    def test_aggregate_complexity_with_none_breakdowns(self, metrics_calculator):
        """aggregate_complexity should handle all-None breakdowns gracefully."""
        results = [
            {"dish_id": "d1", "success": True, "complexity_breakdown": None},
            {"dish_id": "d2", "success": False, "complexity_breakdown": None},
        ]
        stats = metrics_calculator.aggregate_complexity(results)
        assert stats.total_scored == 0
        assert stats.mean_score == 0.0
        assert stats.clarification_triggered_count == 0
        assert stats.total_questions_asked == 0
        assert stats.dominant_factor_distribution == {}  # to_dict returns {}

    def test_per_dish_without_complexity_keys(self, metrics_calculator):
        """Results that don't even have the complexity keys should not crash."""
        results = [
            {"dish_id": "d1", "success": True},
            {"dish_id": "d2", "success": True},
        ]
        stats = metrics_calculator.aggregate_complexity(results)
        assert stats.total_scored == 0

    def test_complexity_metrics_to_dict_defaults(self):
        """Default ComplexityMetrics should serialize safely."""
        cm = ComplexityMetrics()
        d = cm.to_dict()
        assert d["total_scored"] == 0
        assert d["mean_score"] == 0.0
        assert d["clarification_triggered_count"] == 0
        assert d["total_questions_asked"] == 0
        assert d["dominant_factor_distribution"] == {}
