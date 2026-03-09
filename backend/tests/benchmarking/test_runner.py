import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.benchmarking.oracle_runner import OracleRunner
from app.benchmarking.schemas import IngredientInfo, NutritionDish


@pytest.fixture
def mock_dish():
    return NutritionDish(
        dish_id="dish_123",
        total_calories=500.0,
        total_mass=200.0,
        total_fat=20.0,
        total_carb=30.0,
        total_protein=40.0,
        ingredients=[
            IngredientInfo(id="ing_1", name="Chicken", grams=100.0),
            IngredientInfo(id="ing_2", name="Rice", grams=100.0),
        ],
        complexity="simple",
        image_path="/tmp/fake.png",  # noqa: S108
    )


def _sse_line(event_type: str, payload: dict) -> str:
    """Build an SSE data line matching the actual server format (format_sse output)."""
    wrapper = {"type": event_type, "payload": payload}
    return f"data: {json.dumps(wrapper)}"


def _make_stream(lines: list[str]):
    """Create a mock stream context manager from a list of SSE lines."""

    class MockStream:
        status_code = 200

        async def aiter_lines(self):
            for line in lines:
                yield line

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    return MockStream()


@pytest.fixture
def runner():
    with patch("app.benchmarking.oracle_runner.settings") as mock_settings:
        mock_settings.SUPABASE_URL = "http://supabase.test"
        mock_settings.SUPABASE_ANON_KEY = "anon-key"

        with patch("app.benchmarking.oracle_runner.create_client"):
            runner = OracleRunner(
                api_url="http://test.local",
                email="test@example.com",
                password="password",  # noqa: S106
            )
            runner.supabase = MagicMock()
            return runner


@pytest.mark.asyncio
async def test_run_dish_upload_failure(runner, mock_dish):
    runner.access_token = "fake-token"

    with patch.object(runner.client, "post", side_effect=Exception("Upload Error")):
        result = await runner.run_dish(mock_dish)

    assert result["success"] is False
    assert "Upload" in result["error"]


@pytest.mark.asyncio
async def test_run_dish_full_flow(runner, mock_dish):
    """Test full flow: upload → clarification → reconnect → response."""
    runner.access_token = "fake-token"

    # Mock Upload
    mock_upload_resp = MagicMock()
    mock_upload_resp.status_code = 200
    mock_upload_resp.json.return_value = {"log_id": "log_abc"}
    mock_upload_resp.raise_for_status = MagicMock()

    # Stream 1: returns clarification (stream terminates after)
    stream1 = _make_stream([
        _sse_line("agent.clarification", {
            "questions": [
                {"item_name": "Chicken", "question": "Is this spicy?", "options": ["yes", "no"]}
            ],
            "context": {},
            "log_id": "log_abc",
        }),
        "",
    ])

    # Stream 2: returns response (after reconnection)
    stream2 = _make_stream([
        _sse_line("agent.response", {
            "status": "success",
            "nutritional_data": {"title": "Chicken"},
            "complexity_breakdown": {"score": 5.0, "dominant_factor": "item_count"},
            "complexity_score": 5.0,
        }),
        "",
    ])

    # Mock clarify submit response
    mock_clarify_resp = MagicMock()
    mock_clarify_resp.raise_for_status = MagicMock()

    # post is called for: 1) upload, 2) _submit_answers
    mock_post = AsyncMock(side_effect=[mock_upload_resp, mock_clarify_resp])

    # stream is called twice: first for initial, then for reconnection
    mock_stream = MagicMock(side_effect=[stream1, stream2])

    with (
        patch.object(runner.client, "post", mock_post),
        patch.object(runner.client, "stream", mock_stream),
    ):
        result = await runner.run_dish(mock_dish)

    assert result["success"] is True
    assert result["turns"] == 1
    assert result["log_id"] == "log_abc"

    # Verify complexity data extracted
    assert result["complexity_breakdown"] == {"score": 5.0, "dominant_factor": "item_count"}
    assert result["complexity_score"] == 5.0

    # Verify post calls
    assert mock_post.call_count == 2
    # Call 1: Clarify — verify ClarifyRequest payload format
    args, kwargs = mock_post.call_args_list[1]
    assert "/api/v1/analysis/clarify/log_abc" in args[0]
    assert "responses" in kwargs["json"]
    assert isinstance(kwargs["json"]["responses"], list)
    assert "This dish contains" in kwargs["json"]["responses"][0]["response"]


