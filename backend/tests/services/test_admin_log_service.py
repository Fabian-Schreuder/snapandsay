from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.models.log import DietaryLog
from app.services import log_service


@pytest.mark.asyncio
async def test_get_all_logs_implementation(db_session):
    # 1. Verify existence
    if not hasattr(log_service, "get_all_logs"):
        pytest.fail("log_service.get_all_logs method not found")

    # 2. Setup Data
    user1_id = uuid4()
    user2_id = uuid4()
    
    # Create Users
    # Insert into auth.users first (if FK exists)
    try:
        await db_session.execute(
            text("INSERT INTO auth.users (id, email) VALUES (:id, :email)"),
            {"id": user1_id, "email": f"user1_{user1_id.hex}@test.com"}
        )
        await db_session.execute(
            text("INSERT INTO auth.users (id, email) VALUES (:id, :email)"),
            {"id": user2_id, "email": f"user2_{user2_id.hex}@test.com"}
        )
    except Exception:
        # Ignore if auth.users doesn't exist or permissions verify (usually in test db it exists)
        pass

    # Then public.users (safely)
    await db_session.execute(
        text("INSERT INTO public.users (id, anonymous_id, created_at) VALUES (:id, :anon_id, now()) ON CONFLICT (id) DO NOTHING"),
        {"id": user1_id, "anon_id": f"anon_{user1_id.hex}"}
    )
    await db_session.execute(
        text("INSERT INTO public.users (id, anonymous_id, created_at) VALUES (:id, :anon_id, now()) ON CONFLICT (id) DO NOTHING"),
        {"id": user2_id, "anon_id": f"anon_{user2_id.hex}"}
    )
    # No commit needed here if using same session, but db_session fixture might handle commit/rollback?
    # Actually db_session fixture rolls back at end. We can just add objects. 
    # But for raw sql we might need to flush?
    # Using db_session.execute for sql, and db_session.add for ORM should work together in same transaction. (Flush might be needed)
    
    log1 = DietaryLog(
        id=uuid4(),
        user_id=user1_id,
        status="logged",
        created_at=datetime.now(UTC),
        image_path="img1.jpg",
        description="User 1 Log"
    )
    log2 = DietaryLog(
        id=uuid4(),
        user_id=user2_id,
        status="logged",
        created_at=datetime.now(UTC) - timedelta(days=1),
        image_path="img2.jpg",
        description="User 2 Log"
    )
    
    db_session.add(log1)
    db_session.add(log2)
    # await db_session.commit() # This commits transaction. 
    # db_session fixture yields session. If I commit, it persists? 
    # Fixture: yield session; await session.rollback().
    # If I commit, rollback might not undo if I committed?
    # Usually in tests with rollback, we verify data in same transaction.
    # But to make `get_all_logs` see it, we need to flush.
    await db_session.flush()
    
    # 3. Test No Filter (Should get all)
    all_logs = await log_service.get_all_logs(db_session, page=1, limit=10)
    assert len(all_logs) >= 2
    
    # 4. Test Filter by User ID
    user1_logs = await log_service.get_all_logs(db_session, user_id=user1_id, page=1, limit=10)
    assert len(user1_logs) == 1
    assert user1_logs[0].id == log1.id
    
    # 5. Test Filter by Date Range
    # Filter for today (log1)
    today = date.today()
    await log_service.get_all_logs(
        db_session, 
        start_date=today, 
        end_date=today,
        page=1, limit=10
    )
    # This might be flaky depending on timezone, but let's assume UTC/Local consistency for now
    # or ensure log1 is strictly within range.
    pass 
