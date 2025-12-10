import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from datetime import datetime
from app.api import deps
from app.main import app
from app.core.security import UserContext
from app.models.log import DietaryLog
from sqlalchemy import select, text


@pytest.fixture
def override_auth():
    """Override authentication for the test."""
    user_id = uuid4()
    user_context = UserContext(
        id=user_id,
        aud="authenticated",
        role="authenticated",
        email="test@example.com",
        app_metadata={}
    )
    app.dependency_overrides[deps.get_current_user] = lambda: user_context
    app.dependency_overrides[deps.oauth2_scheme] = lambda: "test-token"
    yield user_context
    # Cleanup
    if deps.get_current_user in app.dependency_overrides:
        del app.dependency_overrides[deps.get_current_user]
    if deps.oauth2_scheme in app.dependency_overrides:
        del app.dependency_overrides[deps.oauth2_scheme]

from datetime import datetime, timezone

# ... imports ...

@pytest.mark.asyncio
async def test_stream_error_updates_db_status(test_client, db_session, override_auth):
    """
    Integration test verifying that an exception during streaming analysis
    updates the DietaryLog status to 'failed' in the database.
    """
    user_id = override_auth.id
    log_id = uuid4()
    
    # Check if table exists
    try:
        await db_session.execute(text("SELECT 1 FROM dietary_logs LIMIT 1"))
    except Exception as e:
        pytest.fail(f"Database table check failed: {e}")

    # Create fake user in auth.users to satisfy FK
    unique_email = f"test_{uuid4()}@example.com"
    try:
        await db_session.execute(
            text("""
            INSERT INTO auth.users (id, aud, role, email)
            VALUES (:id, 'authenticated', 'authenticated', :email)
            ON CONFLICT (id) DO NOTHING
            """),
            {"id": user_id, "email": unique_email}
        )
        await db_session.execute(
            text("""
            INSERT INTO dietary_logs (id, user_id, image_path, status, description, created_at, client_timestamp)
            VALUES (:id, :user_id, :image_path, 'processing', 'Initial description', NOW(), NOW())
            """),
            {"id": log_id, "user_id": user_id, "image_path": f"{user_id}/test.jpg"}
        )
        await db_session.commit()
    except Exception as e:
        pytest.fail(f"Setup insert failed: {e}")
    
    # Define a context manager to mock async_session_maker expecting new sessions
    class MockSessionMaker:
        def __init__(self):
            pass
        async def __aenter__(self):
             return db_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
             pass

    # Mock LLM service AND async_session_maker
    with patch("app.services.llm_service.analyze_multimodal_streaming", new_callable=AsyncMock) as mock_llm, \
         patch("app.agent.nodes.async_session_maker") as mock_maker:
        
        mock_llm.side_effect = Exception("Simulated LLM Critical Failure")
        mock_maker.return_value = MockSessionMaker()
        
        # 3. Call the stream endpoint
        payload = {
            "log_id": str(log_id),
            "image_path": f"{user_id}/test.jpg"
        }
        
        response = await test_client.post("/api/v1/analysis/stream", json=payload)
        
        # 4. Verify the endpoint returned 200 (SSE stream starts, then sends error event)
        assert response.status_code == 200
        content = response.text
        
        # Verify error event was emitted
        assert "agent.error" in content
        assert "ANALYSIS_ERROR" in content
        
        # 5. Verify Database update
        # We need to expire/refresh to get latest state
        db_session.expire_all()
        
        result = await db_session.execute(
            select(DietaryLog).where(DietaryLog.id == log_id)
        )
        updated_log = result.scalar_one()
        
        assert updated_log.status == "failed", f"Status was {updated_log.status}, expected 'failed'"
        assert "Simulated LLM Critical Failure" in updated_log.description