@pytest.mark.asyncio
async def test_clarification_question_extraction(runner, mock_dish):
    """Test that clarification questions are extracted from the questions list."""
    runner.access_token = "fake-token"

    # Stream 1: clarification with multiple questions
    stream1 = _make_stream([
        _sse_line("agent.clarification", {
            "questions": [
                {"item_name": "Burger", "question": "What kind of burger?", "options": ["beef", "veggie"]},
                {"item_name": "Sauce", "question": "What sauce?", "options": ["ketchup", "mayo"]},
            ],
            "context": {},
            "log_id": "log_q",
        }),
        "",
    ])

    # Stream 2: response after reconnection
    stream2 = _make_stream([
        _sse_line("agent.response", {
            "status": "success",
            "nutritional_data": {"title": "Burger"},
        }),
        "",
    ])

    mock_clarify = AsyncMock()
    mock_stream = MagicMock(side_effect=[stream1, stream2])

    with (
        patch.object(runner.client, "post", mock_clarify),
        patch.object(runner.client, "stream", mock_stream),
    ):
        result = await runner._process_loop("log_q", mock_dish, {}, "http://img.png")

    assert result["turns"] == 1
    # Both questions should be in clarification history
    assert len(result["clarification_history"]) == 2
    assert result["clarification_history"][0]["question"] == "What kind of burger?"
    assert result["clarification_history"][0]["item_name"] == "Burger"
    assert result["clarification_history"][1]["question"] == "What sauce?"
    assert result["clarification_history"][1]["item_name"] == "Sauce"


@pytest.mark.asyncio
async def test_submit_answers_is_awaited(runner, mock_dish):
    """Test that _submit_answers is awaited (not fire-and-forget)."""
    runner.access_token = "fake-token"

    call_order = []

    original_submit = runner._submit_answers

    async def tracking_submit(*args, **kwargs):
        call_order.append("submit_start")
        await original_submit(*args, **kwargs)
        call_order.append("submit_end")

    # Stream 1: clarification
    stream1 = _make_stream([
        _sse_line("agent.clarification", {
            "questions": [{"item_name": "X", "question": "Q?", "options": []}],
            "context": {},
            "log_id": "log_await",
        }),
        "",
    ])

    # Stream 2: response
    stream2_lines = [
        _sse_line("agent.response", {
            "status": "success",
            "nutritional_data": {"title": "X"},
        }),
        "",
    ]

    class TrackingStream:
        status_code = 200

        async def aiter_lines(self):
            for line in stream2_lines:
                if line:
                    call_order.append("line_processed")
                yield line

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    mock_resp = AsyncMock()
    mock_stream = MagicMock(side_effect=[stream1, TrackingStream()])

    with (
        patch.object(runner, "_submit_answers", side_effect=tracking_submit),
        patch.object(runner.client, "post", mock_resp),
        patch.object(runner.client, "stream", mock_stream),
    ):
        await runner._process_loop("log_await", mock_dish, {}, "http://img.png")

    # submit_end must appear before the response line is processed
    submit_end_idx = call_order.index("submit_end")
    response_line_indices = [i for i, x in enumerate(call_order) if x == "line_processed"]
    assert any(i > submit_end_idx for i in response_line_indices)


@pytest.mark.asyncio
async def test_run_dish_max_turns_limit(runner, mock_dish):
    """Test that max_turns limits clarification rounds."""
    runner.access_token = "fake-token"
    runner.max_turns = 1

    mock_upload = AsyncMock()
    mock_upload.return_value = MagicMock(
        status_code=200,
        json=MagicMock(return_value={"log_id": "log_limit"}),
        raise_for_status=MagicMock(),
    )

    # Stream 1: first clarification (turns=1, processed normally)
    stream1 = _make_stream([
        _sse_line("agent.clarification", {
            "questions": [{"item_name": "A", "question": "Q1?", "options": []}],
            "context": {},
            "log_id": "log_limit",
        }),
        "",
    ])

    # Stream 2: second clarification (turns=2, exceeds max_turns=1, break)
    stream2 = _make_stream([
        _sse_line("agent.clarification", {
            "questions": [{"item_name": "B", "question": "Q2?", "options": []}],
            "context": {},
            "log_id": "log_limit",
        }),
        "",
    ])

    mock_stream = MagicMock(side_effect=[stream1, stream2])

    with (
        patch.object(runner.client, "post", mock_upload),
        patch.object(runner.client, "stream", mock_stream),
    ):
        result = await runner.run_dish(mock_dish)

    # turns=1 (first clarification processed), turns=2 (second triggers break)
    assert result["turns"] == 2
    assert result["success"] is False  # No final response event


