# Story 3.2: Vision & Audio Analysis Node

Status: ready-for-dev

## Story

As a user,
I want the AI to analyze my photo and voice note,
So that it can identify the food items.

## Acceptance Criteria

1.  **Given** An image and/or audio file are present in the `AgentState`
    **When** The `analyze_input` node executes
    **Then** The audio (if present) is transcribed using Whisper
    **And** The image and transcript are analyzed by GPT-4o
    **And** Structured nutritional data (food items, quantities, confidence) is extracted
    **And** The `AgentState` is updated with this structured data

2.  **Given** An input with only an image (no audio)
    **When** The analysis runs
    **Then** It processes the image only and produces structured data

3.  **Given** An input with only text/audio (no image)
    **When** The analysis runs
    **Then** It acts as a text-only logger

4.  **Given** The LLM analysis completes
    **When** The output is generated
    **Then** It MUST match the defined Pydantic schema for `DietaryLog` (ensuring no hallucinations in structure)

## Tasks / Subtasks

- [ ] Core Services Customization
    - [ ] Update `backend/requirements.txt`:
        - Add `openai>=1.0.0` (for GPT-4o and Whisper API)
    - [ ] Update `backend/app/core/config.py`:
        - Add `OPENAI_API_KEY` setting.
        - Add `OPENAI_MODEL_NAME` (default: "gpt-4o") and `WHISPER_MODEL_NAME` (default: "whisper-1") for configurability.
    - [ ] Create `backend/app/schemas/analysis.py`:
        - Define `FoodItem` (name, quantity, calories, confidence).
        - Define `AnalysisResult` (items: List[FoodItem], synthesis_comment).

- [ ] Voice Service Implementation
    - [ ] Create `backend/app/services/voice_service.py`.
    - [ ] Implement `transcribe_audio(file_path: str) -> str`:
        - Use OpenAI `client.audio.transcriptions.create` (model=settings.WHISPER_MODEL_NAME).
        - Handle temp file management if needed (or streaming upload).

- [ ] LLM Service Implementation
    - [ ] Create `backend/app/services/llm_service.py`.
    - [ ] Implement `analyze_multimodal(image_url: str | None, transcript: str | None) -> AnalysisResult`:
        - Construct User Message with Image (base64 or URL) and Transcript.
        - System Prompt: Act as a dietary expert. **Inject current time** to assist with meal type inference (e.g., 8 AM -> Breakfast).
        - Use `client.beta.chat.completions.parse` (Structured Outputs) with `response_format=AnalysisResult` and `model=settings.OPENAI_MODEL_NAME`.
        - **Error Handling**: Wrap API calls in try/catch blocks. Raise custom `LLMGenerationError` on failure (rate limits, context errors) to allow graceful degradation.

- [ ] Agent Node Implementation
    - [ ] **Update `AgentState`**:
        - Modify `backend/app/agent/state.py` to add `audio_url: Optional[str]`. This ensures strict typing for voice inputs.
    - [ ] Modify `backend/app/agent/nodes.py`:
        - Implement `analyze_input(state: AgentState) -> dict`.
        - Logic:
            - Check `state["messages"]` or `state["image_url"]`.
            - Check `state.get("audio_url")`.
            - Call `voice_service.transcribe` if audio exists.
            - Call `llm_service.analyze_multimodal` with image and transcript.
            - Return `{"nutritional_data": result.model_dump()}`.

- [ ] Testing
    - [ ] Create `backend/tests/services/test_voice_service.py` (Mock OpenAI).
    - [ ] Create `backend/tests/services/test_llm_service.py` (Mock OpenAI).
    - [ ] Create `backend/tests/agent/test_nodes.py` (Test `analyze_input` logic).

## Dev Notes

- **Agent State**: `AgentState` must be updated to include `audio_url` as correctly identified during validation.
- **Pure Nodes**: Keep `nodes.py` clean. All heavy logic (API calls) goes into `services/`.
- **Structured Outputs**: Use OpenAI's new `parse` method for reliability. Do NOT rely on prompt engineering alone for JSON.
- **Async**: All service calls should be async (or run in threadpool if sync client used). Prefer `AsyncOpenAI` client.

### Project Structure Notes

- `backend/app/services/` is the correct place for external integrations.
- `backend/app/schemas/` is for Pydantic models.

### References

- [Epic 3 Details](docs/epics.md#epic-3-agentic-analysis--logging)
- [Architecture: Agent Layer](docs/architecture.md#requirements-to-structure-mapping)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)

## Dev Agent Record

### Context Reference

- `docs/epics.md`
- `docs/architecture.md`
- `docs/sprint-artifacts/3-1-langgraph-agent-setup.md`

### Agent Model Used

- **Model**: Gemini 2.0 Flash (Antigravity)
- **Role**: Technical Scrum Master (Bob)

### Completion Notes List

- Validated against Story 3.1 implementation.
- Added dependency on OpenAI API.
- Enforced Service-Repository pattern (logic in services).
- **Critical**: Identified potential missing field `audio_url` in `AgentState`. Scheduled task to check/add it.

### File List

- backend/requirements.txt
- backend/app/core/config.py
- backend/app/schemas/analysis.py
- backend/app/services/voice_service.py
- backend/app/services/llm_service.py
- backend/app/agent/nodes.py
- backend/app/agent/state.py
- backend/tests/services/test_voice_service.py
- backend/tests/services/test_llm_service.py
- backend/tests/agent/test_nodes.py
