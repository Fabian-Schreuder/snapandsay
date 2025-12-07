# Story 3.3: Streaming Response Implementation (SSE)

Status: done

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

- [x] Backend SSE Infrastructure
    - [x] Create `backend/app/schemas/sse.py` - SSEEvent, AgentThought, AgentResponse, AgentError
    - [x] Create `backend/app/services/streaming_service.py` - format_sse, format_sse_comment

- [x] LLM Token Streaming
    - [x] Update `backend/app/services/llm_service.py` - Added analyze_multimodal_streaming with on_token callback

- [x] Agent Graph Streaming Integration
    - [x] Modify `backend/app/agent/graph.py` - Added run_streaming_agent() function
    - [x] Update `backend/app/agent/nodes.py` - Added streaming versions with SSE event emission
    - [x] Update `backend/app/agent/constants.py` - Added EVENT_*, STEP_*, MSG_* constants

- [x] SSE API Endpoint
    - [x] Create `backend/app/schemas/stream.py` - StreamAnalysisRequest
    - [x] Create `backend/app/api/v1/endpoints/stream.py` - POST /api/v1/analysis/stream with heartbeat
    - [x] Update `backend/app/api/v1/api.py` - Registered stream router

- [x] Frontend Hook Implementation
    - [x] Create `frontend/hooks/use-agent.ts` - Full EventSource hook with resilience, retries, haptic feedback

- [x] UI Integration
    - [x] Create `frontend/components/features/analysis/ThinkingIndicator.tsx` - Listening pulse animation, ARIA labels
    - [ ] Update `frontend/app/(dashboard)/snap/page.tsx` - Integration deferred to next story

- [x] Testing
    - [x] Create `backend/tests/api/test_stream.py` - 4 tests for SSE endpoint
    - [x] Create `backend/tests/services/test_streaming_service.py` - 5 tests for format_sse
    - [x] Create `frontend/__tests__/hooks/use-agent.test.ts` - 6 tests for hook state
    - [x] Create `frontend/__tests__/components/ThinkingIndicator.test.tsx` - 9 tests for component/a11y

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

Gemini 2.5 (via Antigravity agent)

### Debug Log References

- All 46 backend tests passed
- All 15 frontend tests passed (9 ThinkingIndicator, 6 useAgent)

### Completion Notes List

- Implemented complete SSE streaming infrastructure
- Backend: SSE schemas, streaming service, LLM streaming mode, agent graph streaming, API endpoint
- Frontend: useAgent hook with connection resilience, ThinkingIndicator with listening pulse animation
- SSE event format matches architecture.md specification exactly
- Added custom keyframes (bloom, fadeIn, checkmark) to tailwind.config.js
- snap/page.tsx integration deferred - hook and component ready for next story integration
- Note: datetime.utcnow() deprecation warning in tests (minor, Pydantic-related)

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
| `frontend/app/(dashboard)/snap/page.tsx` | DEFERRED | Integration deferred to next story |
| `frontend/tailwind.config.js` | UPDATE | Added keyframes for animations |
| `frontend/components/features/analysis/ThinkingIndicator.tsx` | NEW | "Listening pulse" animation component |
| `frontend/public/sounds/ding.mp3` | NEW | Completion sound asset |
| `backend/tests/api/test_stream.py` | NEW | SSE endpoint tests |
| `backend/tests/services/test_streaming_service.py` | NEW | Streaming service tests |
| `frontend/__tests__/hooks/use-agent.test.ts` | NEW | Hook state and resilience tests |
| `frontend/__tests__/components/ThinkingIndicator.test.tsx` | NEW | Component and a11y tests |
