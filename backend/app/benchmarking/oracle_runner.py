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


VALID_MODES = {"agentic", "single-shot", "naive-always-ask"}


class OracleRunner:
    def __init__(
        self,
        api_url: str,
        email: str,
        password: str,
        max_turns: int = 3,
        mode: str = "agentic",
        timeout: float = 180.0,
    ):
        if mode not in VALID_MODES:
            raise ValueError(f"Invalid mode '{mode}'. Must be one of: {VALID_MODES}")

        self.api_url = api_url.rstrip("/")
        self.email = email
        self.password = password
        self.max_turns = max_turns
        self.mode = mode

        # Initialize Supabase Client for Auth logic
        self.supabase: Client = create_client(str(settings.SUPABASE_URL), str(settings.SUPABASE_ANON_KEY))
        self.access_token: str | None = None
        self.user_id: str | None = None

        # Async HTTP client for API calls
        self.client = httpx.AsyncClient(base_url=self.api_url, timeout=timeout, verify=False)  # noqa: S501

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
        self,
        dish: NutritionDish,
        system_prompt_override: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        dish_timeout_seconds: float = 120.0,
        clinical_threshold: float = 5.0,
        confidence_threshold: float = 0.85,
        language: str = "en",
    ) -> dict[str, Any]:
        """Orchestrate the benchmarking loop for a single dish.

        Args:
            dish: The dish to benchmark.
            system_prompt_override: Optional prompt override.
            provider: LLM provider.
            model: LLM model name.
            dish_timeout_seconds: Total per-dish timeout (upload + processing).
            clinical_threshold: Complexity threshold for clarification.
            confidence_threshold: Confidence threshold for clarification.
            language: The language for the agent to use.

        Returns:
            Result dict including latency_seconds for timing and complexity metrics.
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

        upload_timeout = min(30.0, dish_timeout_seconds * 0.25)
        try:
            resp = await self.client.post(
                "/api/v1/analysis/upload", json=payload, headers=headers, timeout=upload_timeout
            )
            # Auto-refresh token on 401 and retry once
            if resp.status_code == 401:
                logger.warning(f"[{dish.dish_id}] JWT expired, re-authenticating...")
                await self.login()
                headers = {"Authorization": f"Bearer {self.access_token}"}
                resp = await self.client.post(
                    "/api/v1/analysis/upload", json=payload, headers=headers, timeout=upload_timeout
                )
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

        # 2. SSE Loop with remaining time budget
        remaining_timeout = dish_timeout_seconds - (time.perf_counter() - start_time)
        if remaining_timeout <= 0:
            latency = time.perf_counter() - start_time
            logger.error(f"[{dish.dish_id}] Upload consumed entire timeout budget ({latency:.1f}s)")
            return {
                "dish_id": dish.dish_id,
                "success": False,
                "error": "timeout",
                "log_id": log_id,
                "turns": 0,
                "latency_seconds": latency,
            }
        try:
            result = await asyncio.wait_for(
                self._process_loop(
                    log_id,
                    dish,
                    headers,
                    image_url,
                    system_prompt_override,
                    provider,
                    model,
                    clinical_threshold=clinical_threshold,
                    confidence_threshold=confidence_threshold,
                    language=language,
                ),
                timeout=remaining_timeout,
            )
        except TimeoutError:
            latency = time.perf_counter() - start_time
            logger.error(f"[{dish.dish_id}] Per-dish timeout after {latency:.1f}s")
            return {
                "dish_id": dish.dish_id,
                "success": False,
                "error": "timeout",
                "log_id": log_id,
                "turns": 0,
                "latency_seconds": latency,
            }

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
        provider: str | None = None,
        model: str | None = None,
        clinical_threshold: float = 5.0,
        confidence_threshold: float = 0.85,
        language: str = "en",
    ) -> dict[str, Any]:
        """Reconnection-based SSE processing loop.

        The server terminates the SSE stream after each clarification event.
        This loop handles reconnection: after receiving a clarification, it submits
        the oracle answer, then opens a NEW stream (with log_id) to continue
        the conversation until an agent.response or agent.error is received.
        """
        turns = 0
        final_log = None
        error_msg = None
        clarification_history: list[dict[str, Any]] = []
        complexity_breakdown = None
        complexity_score = None
        semantic_gatekeeper_fired = False
        max_reconnections = 10

        # Build initial stream payload with force flags based on mode
        force_finalize = self.mode == "single-shot"
        force_clarify = self.mode == "naive-always-ask"

        initial_payload = {
            "log_id": log_id,
            "image_path": image_url,
            "audio_path": None,
            "system_prompt_override": system_prompt_override,
            "provider": provider,
            "model": model,
            "force_finalize": force_finalize,
            "force_clarify": force_clarify,
            "clinical_threshold": clinical_threshold,
            "confidence_threshold": confidence_threshold,
            "language": language,
        }

        done = False
        reconnection_count = 0
        is_first_request = True

        try:
            while not done and reconnection_count <= max_reconnections:
                # First iteration: send full payload. Subsequent: continuation with log_id
                if is_first_request:
                    stream_payload = initial_payload
                    is_first_request = False
                else:
                    reconnection_count += 1
                    stream_payload = {
                        "log_id": log_id,
                        "image_path": image_url,
                        "audio_path": None,
                        "system_prompt_override": system_prompt_override,
                        "provider": provider,
                        "model": model,
                        "force_finalize": force_finalize,
                        "force_clarify": force_clarify,
                        "language": language,
                    }

                current_event_type = None

                async with self.client.stream(
                    "POST", "/api/v1/analysis/stream", json=stream_payload, headers=headers
                ) as response:
                    if response.status_code == 401:
                        logger.warning(f"[{dish.dish_id}] JWT expired during stream, re-authenticating...")
                        await self.login()
                        headers["Authorization"] = f"Bearer {self.access_token}"
                        continue  # Retry this stream request with refreshed token
                    if response.status_code != 200:
                        error_msg = f"Stream failed: {response.status_code}"
                        done = True
                        break

                    async for line in response.aiter_lines():
                        if not line.strip() or line.startswith(":"):
                            continue

                        if line.startswith("event:"):
                            current_event_type = line.split(":", 1)[1].strip()
                        elif line.startswith("data:"):
                            data_str = line.split(":", 1)[1].strip()
                            try:
                                event_wrapper = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            event_type = event_wrapper.get("type", current_event_type)
                            data = event_wrapper.get("payload", event_wrapper)

                            if event_type == "agent.clarification":
                                turns += 1

                                # Detect semantic gatekeeper firing in single-shot mode
                                if self.mode == "single-shot":
                                    semantic_gatekeeper_fired = True
                                    logger.warning(
                                        f"[{dish.dish_id}] Semantic gatekeeper fired in "
                                        f"single-shot mode — auto-answering"
                                    )

                                # Extract questions from list (AgentClarification schema)
                                questions_list = data.get("questions", [])
                                if questions_list:
                                    logger.info(
                                        f"[{dish.dish_id}] Clarification {turns}: "
                                        f"{len(questions_list)} question(s)"
                                    )
                                else:
                                    logger.info(f"[{dish.dish_id}] Clarification {turns}: empty")

                                if turns > self.max_turns:
                                    logger.warning(f"[{dish.dish_id}] Max turns reached")
                                    done = True
                                    break

                                # Parse and answer each question individually
                                responses = []
                                for q_item in questions_list:
                                    q_text = q_item.get("question", "")
                                    intent = self._question_parser.parse(q_text)
                                    answer = self._question_parser.lookup_answer(intent, dish)
                                    logger.info(
                                        f"[{dish.dish_id}] Q: {q_text[:50]} → "
                                        f"{intent.question_type.name}: {answer[:50]}..."
                                    )
                                    responses.append({"response": answer, "is_voice": False})
                                    clarification_history.append(
                                        {
                                            "question": q_text,
                                            "item_name": q_item.get("item_name", ""),
                                            "intent": intent.question_type.name,
                                            "entity": intent.entity,
                                            "answer": answer,
                                        }
                                    )

                                # Submit all answers and wait for confirmation
                                await self._submit_answers(log_id, responses, headers)
                                # Stream terminates after clarification — break inner loop
                                # to reconnect via outer loop
                                break

                            elif event_type == "agent.response":
                                final_log = data.get("nutritional_data")
                                status = data.get("status")

                                complexity_breakdown = data.get("complexity_breakdown")
                                if complexity_breakdown and not isinstance(complexity_breakdown, dict):
                                    logger.warning(
                                        f"[{dish.dish_id}] Invalid complexity_breakdown format: "
                                        f"{type(complexity_breakdown)}"
                                    )
                                    complexity_breakdown = None

                                complexity_score = data.get("complexity_score")

                                logger.info(f"[{dish.dish_id}] Final Result: {status}")
                                done = True
                                break

                            elif event_type == "agent.error":
                                error_msg = data.get("message", "Unknown error")
                                logger.error(f"[{dish.dish_id}] Agent Error: {error_msg}")
                                done = True
                                break

            if reconnection_count > max_reconnections:
                error_msg = f"Max reconnections ({max_reconnections}) exceeded"
                logger.error(f"[{dish.dish_id}] {error_msg}")

        except Exception as e:
            logger.error(f"Stream exception for {dish.dish_id}: {e}")
            error_msg = str(e)

        # Log warning for naive-always-ask with 0 turns
        if self.mode == "naive-always-ask" and turns == 0:
            logger.warning(
                f"[{dish.dish_id}] naive-always-ask mode completed with 0 turns "
                f"(likely due to _item_already_asked filtering)"
            )

        success = final_log is not None
        result: dict[str, Any] = {
            "dish_id": dish.dish_id,
            "success": success,
            "turns": turns,
            "final_data": final_log,
            "error": error_msg,
            "log_id": log_id,
            "clarification_history": clarification_history,
            "complexity_breakdown": complexity_breakdown,
            "complexity_score": complexity_score,
        }
        if semantic_gatekeeper_fired:
            result["semantic_gatekeeper_fired"] = True
        return result

    async def _submit_answers(self, log_id: str, responses: list[dict], headers: dict):
        """Submit clarification responses. Raises on failure to prevent silent reconnect loops."""
        url = f"/api/v1/analysis/clarify/{log_id}"
        payload = {"responses": responses}
        resp = await self.client.post(url, json=payload, headers=headers)
        if resp.status_code == 401:
            logger.warning(f"[{log_id}] JWT expired during clarify, re-authenticating...")
            await self.login()
            headers["Authorization"] = f"Bearer {self.access_token}"
            resp = await self.client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        logger.debug(f"Answer submitted for {log_id} ({len(responses)} responses)")
