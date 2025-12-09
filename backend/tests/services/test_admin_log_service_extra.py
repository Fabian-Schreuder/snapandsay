
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import text
from app.services import log_service
from app.models.log import DietaryLog

@pytest.mark.asyncio
async def test_get_all_logs_calorie_filtering(db_session):
    # Setup Data
    user_id = uuid4()
    
    
    # Create User in auth.users first (FK constraint)
    try:
        await db_session.execute(
            text("INSERT INTO auth.users (id, email) VALUES (:id, :email)"),
            {"id": user_id, "email": f"user_{user_id.hex}@test.com"}
        )
    except Exception:
        pass # Ignore if already exists (cleanup might be flaky)

    # Create User in public.users
    await db_session.execute(
        text("INSERT INTO public.users (id, anonymous_id, created_at) VALUES (:id, :anon_id, now()) ON CONFLICT (id) DO NOTHING"),
        {"id": user_id, "anon_id": f"anon_{user_id.hex}"}
    )

    log_low = DietaryLog(
        id=uuid4(),
        user_id=user_id,
        status="logged",
        calories=100,
        image_path="low.jpg",
        created_at=datetime.now(timezone.utc)
    )
    log_med = DietaryLog(
        id=uuid4(),
        user_id=user_id,
        status="logged",
        calories=500,
        image_path="med.jpg",
        created_at=datetime.now(timezone.utc)
    )
    log_high = DietaryLog(
        id=uuid4(),
        user_id=user_id,
        status="logged",
        calories=1000,
        image_path="high.jpg",
        created_at=datetime.now(timezone.utc)
    )
    
    db_session.add(log_low)
    db_session.add(log_med)
    db_session.add(log_high)
    await db_session.flush()
    
    # Test Min Calories (>= 500) -> should get med and high (2)
    logs_min = await log_service.get_all_logs(db_session, user_id=user_id, min_calories=500)
    assert len(logs_min) == 2
    ids = [l.id for l in logs_min]
    assert log_med.id in ids
    assert log_high.id in ids
    assert log_low.id not in ids
    
    # Test Max Calories (<= 500) -> should get low and med (2)
    logs_max = await log_service.get_all_logs(db_session, user_id=user_id, max_calories=500)
    assert len(logs_max) == 2
    ids = [l.id for l in logs_max]
    assert log_low.id in ids
    assert log_med.id in ids
    assert log_high.id not in ids
    
    # Test Range (200 - 800) -> should get med (1)
    logs_range = await log_service.get_all_logs(db_session, user_id=user_id, min_calories=200, max_calories=800)
    assert len(logs_range) == 1
    assert logs_range[0].id == log_med.id
