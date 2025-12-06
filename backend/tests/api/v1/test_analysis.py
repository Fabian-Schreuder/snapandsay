import pytest
from uuid import uuid4
from app.api.deps import get_current_user
from app.core.security import UserContext
from app.main import app

# Mock User
class MockUser(UserContext):
    def __init__(self, user_id):
        self.id = user_id
        self.email = "test@example.com"
        self.role = "authenticated"

@pytest.mark.asyncio
async def test_upload_analysis_success(test_client, db_session):
    # 1. Mock Authentication
    user_id = uuid4()
    mock_user = MockUser(user_id)
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # 2. Prepare Payload
    payload = {
        "image_path": f"{user_id}/test_image.jpg",
        "audio_path": f"{user_id}/test_audio.webm",
        "client_timestamp": "2023-10-27T10:00:00Z"
    }
    
    # 3. Request
    response = await test_client.post("/api/v1/analysis/upload", json=payload)
    
    # 4. Cleanup overrides
    app.dependency_overrides = {}
    
    # 5. Assertions
    assert response.status_code == 200
    data = response.json()
    assert "log_id" in data
    assert data["status"] == "processing"
    
    # 6. Verify DB
    # We can check DB via db_session, but since transaction is rolled back, 
    # we need to ensure the endpoint committed or flushed? 
    # The endpoint should commit.
    # But db_session fixture rolls back AFTER test.
    # We can query using db_session.
    from sqlalchemy import select
    from app.models.log import DietaryLog
    
    result = await db_session.execute(select(DietaryLog).where(DietaryLog.id == data["log_id"]))
    log_entry = result.scalar_one_or_none()
    
    assert log_entry is not None
    assert str(log_entry.user_id) == str(user_id)
    assert log_entry.image_path == payload["image_path"]
    assert log_entry.status == "processing"
