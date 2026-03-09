"""Tests for SSE schema backwards compatibility and complexity fields."""

from app.schemas.sse import AgentResponse


class TestAgentResponseComplexity:
    """Tests for AgentResponse with complexity fields."""

    def test_with_complexity_fields(self):
        """AgentResponse should accept complexity fields as dict."""
        resp = AgentResponse(
            log_id="abc-123",
            nutritional_data={"items": []},
            status="success",
            complexity_breakdown={"score": 5.0, "dominant_factor": "item_count"},
            complexity_score=5.0,
        )
        assert resp.complexity_breakdown == {"score": 5.0, "dominant_factor": "item_count"}
        assert resp.complexity_score == 5.0

    def test_without_complexity_fields(self):
        """AgentResponse should work without complexity fields (backwards compat)."""
        resp = AgentResponse(
            log_id="abc-123",
            nutritional_data={"items": []},
            status="success",
        )
        assert resp.complexity_breakdown is None
        assert resp.complexity_score is None

    def test_serialization_with_complexity(self):
        """Serialization should include complexity fields when present."""
        resp = AgentResponse(
            log_id="abc-123",
            nutritional_data={"items": []},
            complexity_breakdown={"score": 3.0},
            complexity_score=3.0,
        )
        data = resp.model_dump()
        assert data["complexity_breakdown"] == {"score": 3.0}
        assert data["complexity_score"] == 3.0

    def test_serialization_without_complexity(self):
        """Serialization should include None complexity fields when absent."""
        resp = AgentResponse(
            log_id="abc-123",
            nutritional_data={"items": []},
        )
        data = resp.model_dump()
        assert data["complexity_breakdown"] is None
        assert data["complexity_score"] is None
