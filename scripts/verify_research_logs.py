import asyncio
import logging
import sys
import os

# Add backend to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

from sqlalchemy import select
from app.database import async_session_maker
from app.models.research import ResearchLog
from app.models.log import DietaryLog
from app.models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_research_logs():
    logger.info("Verifying Research Logs...")
    
    async with async_session_maker() as session:
        # Query ResearchLogs joined with DietaryLog
        query = select(ResearchLog, DietaryLog).join(DietaryLog, ResearchLog.log_id == DietaryLog.id).order_by(ResearchLog.created_at.desc()).limit(10)
        
        result = await session.execute(query)
        rows = result.all()
        
        if not rows:
            logger.warning("No research logs found. Creating a test entry...")
            # Create a test entry if none exist to verify model works
            try:
                # Need a dietary log first
                dietary_log = DietaryLog(
                    image_path="test.jpg",
                    status="logged",
                    user_id=None # Assuming nullable for test or we need a real user. 
                                # Actually user_id is nullable=False in model.
                                # Let's skip creation to avoid constraint errors and just report empty.
                )
                logger.info("Skipping test entry creation (requires valid user and foreign keys). Please use the app to generate a log.")
            except Exception as e:
                logger.error(f"Error: {e}")
        else:
            logger.info(f"Found {len(rows)} research log entries:")
            print("-" * 80)
            print(f"{'Log ID':<36} | {'Modality':<10} | {'Time (ms)':<10} | {'Turns':<5} | {'Corrected':<5} | {'Conf':<5}")
            print("-" * 80)
            
            for research_log, dietary_log in rows:
                print(f"{str(research_log.log_id):<36} | {research_log.input_modality:<10} | {research_log.processing_time_ms:<10} | {research_log.agent_turns_count:<5} | {str(research_log.was_corrected):<9} | {research_log.confidence_score:.2f}")
            print("-" * 80)

if __name__ == "__main__":
    try:
        asyncio.run(verify_research_logs())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Verification failed: {e}")
