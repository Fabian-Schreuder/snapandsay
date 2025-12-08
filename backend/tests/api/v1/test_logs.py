import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy import text

from app.api.deps import get_current_user
from app.core.security import UserContext
from app.main import app
from app.models.log import DietaryLog


@pytest.mark.asyncio
async def test_get_logs_returns_empty_list_when_none_exist(test_client, db_session):
    """Test that endpoint returns empty list when no logs exist for user."""
    user_id = uuid4()
    mock_user = UserContext(id=user_id, aud="authenticated", role="authenticated")
    
    await db_session.execute(text("SET session_replication_role = replica"))
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    response = await test_client.get("/api/v1/logs")
    
    app.dependency_overrides = {}
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_get_logs_filters_by_date_correctly(test_client, db_session):
    """Test that logs are filtered by date and sorted descending."""
    user_id = uuid4()
    mock_user = UserContext(id=user_id, aud="authenticated", role="authenticated")
    
    await db_session.execute(text("SET session_replication_role = replica"))
    
    # Create logs for today
    today = datetime.now(timezone.utc).date()
    log1 = DietaryLog(
        user_id=user_id,
        image_path=f"{user_id}/image1.jpg",
        status="logged",
        calories=300,
        description="Breakfast",
        created_at=datetime.combine(today, datetime.min.time().replace(hour=8), tzinfo=timezone.utc),
    )
    log2 = DietaryLog(
        user_id=user_id,
        image_path=f"{user_id}/image2.jpg",
        status="logged",
        calories=500,
        description="Lunch",
        created_at=datetime.combine(today, datetime.min.time().replace(hour=12), tzinfo=timezone.utc),
    )
    # Create log for yesterday (should not be returned for today)
    yesterday = today - timedelta(days=1)
    log3 = DietaryLog(
        user_id=user_id,
        image_path=f"{user_id}/image3.jpg",
        status="logged",
        calories=400,
        description="Yesterday dinner",
        created_at=datetime.combine(yesterday, datetime.min.time().replace(hour=19), tzinfo=timezone.utc),
    )
    
    db_session.add_all([log1, log2, log3])
    await db_session.commit()
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # Request today's logs
    response = await test_client.get(f"/api/v1/logs?date={today.isoformat()}")
    
    app.dependency_overrides = {}
    
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 2
    # Should be sorted by created_at DESC (newest first)
    assert data["data"][0]["description"] == "Lunch"
    assert data["data"][1]["description"] == "Breakfast"


@pytest.mark.asyncio
async def test_get_logs_requires_authentication(test_client, db_session):
    """Test that endpoint returns 401 without authentication."""
    # No auth override - should fail
    response = await test_client.get("/api/v1/logs")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_logs_only_returns_logged_status(test_client, db_session):
    """Test that only logs with status='logged' are returned."""
    user_id = uuid4()
    mock_user = UserContext(id=user_id, aud="authenticated", role="authenticated")
    
    await db_session.execute(text("SET session_replication_role = replica"))
    
    today = datetime.now(timezone.utc)
    
    # Create logs with different statuses
    log_processing = DietaryLog(
        user_id=user_id,
        image_path=f"{user_id}/processing.jpg",
        status="processing",
        created_at=today,
    )
    log_clarification = DietaryLog(
        user_id=user_id,
        image_path=f"{user_id}/clarification.jpg",
        status="clarification",
        created_at=today,
    )
    log_logged = DietaryLog(
        user_id=user_id,
        image_path=f"{user_id}/logged.jpg",
        status="logged",
        calories=250,
        description="Completed meal",
        created_at=today,
    )
    
    db_session.add_all([log_processing, log_clarification, log_logged])
    await db_session.commit()
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    response = await test_client.get("/api/v1/logs")
    
    app.dependency_overrides = {}
    
    assert response.status_code == 200
    data = response.json()
    # Only the 'logged' status log should be returned
    assert data["meta"]["total"] == 1
    assert data["data"][0]["description"] == "Completed meal"


@pytest.mark.asyncio
async def test_get_logs_handles_timezone_correctly(test_client, db_session):
    """Test UTC boundary handling for date filtering."""
    user_id = uuid4()
    mock_user = UserContext(id=user_id, aud="authenticated", role="authenticated")
    
    await db_session.execute(text("SET session_replication_role = replica"))
    
    # Create a log at 23:59 UTC on a specific date
    test_date = datetime(2024, 1, 15, tzinfo=timezone.utc).date()
    late_log = DietaryLog(
        user_id=user_id,
        image_path=f"{user_id}/late.jpg",
        status="logged",
        calories=100,
        description="Late night snack",
        created_at=datetime(2024, 1, 15, 23, 59, 0, tzinfo=timezone.utc),
    )
    # Create a log at 00:01 UTC on the next day
    early_next_day = DietaryLog(
        user_id=user_id,
        image_path=f"{user_id}/early.jpg",
        status="logged",
        calories=200,
        description="Early breakfast",
        created_at=datetime(2024, 1, 16, 0, 1, 0, tzinfo=timezone.utc),
    )
    
    db_session.add_all([late_log, early_next_day])
    await db_session.commit()
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # Request logs for 2024-01-15
    response = await test_client.get("/api/v1/logs?date=2024-01-15")
    
    app.dependency_overrides = {}
    
    assert response.status_code == 200
    data = response.json()
    # Only the late night snack should be returned for 2024-01-15
    assert data["meta"]["total"] == 1
    assert data["data"][0]["description"] == "Late night snack"
