import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.benchmarking.oracle_runner import OracleRunner
from app.benchmarking.schemas import NutritionDish, IngredientInfo

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
            IngredientInfo(id="ing_2", name="Rice", grams=100.0)
        ],
        complexity="simple",
        image_path="/tmp/fake.png"
    )

@pytest.fixture
def runner():
    with patch("app.benchmarking.oracle_runner.settings") as mock_settings:
        mock_settings.SUPABASE_URL = "http://supabase.test"
        mock_settings.SUPABASE_ANON_KEY = "anon-key"
        
        # We also need to mock create_client since it's called in __init__
        with patch("app.benchmarking.oracle_runner.create_client") as mock_create_client:
            runner = OracleRunner(
                api_url="http://test.local",
                email="test@example.com",
                password="password"
            )
            # Mock the supabase client instance on the runner
            runner.supabase = MagicMock()
            
            return runner

@pytest.mark.asyncio
async def test_run_dish_upload_failure(runner, mock_dish):
    # Mock login to avoid network
    runner.access_token = "fake-token"
    
    # Mock Upload Failure
    with patch.object(runner.client, "post", side_effect=Exception("Upload Error")) as mock_post:
        result = await runner.run_dish(mock_dish)
        
    assert result["success"] is False
    assert "Upload" in result["error"]

@pytest.mark.asyncio
async def test_run_dish_full_flow(runner, mock_dish):
    runner.access_token = "fake-token"
    
    # 1. Mock Upload Success
    mock_upload_resp = MagicMock()
    mock_upload_resp.status_code = 200
    mock_upload_resp.json.return_value = {"log_id": "log_abc"}
    
    # 2. Mock SSE Stream
    # We need to simulate a stream of lines
    # Clarification -> Response
    
    lines = [
        # Clarification Event
        b"event: agent.clarification",
        b'data: {"question": "Is this spicy?", "log_id": "log_abc"}',
        b"",
        # Final Response Event
        b"event: agent.response",
        b'data: {"status": "success", "nutritional_data": {"title": "Chicken"}}',
        b"",
    ]
    
    class MockStreamContext:
        def __init__(self, *args, **kwargs):
            self.status_code = 200
        
        async def aiter_lines(self):
            for line in lines:
                yield line.decode("utf-8")
        
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, *args):
            pass

    # 3. Mock Clarify Submit
    mock_clarify_resp = MagicMock()
    mock_clarify_resp.status_code = 200
    
    with patch.object(runner.client, "post") as mock_post, \
         patch.object(runner.client, "stream") as mock_stream:
             
        # Configure Mocks
        mock_post.side_effect = [
            mock_upload_resp, # 1. Upload
            mock_clarify_resp # 2. Submit Answer
        ]
        mock_stream.return_value = MockStreamContext()
        
        # Run
        result = await runner.run_dish(mock_dish)
        
        # In the implementation, _submit_answer is a background task. 
        # We need to ensure it runs before checking assertions.
        # Since we use MagicMock for client.post, it's synchronous in the test, 
        # but the task creation puts it on the loop.
        
        # Wait for all pending tasks on the loop
        pending = asyncio.all_tasks()
        for t in pending:
            if t is not asyncio.current_task():
                try:
                    await t
                except Exception:
                    pass

        # Assertions
        assert result["success"] is True
        assert result["turns"] == 1
        assert result["log_id"] == "log_abc"
        
        # Verify Post Calls
        # Call 0: Upload
        assert mock_post.call_count == 2
        # Call 1: Clarify
        args, kwargs = mock_post.call_args_list[1]
        assert "/api/v1/analysis/clarify/log_abc" in args[0]
        assert "This dish contains" in kwargs["json"]["response"]

@pytest.mark.asyncio
async def test_run_dish_max_turns_limit(runner, mock_dish):
    runner.access_token = "fake-token"
    runner.max_turns = 1
    
    mock_upload = MagicMock()
    mock_upload.status_code = 200
    mock_upload.json.return_value = {"log_id": "log_limit"}
    
    # Send 2 clarifications
    lines = [
        b"event: agent.clarification",
        b'data: {"question": "Q1?"}',
        b"",
        b"event: agent.clarification",
        b'data: {"question": "Q2?"}',
        b"",
    ]
    
    class MockStream:
        status_code = 200
        async def aiter_lines(self):
            for line in lines:
                yield line.decode("utf-8")
        async def __aenter__(s): return s
        async def __aexit__(*args): pass
        
    with patch.object(runner.client, "post", return_value=mock_upload) as m_post, \
         patch.object(runner.client, "stream", return_value=MockStream()):
         
        result = await runner.run_dish(mock_dish)
        
        # Should stop after Q2 because loop breaks when turns > max
        # It breaks *before* submitting answer if turns > max? 
        # Logic in runner:
        # turns += 1
        # if turns > max: break
        
        # So for max=1: 
        # Event 1: turns=1. Not > 1. Submit ans.
        # Event 2: turns=2. > 1. Break.
        
        assert result["turns"] == 2
        assert result["success"] is False # No final event
