import asyncio
import json
import logging
import time
from datetime import UTC, datetime
from typing import Any

import httpx
from supabase import Client, create_client

from app.benchmarking.question_parser import QuestionParser
from app.benchmarking.schemas import NutritionDish
from app.config import settings

logger = logging.getLogger(__name__)


class OracleRunner:
    def __init__(self, api_url: str, email: str, password: str, max_turns: int = 3):
        self.api_url = api_url.rstrip("/")
        self.email = email
        self.password = password
        self.max_turns = max_turns

        # Initialize Supabase Client for Auth logic
        self.supabase: Client = create_client(str(settings.SUPABASE_URL), str(settings.SUPABASE_ANON_KEY))
        self.access_token: str | None = None
        self.user_id: str | None = None

        # Async HTTP client for API calls
        self.client = httpx.AsyncClient(base_url=self.api_url, timeout=120.0, verify=False)  # noqa: S501

        # Question parser for targeted Oracle responses
        self._question_parser = QuestionParser()

    async def login(self):
        """Authenticate with Supabase to get JWT."""
        try:
            res = self.supabase.auth.sign_in_with_password({"email": self.email, "password": self.password})
            if res.session:
                self.access_token = res.session.access_token
                self.user_id = res.user.id
                logger.info(f"Logged in as {self.email}")
            else:
                raise Exception("No session returned")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    async def close(self):
        await self.client.aclose()

    async def run_dish(
        self, dish: NutritionDish, system_prompt_override: str | None = None
    ) -> dict[str, Any]:
        """
        Orchestrates the benchmarking loop for a single dish.
        Returns result dict including latency_seconds for timing.
        """
        start_time = time.perf_counter()

        if not self.access_token:
            await self.login()

        headers = {"Authorization": f"Bearer {self.access_token}"}

        # 1. Upload
        logger.info(f"Starting dish {dish.dish_id}")

        # Construct GCS URL for upload (Assuming public access)
        image_url = f"https://storage.googleapis.com/nutrition5k_dataset/nutrition5k_dataset/imagery/realsense_overhead/{dish.dish_id}/rgb.png"

        payload = {"image_path": image_url, "client_timestamp": datetime.now(UTC).isoformat()}

        try:
            resp = await self.client.post("/api/v1/analysis/upload", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            log_id = data["log_id"]
        except Exception as e:
            logger.error(f"Upload failed for {dish.dish_id}: {e}")
            latency = time.perf_counter() - start_time
            return {
                "dish_id": dish.dish_id,
                "success": False,
                "error": f"Upload: {e}",
                "log_id": None,
                "latency_seconds": latency,
            }

        # 2. SSE Loop
        result = await self._process_loop(log_id, dish, headers, image_url, system_prompt_override)

        # Add latency to result
        result["latency_seconds"] = time.perf_counter() - start_time
        return result

    async def _process_loop(
        self,
        log_id: str,
        dish: NutritionDish,
        headers: dict,
        image_url: str,
        system_prompt_override: str | None = None,
    ) -> dict[str, Any]:
        """
        Connects to SSE stream and handles events.
        """
        turns = 0
        final_log = None
        error_msg = None

        stream_payload = {
            "log_id": log_id,
            "image_path": image_url,
            "audio_path": None,
            "system_prompt_override": system_prompt_override,
        }

        # Note: In a real scenario, the stream URL might expect GET for event-stream,
        # but analysis/stream is POST.

        current_event_type = None

        try:
            async with self.client.stream(
                "POST", "/api/v1/analysis/stream", json=stream_payload, headers=headers
            ) as response:
                if response.status_code != 200:
                    return {
                        "dish_id": dish.dish_id,
                        "success": False,
                        "error": f"Stream failed: {response.status_code}",
                        "log_id": log_id,
                    }

                async for line in response.aiter_lines():
                    if not line.strip() or line.startswith(":"):
                        continue

                    if line.startswith("event:"):
                        current_event_type = line.split(":", 1)[1].strip()
                    elif line.startswith("data:"):
                        data_str = line.split(":", 1)[1].strip()
                        try:
                            # Parse the wrapper {type: ..., payload: ...}
                            event_wrapper = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        # Extract type and payload
                        # Backend sends: {"type": "...", "payload": {...}} in data field
                        event_type = event_wrapper.get("type", current_event_type)
                        data = event_wrapper.get("payload", event_wrapper)

                        # Handle Event
                        if event_type == "agent.clarification":
                            turns += 1
                            question = data.get("question", "")
                            logger.info(f"[{dish.dish_id}] Clarification {turns}: {question}")

                            if turns > self.max_turns:
                                logger.warning(f"[{dish.dish_id}] Max turns reached")
                                break

                            # Use QuestionParser for targeted Oracle answer
                            intent = self._question_parser.parse(question)
                            answer = self._question_parser.lookup_answer(intent, dish)
                            logger.info(
                                f"[{dish.dish_id}] Intent: {intent.question_type.name}, "
                                f"Answering: {answer[:50]}..."
                            )

                            # Submit answer asynchronously
                            asyncio.create_task(self._submit_answer(log_id, answer, headers))

                        elif event_type == "agent.response":
                            # Final result
                            final_log = data.get("nutritional_data")
                            status = data.get("status")
                            logger.info(f"[{dish.dish_id}] Final Result: {status}")
                            # We can break here as we got the result
                            break

                        elif event_type == "agent.error":
                            error_msg = data.get("message", "Unknown error")
                            logger.error(f"[{dish.dish_id}] Agent Error: {error_msg}")
                            break

        except Exception as e:
            logger.error(f"Stream exception for {dish.dish_id}: {e}")
            error_msg = str(e)

        success = final_log is not None
        return {
            "dish_id": dish.dish_id,
            "success": success,
            "turns": turns,
            "final_data": final_log,
            "error": error_msg,
            "log_id": log_id,
        }

    async def _submit_answer(self, log_id: str, answer: str, headers: dict):
        """Submit clarification response."""
        url = f"/api/v1/analysis/clarify/{log_id}"
        payload = {"response": answer, "is_voice": False}
        try:
            resp = await self.client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.debug(f"Answer submitted for {log_id}")
        except Exception as e:
            logger.error(f"Failed to submit answer for {log_id}: {e}")
