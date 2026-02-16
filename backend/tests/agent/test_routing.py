"""Tests for confidence-based routing logic."""

from app.agent.constants import AMPM_ENTRY, FINALIZE_LOG
from app.agent.routing import route_by_confidence


class TestRouteByConfidence:
    """Test suite for route_by_confidence function."""

    def test_high_confidence_routes_to_finalize(self):
        """High confidence (>= 0.85) should route to finalize_log."""
        state = {
            "overall_confidence": 0.90,
            "clarification_count": 0,
        }
        assert route_by_confidence(state) == FINALIZE_LOG

    def test_exact_threshold_routes_to_finalize(self):
        """Exactly 0.85 confidence should route to finalize_log."""
        state = {
            "overall_confidence": 0.85,
            "clarification_count": 0,
        }
        assert route_by_confidence(state) == FINALIZE_LOG

    def test_low_confidence_routes_to_ampm(self):
        """Low confidence (< 0.85) should route to AMPM entry."""
        state = {
            "overall_confidence": 0.70,
            "clarification_count": 0,
        }
        assert route_by_confidence(state) == AMPM_ENTRY

    def test_just_below_threshold_routes_to_ampm(self):
        """Just below 0.85 should route to AMPM entry."""
        state = {
            "overall_confidence": 0.849,
            "clarification_count": 0,
        }
        assert route_by_confidence(state) == AMPM_ENTRY

    def test_max_attempts_routes_to_finalize_despite_low_confidence(self):
        """Max clarification attempts (>= 2) should force finalize_log."""
        state = {
            "overall_confidence": 0.50,
            "clarification_count": 2,
        }
        assert route_by_confidence(state) == FINALIZE_LOG

    def test_max_attempts_exceeded_routes_to_finalize(self):
        """More than max attempts should still route to finalize_log."""
        state = {
            "overall_confidence": 0.30,
            "clarification_count": 5,
        }
        assert route_by_confidence(state) == FINALIZE_LOG

    def test_one_attempt_with_low_confidence_routes_to_ampm(self):
        """Under max attempts with low confidence should route to AMPM."""
        state = {
            "overall_confidence": 0.60,
            "clarification_count": 1,
        }
        assert route_by_confidence(state) == AMPM_ENTRY

    def test_zero_confidence_routes_to_ampm(self):
        """Zero confidence should route to AMPM."""
        state = {
            "overall_confidence": 0.0,
            "clarification_count": 0,
        }
        assert route_by_confidence(state) == AMPM_ENTRY

    def test_missing_confidence_defaults_to_zero(self):
        """Missing overall_confidence should default to 0.0 (AMPM)."""
        state = {
            "clarification_count": 0,
        }
        assert route_by_confidence(state) == AMPM_ENTRY

    def test_missing_clarification_count_defaults_to_zero(self):
        """Missing clarification_count should default to 0."""
        state = {
            "overall_confidence": 0.50,
        }
        assert route_by_confidence(state) == AMPM_ENTRY

