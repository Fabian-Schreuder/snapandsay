# Story 3.3: Streaming Response Implementation (SSE)

Status: ready-for-dev

## Story

As a user,
I want to see "thinking" indicators while the AI processes,
So that I know the app hasn't frozen and feel engaged with the experience.

## Acceptance Criteria

1.  **Given** The agent is processing a request
    **When** It moves between steps or generates tokens
    **Then** The UI receives Server-Sent Events (SSE)
    **And** The UI displays a "Thinking..." animation or text stream

2.  **Given** The agent is in the `analyze_input` node
    **When** Processing begins
    **Then** An SSE event `agent.thought` is emitted with `{"step": "analyzing", "message": "Looking at your meal..."}`

3.  **Given** The agent transitions between nodes
    **When** Each node completes
    **Then** An SSE event `agent.thought` is emitted describing the transition

4.  **Given** The agent generates a final response
    **When** Processing completes
    **Then** An SSE event `agent.response` is emitted with the final structured data
    **And** The stream closes gracefully

5.  **Given** An error occurs during processing
    **When** The agent encounters an exception
    **Then** An SSE event `agent.error` is emitted with error details
    **And** The stream closes with appropriate error handling

6.  **Given** The frontend establishes an SSE connection
    **When** The connection is active
    **Then** The `use-agent.ts` hook manages the EventSource lifecycle
    **And** Connection cleanup happens on component unmount

7.  **Given** The agent completes processing successfully
    **When** The `agent.response` event is received
    **Then** A satisfying completion sound plays ("Ding")
    **And** Haptic feedback is triggered on supported devices
    **And** The UI transitions to show the logged meal result

## Tasks / Subtasks

- [ ] Backend SSE Infrastructure
    - [ ] **Create `backend/app/schemas/sse.py`**:
        - Define `SSEEvent` Pydantic model with fields: `type` (Literal["agent.thought", "agent.response", "agent.error"]), `payload` (dict)
        - Define `AgentThought` schema: `step` (str), `message` (str), `timestamp` (datetime)
        - Define `AgentResponse` schema: includes `log_id`, `nutritional_data`, `status`
        - Define `AgentError` schema: `code` (str), `message` (str)
    - [ ] **Create `backend/app/services/streaming_service.py`**:
        - Implement `async def format_sse(event: SSEEvent) -> str` helper to format SSE data
        - Follow SSE format: `data: {"type": "...", "payload": {...}}\n\n`

- [ ] LLM Token Streaming (Critical for UX)
    - [ ] **Update `backend/app/services/llm_service.py`**:
        - Modify `analyze_multimodal()` to accept an optional `on_token` callback
        - Use OpenAI streaming mode: `stream=True` with `client.chat.completions.create`
        - Yield partial text chunks as `agent.thought` events during LLM generation
        - Accumulate chunks and parse final structured response
        - This prevents 5-15 second silence during GPT-4o processing

- [ ] Agent Graph Streaming Integration
    - [ ] **Modify `backend/app/agent/graph.py`**:
        - Add a `get_streaming_agent_graph()` function that returns a graph with streaming capabilities
        - Ensure graph uses LangGraph's `astream_events()` or manual event emission
    - [ ] **Update `backend/app/agent/nodes.py`**:
        - Add event emission callbacks/yields at key points in each node
        - `analyze_input`: Emit "Analyzing your meal..." at start, stream LLM tokens during, "Processing complete" at end
        - `generate_clarification`: Emit "Checking if I need more info..." 
        - `finalize_log`: Emit "Saving your meal log..."
    - [ ] **Create `backend/app/agent/constants.py` updates** (define all upfront to avoid piecemeal additions):
        - Add event type constants: `EVENT_THOUGHT = "agent.thought"`, `EVENT_RESPONSE = "agent.response"`, `EVENT_ERROR = "agent.error"`
        - Add thought step constants: `STEP_ANALYZING`, `STEP_CLARIFYING`, `STEP_FINALIZING`

- [ ] SSE API Endpoint
    - [ ] **Create `backend/app/schemas/stream.py`** (NEW):
        - Define `StreamAnalysisRequest`:
          ```python
          class StreamAnalysisRequest(BaseModel):
              log_id: UUID  # From /upload response
              image_path: Optional[str] = None
              audio_path: Optional[str] = None
          ```
    - [ ] **Create `backend/app/api/v1/endpoints/stream.py`** (NEW):
        - Implement `POST /api/v1/analysis/stream` endpoint
        - Accept `StreamAnalysisRequest` (defined above)
        - Return `StreamingResponse` with `media_type="text/event-stream"`
        - Use `async def event_generator()` that:
            1. Initializes agent graph with state from request
            2. Yields SSE events as agent processes (including LLM token streams)
            3. Uses `try/except/finally` for proper cleanup
            4. Emits heartbeat every 15s to keep connection alive
        - Include headers: `Cache-Control: no-cache`, `Connection: keep-alive`
    - [ ] **Update `backend/app/api/v1/api.py`**:
        - Register the new stream router

