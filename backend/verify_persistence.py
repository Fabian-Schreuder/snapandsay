import asyncio
import os
import uuid

# Mock envs for Settings
os.environ["SUPABASE_JWT_SECRET"] = "super-secret-jwt-token-for-testing-purposes-only"
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres"  # fallback if .env missing
)
os.environ["SUPABASE_URL"] = "http://localhost:54321"

from app.agent.nodes import finalize_log_streaming
from app.database import async_session_maker
from app.models.log import DietaryLog
from app.models.user import User


async def verify_persistence():
    # 1. Create a dummy user and log
    log_id = uuid.uuid4()
    print(f"Creating test log {log_id}...")

    from sqlalchemy import select

    async with async_session_maker() as session:
        # Fetch existing user to avoid FK issues with auth.users
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            print("No users found in DB. Cannot verify persistence without a user.")
            return

        user_id = user.id
        print(f"Using existing user {user_id}")

        # Create initial log
        log = DietaryLog(
            id=log_id, user_id=user_id, image_path="test.jpg", status="processing", description="Initial"
        )
        session.add(log)
        await session.commit()

    # 2. Simulate Agent State with full data
    state = {
        "log_id": log_id,
        "overall_confidence": 0.95,
        "clarification_count": 0,
        "nutritional_data": {
            "items": [
                {
                    "name": "Test Burger",
                    "quantity": "1 whole",
                    "calories": 500,
                    "protein": 30,
                    "carbs": 40,
                    "fats": 20,
                    "confidence": 0.9,
                }
            ],
            "meal_type": "Lunch",
            "synthesis_comment": "A delicious test burger.",
        },
    }

    # 3. Run finalize_log_streaming
    print("Running finalize_log_streaming...")
    async for _event in finalize_log_streaming(state):
        pass  # just consume the generator

    # 4. Verify DB
    print("Verifying database...")
    from sqlalchemy import select

    async with async_session_maker() as session:
        result = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
        updated_log = result.scalar_one()

        print(f"Log Status: {updated_log.status}")
        print(f"Calories: {updated_log.calories} (Expected: 500)")
        print(f"Protein: {updated_log.protein} (Expected: 30)")
        print(f"Carbs: {updated_log.carbs} (Expected: 40)")
        print(f"Fats: {updated_log.fats} (Expected: 20)")
        print(f"Meal Type: {updated_log.meal_type} (Expected: Lunch)")
        print(f"Transcript: {updated_log.transcript} (Expected: None, we didn't test transcript here)")

        if (
            updated_log.protein == 30
            and updated_log.carbs == 40
            and updated_log.fats == 20
            and updated_log.meal_type == "Lunch"
        ):
            print("\nSUCCESS: All fields persisted correctly!")
        else:
            print("\nFAILURE: Fields missing or incorrect.")

        # Cleanup
        print("Cleaning up...")
        await session.delete(updated_log)
        # await session.delete(await session.get(User, user_id)) # Don't delete existing user
        await session.commit()


if __name__ == "__main__":
    asyncio.run(verify_persistence())
