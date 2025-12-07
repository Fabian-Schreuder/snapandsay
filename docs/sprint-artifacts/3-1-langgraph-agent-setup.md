# Story 3.1: LangGraph Agent Setup

Status: Done

## Story

As a developer,
I want to initialize the LangGraph orchestration layer,
So that we can manage the complex reasoning loop of the AI.

## Acceptance Criteria

1.  **Given** The backend application is starting
    **When** The `app.agent` module is loaded
    **Then** The `AgentState` TypedDict is defined with strict typing
    **And** The state includes `messages` (Annotated[list[BaseMessage], add_messages]), `image_url` (Optional[str]), and `nutritional_data` (Optional[dict])

2.  **Given** The LangGraph `StateGraph` is initialized
    **When** The nodes are added
    **Then** Empty placeholder nodes are created for `analyze_input`, `generate_clarification`, and `finalize_log`
    **And** Each node function signature accepts `AgentState` and returns a partial state update (async def)

3.  **Given** The graph structure is defined
    **When** The edges are configured
    **Then** The graph compiles successfully using `graph.compile()`
    **And** The resulting runnable can be invoked/streamed

4.  **Given** The application requires async execution
    **When** The nodes are implemented
    **Then** All node functions must be `async def` to support non-blocking I/O (Database, LLM calls)

## Tasks / Subtasks

- [x] Agent Foundation
    - [x] Update `backend/requirements.txt`:
        - Add `langgraph>=0.1.5`
        - Add `langchain-core`
    - [x] Create `backend/app/agent/state.py` defining `AgentState` (TypedDict).
        - Use `langchain_core.messages.BaseMessage` for the messages list.
        - Use `langgraph.graph.message.add_messages` for the reducer.
    - [x] Create `backend/app/agent/nodes.py` with async placeholder functions.
        - `async def analyze_input(state: AgentState)`
        - `async def generate_clarification(state: AgentState)`
        - `async def finalize_log(state: AgentState)`
    - [x] Create `backend/app/agent/graph.py`.
        - Initialize `StateGraph(AgentState)`.
        - Add nodes and edges (Start -> analyze_input).
        - Compile logic in a singleton or factory function `get_agent_graph()`.

- [x] Integration Verification
    - [x] Create a unit test `backend/tests/agent/test_graph.py` to verify graph compilation and structure.
    - [x] Verify state validation works as expected.

## Dev Notes

- **LangGraph Version**: Ensure compatibility with `langgraph>=0.1.5`. Use `StateGraph` and `END`/`START` constants from `langgraph.graph`.
- **State Management**: The `AgentState` is the single source of truth for the request lifecycle. Avoid side effects outside of state updates where possible.
- **Asyncio**: Python backend is fully async. Do not use blocking calls.
- **Project Structure**:
    - `backend/app/agent/` directory is the home for all agent logic.
    - Keep nodes pure-ish (business logic should ideally reside in `services/` and be called by nodes).

### Project Structure Notes

- **Alignment**: Standard `backend/app` structure.
- **New Directory**: `backend/app/agent/` needs to be created.

### References

- [Epics: Story 3.1](docs/epics.md#story-31-langgraph-agent-setup)
- [Architecture: Agent Layer](docs/architecture.md#requirements-to-structure-mapping)
- [LangGraph Docs](https://python.langchain.com/docs/langgraph)

## Dev Agent Record

### Context Reference

- `docs/epics.md`
- `docs/architecture.md`
- `docs/sprint-artifacts/2-3-combined-capture-upload-service.md`
- `docs/project_context.md`

### Agent Model Used

- **Model**: Gemini 2.0 Flash (Antigravity)
- **Role**: Technical Scrum Master (Bob)

### Completion Notes List

- Implemented `AgentState` in `backend/app/agent/state.py` with required fields.
- Implemented placeholder nodes in `backend/app/agent/nodes.py`.
- Implemented `get_agent_graph` in `backend/app/agent/graph.py` with initial Start -> analyze_input -> End flow.
- Added dependencies: `langgraph`, `langchain-core` to `backend/pyproject.toml` and updated `backend/requirements.txt`.
- Added unit tests in `backend/tests/agent/test_graph.py` verifying graph compilation and basic structure.
- **Review (Auto-Fix)**: Added `backend/app/agent/constants.py` and registered all nodes in graph to avoid dead code.

### File List

- backend/app/agent/state.py
- backend/app/agent/nodes.py
- backend/app/agent/graph.py
- backend/app/agent/__init__.py
- backend/tests/agent/test_graph.py
- backend/requirements.txt
- backend/pyproject.toml
- backend/app/agent/constants.py
