# Story 3.4: Clarification Logic (Probabilistic Silence)

Status: ready-for-dev

## Story

As a user,
I want the AI to only ask me questions when it's unsure,
So that I'm not annoyed by obvious questions and can log meals faster.

## Acceptance Criteria

1.  **Given** The AI has analyzed the input and the overall confidence score is ≥ 0.85
    **When** The agent routes after `analyze_input`
    **Then** It automatically proceeds to `finalize_log` (Silence)
    **And** No clarification question is shown to the user

2.  **Given** The AI has analyzed the input and the overall confidence score is < 0.85
    **When** The agent routes after `analyze_input`
    **Then** It proceeds to `generate_clarification`
    **And** A clarification question is generated (e.g., "What kind of dressing was on your salad?")

3.  **Given** The agent is generating a clarification question
    **When** The question is ready
    **Then** An SSE event `agent.clarification` is emitted with the question text
    **And** The UI displays the question in the "Listening" state

4.  **Given** The user responds to a clarification question (text or voice)
    **When** The response is submitted
    **Then** The agent processes the response
    **And** Re-evaluates confidence before routing again

5.  **Given** The user provides a clarification response
    **When** The new overall confidence is ≥ 0.85
    **Then** The agent proceeds to `finalize_log`
    **And** The log is saved with the updated information

6.  **Given** The confidence remains low after clarification
    **When** The maximum clarification attempts (2) are reached
    **Then** The agent proceeds to `finalize_log` with best-effort data
    **And** The log is flagged with `needs_review: true`

7.  **Given** The `finalize_log` node completes
    **When** Saving the dietary log
    **Then** The `DietaryLog` record is updated with `status: "logged"`
    **And** The nutritional data is persisted to the database

## Tasks / Subtasks