- [ ] Frontend Hook Implementation
    - [ ] **Create `frontend/hooks/use-agent.ts`** (NEW):
        - Implement `useAgent()` hook using `EventSource` API
        - State: `status` ("idle" | "connecting" | "streaming" | "complete" | "error")
        - State: `thoughts` (array of thought messages for progressive display)
        - State: `result` (final nutritional data)
        - State: `error` (error message if any)
        - Implement `startStreaming(logId: string, imagePath?: string, audioPath?: string)` function
        - Connection Resilience:
            - Heartbeat detection: expect server ping every 15s, reconnect if missed
            - Exponential backoff on failure (1s, 2s, 4s) with max 3 retries
            - Network state detection via `navigator.onLine` events
            - Graceful offline message: "Waiting for connection..."
        - Cleanup: Close EventSource on unmount or completion
        - Events: Listen for `message` event, parse JSON, update state based on `type`
        - Completion: Trigger haptic feedback and play "ding" sound on success

- [ ] UI Integration
    - [ ] **Update `frontend/app/(dashboard)/snap/page.tsx`**:
        - Import and use `useAgent` hook after upload completes
        - Add `ThinkingIndicator` component showing current thought step
        - Implement progressive text display showing agent's thinking process
        - Transition to result display when `agent.response` received
    - [ ] **Create `frontend/components/features/analysis/ThinkingIndicator.tsx`** (NEW):
        - Accept `thoughts: string[]` and `status: string` props
        - **Animation Style** (per UX spec): "Listening pulse" effect - NOT a spinner
            - Gentle organic expansion/contraction animation
            - Optional: Playful food icon (fork/spoon) with subtle bounce
        - **Design for 3-5 second engagement** without causing frustration
        - Show stacked thought messages with smooth fade-in (200ms ease-in-out)
        - Senior-friendly requirements:
            - Text size: 20px minimum (Body Large from UX spec)
            - High contrast: `text-slate-900` on `bg-zinc-50`
            - Toasts stay visible 6 seconds minimum
        - **Completion Feedback**:
            - Visual: Checkmark that "blooms" with satisfaction
            - Audio: Satisfying "Ding" sound (pre-load audio asset)
            - Haptic: `navigator.vibrate(50)` on supported devices

- [ ] Testing
    - [ ] **Create `backend/tests/api/test_stream.py`**:
        - Test SSE endpoint returns proper content-type header
        - Test event format matches specification
        - Test error handling emits `agent.error` event
        - Mock agent graph to test streaming behavior
    - [ ] **Create `backend/tests/services/test_streaming_service.py`**:
        - Test `format_sse` produces valid SSE format
        - Test all event types format correctly
    - [ ] **Create `frontend/__tests__/hooks/use-agent.test.ts`**:
        - Mock EventSource
        - Test state transitions (idle -> connecting -> streaming -> complete)
        - Test error handling and retry logic
        - Test cleanup on unmount
    - [ ] **Create `frontend/__tests__/components/ThinkingIndicator.test.tsx`**:
        - Test renders correctly with different statuses
        - Test accessibility (ARIA labels, announcements)

## Dev Notes

### Architecture Compliance

- **SSE Pattern (from architecture.md)**: 
  - Format: `data: { "type": "event_type", "payload": { ... } }`
  - Event Types: `agent.thought`, `agent.response`, `agent.error`
- **Streaming endpoint should be separate from the upload endpoint** - upload creates the log, stream endpoint processes it
- **Use FastAPI's `StreamingResponse`** with `media_type="text/event-stream"`

### Critical Implementation Details

1. **LangGraph Streaming**: Use `graph.astream_events()` or manually yield events from async generator
2. **Event Ordering**: Events MUST be emitted in order: thought(s) → response OR error
3. **Timeout Handling**: Backend should have a max processing time (e.g., 60s) after which it emits an error
4. **Authentication**: SSE endpoint MUST verify JWT token like other protected endpoints
5. **CORS**: Ensure SSE endpoint allows credentials for authenticated requests

### Senior-Friendly UX Requirements