@pytest.mark.asyncio
async def test_mode_validation(runner):
    """Test that invalid mode raises ValueError."""
    with (
        patch("app.benchmarking.oracle_runner.settings") as mock_settings,
        patch("app.benchmarking.oracle_runner.create_client"),
    ):
        mock_settings.SUPABASE_URL = "http://supabase.test"
        mock_settings.SUPABASE_ANON_KEY = "anon-key"

        with pytest.raises(ValueError, match="Invalid mode"):
            OracleRunner(
                api_url="http://test.local",
                email="test@example.com",
                password="password",  # noqa: S106
                mode="invalid-mode",
            )


@pytest.mark.asyncio
async def test_mode_sets_force_flags(runner, mock_dish):
    """Test that stream_payload includes correct force flags per mode."""
    runner.access_token = "fake-token"

    # Test single-shot mode
    runner.mode = "single-shot"

    stream1 = _make_stream([
        _sse_line("agent.response", {
            "status": "success",
            "nutritional_data": {"title": "Test"},
        }),
        "",
    ])

    captured_payloads = []

    def capture_stream(*args, **kwargs):
        captured_payloads.append(kwargs.get("json", {}))
        return stream1

    mock_stream = MagicMock(side_effect=capture_stream)

    with patch.object(runner.client, "stream", mock_stream):
        await runner._process_loop("log_1", mock_dish, {}, "http://img.png")

    assert captured_payloads[0]["force_finalize"] is True
    assert captured_payloads[0]["force_clarify"] is False


@pytest.mark.asyncio
async def test_semantic_gatekeeper_in_single_shot(runner, mock_dish):
    """Test handling semantic gatekeeper clarification in single-shot mode."""
    runner.access_token = "fake-token"
    runner.mode = "single-shot"

    # Stream 1: semantic gatekeeper fires clarification despite force_finalize
    stream1 = _make_stream([
        _sse_line("agent.clarification", {
            "questions": [{"item_name": "Soup", "question": "What kind of soup?", "options": []}],
            "context": {"type": "semantic"},
            "log_id": "log_sg",
        }),
        "",
    ])

    # Stream 2: response after auto-answer
    stream2 = _make_stream([
        _sse_line("agent.response", {
            "status": "success",
            "nutritional_data": {"title": "Soup"},
        }),
        "",
    ])

    mock_clarify = AsyncMock()
    mock_stream = MagicMock(side_effect=[stream1, stream2])

    with (
        patch.object(runner.client, "post", mock_clarify),
        patch.object(runner.client, "stream", mock_stream),
    ):
        result = await runner._process_loop("log_sg", mock_dish, {}, "http://img.png")

    assert result["success"] is True
    assert result["semantic_gatekeeper_fired"] is True
    assert result["turns"] == 1


@pytest.mark.asyncio
async def test_max_reconnections_limit(runner, mock_dish):
    """Test that max_reconnections prevents infinite loops."""
    runner.access_token = "fake-token"
    runner.max_turns = 100  # High limit to not trigger max_turns

    # Create streams that always return clarification
    def always_clarify(*args, **kwargs):
        return _make_stream([
            _sse_line("agent.clarification", {
                "questions": [{"item_name": "X", "question": "Q?", "options": []}],
                "context": {},
                "log_id": "log_inf",
            }),
            "",
        ])

    mock_clarify = AsyncMock()
    mock_stream = MagicMock(side_effect=always_clarify)

    with (
        patch.object(runner.client, "post", mock_clarify),
        patch.object(runner.client, "stream", mock_stream),
    ):
        result = await runner._process_loop("log_inf", mock_dish, {}, "http://img.png")

    assert result["success"] is False
    assert "Max reconnections" in (result.get("error") or "")