- [ ] **Task 1: Extend AgentState and Database Schema** (AC: #1, #2, #6, #7)
    - [ ] Update `backend/app/agent/state.py` - Add `log_id: Optional[UUID]`, `overall_confidence: float`, `clarification_count: int`, `needs_clarification: bool`, `needs_review: bool` fields
    - [ ] Update `backend/app/schemas/analysis.py` - Add `overall_confidence: float` field to `AnalysisResult` computed from item confidences
    - [ ] Update `backend/app/models/log.py` - Add `needs_review = Column(Boolean, default=False)` column
    - [ ] Create `supabase/migrations/XXXX_add_needs_review.sql` - Add `needs_review` boolean column to `dietary_logs` table

- [ ] **Task 2: Implement Confidence Routing Function** (AC: #1, #2)
    - [ ] Create `backend/app/agent/routing.py` - Implement `route_by_confidence(state: AgentState) -> str` function
    - [ ] Function returns `FINALIZE_LOG` if overall_confidence ≥ 0.85, else `GENERATE_CLARIFICATION`

- [ ] **Task 3: Update Agent Graph with Conditional Edge** (AC: #1, #2)
    - [ ] Modify `backend/app/agent/graph.py` - Replace `add_edge(ANALYZE_INPUT, GENERATE_CLARIFICATION)` with `add_conditional_edges(ANALYZE_INPUT, route_by_confidence, {GENERATE_CLARIFICATION: GENERATE_CLARIFICATION, FINALIZE_LOG: FINALIZE_LOG})`
    - [ ] Update `run_streaming_agent()` to use conditional routing logic instead of sequential execution
    - [ ] Add unit test for conditional edge routing

- [ ] **Task 4: Implement Clarification Generation** (AC: #3)
    - [ ] Modify `backend/app/agent/nodes.py` - Implement real logic in `generate_clarification()` and `generate_clarification_streaming()`
    - [ ] Create LLM prompt to generate contextual clarification questions with suggested options based on low-confidence items
    - [ ] Update `backend/app/agent/constants.py` - Add `EVENT_CLARIFICATION = "agent.clarification"`, `CLARIFICATION_TIMEOUT_SECONDS = 30` and related constants
    - [ ] Update `backend/app/schemas/sse.py` - Add `AgentClarification` schema with `question: str`, `options: List[str]`, `context: dict` fields
    - [ ] Update `DietaryLog.status` to `"clarification"` when entering clarification state

- [ ] **Task 5: Implement Clarification Response Handling** (AC: #4, #5)
    - [ ] Create `POST /api/v1/analysis/clarify/{log_id}` endpoint in `backend/app/api/v1/endpoints/analysis.py`
        - Request body: `ClarifyRequest { response: str, is_voice: bool }`
        - If `is_voice=true`, transcribe audio using `voice_service.transcribe_audio()`
        - Triggers agent re-analysis with updated context
    - [ ] Create `backend/app/agent/nodes.py` - Add `process_clarification_response()` node
    - [ ] Update agent state with clarification response and re-analyze
    - [ ] Implement loop from clarification back through routing

- [ ] **Task 6: Implement Max Clarification Guard** (AC: #6)
    - [ ] Update routing function to check `clarification_count >= 2`
    - [ ] If max reached, route to `finalize_log` regardless of confidence
    - [ ] Set `needs_review: true` in state when best-effort finalization occurs

- [ ] **Task 7: Implement Finalize Log Persistence** (AC: #7)
    - [ ] Modify `backend/app/agent/nodes.py` - Implement real logic in `finalize_log()` and `finalize_log_streaming()`
    - [ ] Update `DietaryLog` record in database with nutritional data and `status: "logged"`
    - [ ] Handle `needs_review` flag persistence

- [ ] **Task 8: Update Frontend for Clarification Flow** (AC: #3, #4)
    - [ ] Update `frontend/hooks/use-agent.ts` - Add handler for `agent.clarification` event type, implement 30-second timeout
    - [ ] Create `frontend/components/features/analysis/ClarificationPrompt.tsx`:
        - Display question with large, readable text (20px+ per UX spec)
        - Render `options` as large tap targets for quick selection
        - Integrate `useAudio` hook for voice response option (hold-to-record pattern)
        - Text input fallback with 60px height
        - 30-second timeout with friendly "Taking too long? Tap to skip" message
    - [ ] Update `frontend/app/(dashboard)/snap/page.tsx` - Integrate clarification UI state, handle timeout event

- [ ] **Task 9: Testing**
    - [ ] Create `backend/tests/agent/test_routing.py` - 5+ tests for routing logic (high/low confidence, max attempts)
    - [ ] Update `backend/tests/agent/test_graph.py` - Tests for conditional edge behavior
    - [ ] Update `backend/tests/agent/test_nodes.py` - Tests for clarification and finalize nodes
    - [ ] Create `frontend/__tests__/components/ClarificationPrompt.test.tsx` - UI and accessibility tests
    - [ ] Update `frontend/__tests__/hooks/use-agent.test.ts` - Clarification event handling tests

## Dev Notes

### Architecture Compliance

- **Conditional Edge Pattern**: Use LangGraph's `add_conditional_edges()` for confidence-based routing
- **SSE Events (from architecture.md)**:
  - Add new event: `agent.clarification` for prompt display
  - Format: `data: { "type": "agent.clarification", "payload": { "question": "...", "context": {...} } }`
- **Confidence Threshold**: 0.85 is specified in PRD/Epics - do NOT change without stakeholder approval
- **Service Layer**: Database updates go through services, not directly in nodes

### Critical Implementation Details

1. **Overall Confidence Calculation**: Compute as simple average of item confidences (weighted by portion optional for future optimization):
   ```python
   # Simple average (required)
   overall_confidence = sum(item.confidence for item in items) / len(items) if items else 0.0
   
   # Optional: Weighted by estimated grams (future optimization)
   # total_weight = sum(parse_quantity_grams(item.quantity) for item in items)
   # overall_confidence = sum(item.confidence * parse_quantity_grams(item.quantity) for item in items) / total_weight
   ```

2. **Conditional Edge Pattern**:
   ```python
   from langgraph.graph import END
   
   def route_by_confidence(state: AgentState) -> str:
       if state.get("clarification_count", 0) >= MAX_CLARIFICATIONS:
           return FINALIZE_LOG
       if state.get("overall_confidence", 0.0) >= CONFIDENCE_THRESHOLD:
           return FINALIZE_LOG
       return GENERATE_CLARIFICATION
   
   workflow.add_conditional_edges(
       ANALYZE_INPUT,
       route_by_confidence,
       {
           GENERATE_CLARIFICATION: GENERATE_CLARIFICATION,
           FINALIZE_LOG: FINALIZE_LOG,
       }
   )
   ```

3. **Constants to Add**:
   ```python
   CONFIDENCE_THRESHOLD = 0.85
   MAX_CLARIFICATIONS = 2
   EVENT_CLARIFICATION = "agent.clarification"
   CLARIFICATION_TIMEOUT_SECONDS = 30
   ```

4. **AgentClarification Schema**:
   ```python
   class AgentClarification(BaseModel):
       question: str  # e.g., "What kind of dressing?"
       options: List[str] = []  # e.g., ["Ranch", "Italian", "Vinaigrette"]
       context: dict = {}  # Low-confidence item details
       log_id: UUID  # For response endpoint
   ```

5. **Clarification Question Generation**: Use GPT-4o with a prompt like:
   > "Based on the following food items with low confidence, generate a single, friendly clarification question for a senior user. Include 2-3 common options as suggestions. Target 6th grade reading level."

6. **Streaming Graph Update**: The `run_streaming_agent()` function needs to check routing condition and branch execution accordingly.

7. **Status Transitions**: DietaryLog status flow: `processing` → `clarification` (if asking) → `logged` (or `logged` with `needs_review=true`)

### Anti-Patterns to Avoid

- **DO NOT** hardcode the confidence threshold in multiple places (use constant from `constants.py`)
- **DO NOT** ask more than 2 clarification questions (max attempts guard)
- **DO NOT** use complex language in clarification questions (target reading level: 6th grade)
- **DO NOT** persist logs with `status: "processing"` - ensure state is `logged` or `needs_review`
- **DO NOT** block the UI during clarification - maintain async/streaming pattern

### Previous Story Intelligence (Story 3.3)

- **SSE Infrastructure Complete**: `SSEEvent`, `AgentThought`, `AgentResponse`, `AgentError` schemas exist
- **Streaming Service**: `format_sse()` utility in `streaming_service.py`
- **Frontend Hook**: `use-agent.ts` manages EventSource with resilience patterns
- **UI Component**: `ThinkingIndicator.tsx` ready for use
- **Event Constants**: `EVENT_THOUGHT`, `EVENT_RESPONSE`, `EVENT_ERROR` defined
- **snap/page.tsx integration was deferred** - needs full integration in this story

### Git Intelligence (Recent Commits)

1. `2389b70` - SSE streaming implementation complete with frontend hook
2. `e93dc06` - LLM and voice services with OpenAI integration
3. `076c9d1` - LangGraph agent foundation with state and nodes

Key patterns from commits:
- Nodes yield `SSEEvent` objects then state update dicts
- Constants centralized in `constants.py`
- Async generator pattern for streaming nodes

### Project Structure Notes

- **New Files**:
  - `backend/app/agent/routing.py` - Routing logic
  - `frontend/components/features/analysis/ClarificationPrompt.tsx` - Clarification UI with voice input
  - `supabase/migrations/XXXX_add_needs_review.sql` - Database migration

- **Modified Files**:
  - `backend/app/agent/state.py` - Extended state with `log_id`
  - `backend/app/agent/graph.py` - Conditional edges
  - `backend/app/agent/nodes.py` - Clarification and finalize logic
  - `backend/app/agent/constants.py` - New constants including timeout
  - `backend/app/schemas/sse.py` - AgentClarification schema with options
  - `backend/app/schemas/analysis.py` - overall_confidence field
  - `backend/app/models/log.py` - Add needs_review column
  - `backend/app/api/v1/endpoints/analysis.py` - Add clarify endpoint
  - `frontend/hooks/use-agent.ts` - Clarification event handler with timeout
  - `frontend/app/(dashboard)/snap/page.tsx` - Full integration

### Senior-Friendly UX Requirements

- **Clarification Questions**: Simple, direct language (e.g., "What type of dressing?" not "Could you specify the condiment variety?")
- **One Question at a Time**: Never batch multiple questions
- **Voice Response Option**: Allow voice OR text response for clarification
- **Patient Timing**: Allow 30+ seconds for response before timeout
- **Helpful Defaults**: Suggest common answers (e.g., "Ranch, Italian, or something else?")

### References

- [Epic 3 Details: Story 3.4](file:///home/fabian/dev/work/snapandsay/docs/epics.md#story-34-clarification-logic-probabilistic-silence) - Confidence threshold requirements
- [Architecture: SSE Pattern](file:///home/fabian/dev/work/snapandsay/docs/architecture.md#communication-patterns) - Event format specification
- [Architecture: Agent Layer](file:///home/fabian/dev/work/snapandsay/docs/architecture.md#project-structure) - Agent file locations
- [Previous Story: 3.3](file:///home/fabian/dev/work/snapandsay/docs/sprint-artifacts/3-3-streaming-response-implementation-sse.md) - SSE infrastructure
- [Project Context](file:///home/fabian/dev/work/snapandsay/docs/project_context.md) - Testing and coding standards

### External Resources

- [LangGraph Conditional Edges](https://langchain-ai.github.io/langgraph/concepts/low_level/#conditional-edges)
- [LangGraph Human-in-the-Loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)

## Dev Agent Record

### Context Reference

- `docs/epics.md`
- `docs/architecture.md`
- `docs/project_context.md`
- `docs/sprint-artifacts/3-3-streaming-response-implementation-sse.md`
- `backend/app/agent/graph.py`
- `backend/app/agent/nodes.py`
- `backend/app/agent/state.py`
- `backend/app/agent/constants.py`
- `backend/app/schemas/analysis.py`

### Agent Model Used

Gemini 2.5 (via Antigravity agent)

### Debug Log References

### Completion Notes List

### File List