- **Progressive Feedback**: Show what the AI is "thinking" to maintain engagement
- **Large, Readable Text**: Minimum 20px for thinking messages (Body Large scale)
- **Smooth Animations**: No jarring transitions, gentle pulse/fade effects ("listening pulse" not spinner)
- **Clear Completion**: Visual bloom + "Ding" sound + haptic feedback
- **Engagement Duration**: Design thinking state to hold attention for 3-5 seconds comfortably

### Anti-Patterns to Avoid

- **DO NOT** use WebSockets (SSE is simpler for this unidirectional use case)
- **DO NOT** poll for updates (defeats the purpose of real-time streaming)  
- **DO NOT** use a generic spinner (creates anxiety for seniors - use "listening pulse")
- **DO NOT** emit events too frequently (batch if under 100ms apart to avoid UI thrashing)
- **DO NOT** show technical error messages (use friendly language: "I'm having trouble" not "Error 500")

### Previous Story Intelligence (Story 3.2)

- Agent nodes are async (`async def analyze_input(state)`)
- LLM calls use `llm_service.analyze_multimodal()`
- Graph is compiled via `workflow.compile()`
- Agent state includes: `image_url`, `audio_url`, `messages`, `nutritional_data`
- Node constants defined in `app/agent/constants.py`

### Project Structure Notes

- Backend SSE endpoint: `backend/app/api/v1/endpoints/stream.py` (new file)
- Frontend hook: `frontend/hooks/use-agent.ts` (matches architecture.md specification)
- Analysis components: `frontend/components/features/analysis/` directory (create if needed)

### References

- [Epic 3 Details](file:///home/fabian/dev/work/snapandsay/docs/epics.md#epic-3-agentic-analysis--logging) - FR11 Streaming requirement
- [Architecture: SSE Pattern](file:///home/fabian/dev/work/snapandsay/docs/architecture.md#communication-patterns) - Event format specification
- [Architecture: Frontend Hooks](file:///home/fabian/dev/work/snapandsay/docs/architecture.md#project-organization) - `use-agent.ts` location
- [Previous Story: 3.2](file:///home/fabian/dev/work/snapandsay/docs/sprint-artifacts/3-2-vision-audio-analysis-node.md) - Agent node patterns

### External Resources

- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [LangGraph Streaming](https://langchain-ai.github.io/langgraph/concepts/streaming/)
- [MDN EventSource API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)

## Dev Agent Record

### Context Reference

- `docs/epics.md`
- `docs/architecture.md`
- `docs/sprint-artifacts/3-2-vision-audio-analysis-node.md`
- `backend/app/agent/graph.py`
- `backend/app/agent/nodes.py`
- `backend/app/api/v1/endpoints/analysis.py`

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

- Story created by SM agent with comprehensive context analysis
- All acceptance criteria mapped to specific implementation tasks
- SSE event format aligned with architecture.md specification
- Frontend hook pattern follows existing `use-audio.ts` conventions

### File List

| File | Action | Purpose |
|------|--------|--------|
| `backend/app/schemas/sse.py` | NEW | SSE event type definitions (SSEEvent, AgentThought, etc.) |
| `backend/app/schemas/stream.py` | NEW | StreamAnalysisRequest schema |
| `backend/app/services/streaming_service.py` | NEW | SSE formatting utilities |
| `backend/app/services/llm_service.py` | UPDATE | Add streaming mode with token callback |
| `backend/app/api/v1/endpoints/stream.py` | NEW | SSE streaming endpoint |
| `backend/app/api/v1/api.py` | UPDATE | Register stream router |
| `backend/app/agent/graph.py` | UPDATE | Add streaming graph function |
| `backend/app/agent/nodes.py` | UPDATE | Add event emission in nodes |
| `backend/app/agent/constants.py` | UPDATE | Add event type and step constants |
| `frontend/hooks/use-agent.ts` | NEW | EventSource hook with resilience |
| `frontend/app/(dashboard)/snap/page.tsx` | UPDATE | Integrate useAgent hook and ThinkingIndicator |
| `frontend/components/features/analysis/ThinkingIndicator.tsx` | NEW | "Listening pulse" animation component |
| `frontend/public/sounds/ding.mp3` | NEW | Completion sound asset |
| `backend/tests/api/test_stream.py` | NEW | SSE endpoint tests |
| `backend/tests/services/test_streaming_service.py` | NEW | Streaming service tests |
| `frontend/__tests__/hooks/use-agent.test.ts` | NEW | Hook state and resilience tests |
| `frontend/__tests__/components/ThinkingIndicator.test.tsx` | NEW | Component and a11y tests |
