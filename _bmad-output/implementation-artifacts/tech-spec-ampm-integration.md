---
title: 'Automated Multi-Pass Method (AMPM) Integration'
slug: 'ampm-integration'
created: '2026-02-15'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python', 'LangGraph', 'Pydantic']
files_to_modify: ['backend/app/agent/graph.py', 'backend/app/agent/state.py', 'backend/app/agent/constants.py', 'backend/app/agent/ampm_graph.py', 'backend/app/agent/ampm_nodes.py', 'backend/app/agent/routing.py', 'backend/app/agent/nodes.py']
code_patterns: ['StateGraph', 'TypedDict', 'Conditional Routing', 'SSE Streaming']
test_patterns: ['pytest', 'manual verification', 'integration tests']
---

# Tech-Spec: Automated Multi-Pass Method (AMPM) Integration

**Created:** 2026-02-15

## Overview

### Problem Statement

Single-pass analysis misses details (preparation, portion, brand) on complex meals, reducing nutritional accuracy.

### Solution

Implement an **Adaptive 3-Pass AMPM (Automated Multi-Pass Method)** using a LangGraph Subgraph. This approach conditionally triggers a multi-turn detail cycle only for low-confidence items, ensuring high fidelity for complex logs while keeping the happy path fast for simple ones.

### Scope

**In Scope:**
*   **Architecture:** Adaptive 3-Pass Strategy (Quick Scan -> Detail Cycle Subgraph -> Final Probe).
*   **New Components:** `AMPMState`, `ampm_graph.py` (Subgraph definition), `ampm_nodes.py` (AMPM node implementations).
*   **Refactoring:** Update main `graph.py` (both compiled graph AND `run_streaming_agent()`) to route to the AMPM Subgraph instead of the simple `generate_clarification` node.
*   **Logic:** Implement "Detail Cycle" logic (identify gaps -> ask clarification -> update state) and "Final Probe" (conditional forgotten foods check).

**Out of Scope:**
*   UI changes (uses existing chat interface).
*   Changes to the initial `analyze_input` node prompts (focus is on the workflow structure).

## Context for Development

### Codebase Patterns

*   **Agent Architecture**: `StateGraph` in `backend/app/agent/graph.py` defines the workflow.
*   **Dual Execution Paths**: The codebase has TWO parallel paths: `get_agent_graph()` (compiled LangGraph) and `run_streaming_agent()` (manual streaming orchestration). **Both must be updated.** ⚠️ Cross-reference both locations with comments linking to the other. Long-term: consider migrating to LangGraph's `astream_events()` to eliminate this dual path.
*   **State Management**: `AgentState` in `backend/app/agent/state.py` is a `TypedDict` tracking the conversation and analysis data.
*   **Schemas**: Pydantic models in `backend/app/schemas/` enforce data structure (e.g., `DietaryLogResponse` in `log.py`).
*   **Constants**: Node names and messages are centralized in `backend/app/agent/constants.py`.
*   **Localization**: All user-facing strings in `constants.py` are bilingual (EN/NL) via the `MESSAGES` dict and `get_message()` helper.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `backend/app/agent/graph.py` | Main agent workflow. Contains BOTH `get_agent_graph()` and `run_streaming_agent()`. Both need refactoring. |
| `backend/app/agent/state.py` | `AgentState` definition. Needs extension for AMPM tracking. |
| `backend/app/agent/constants.py` | Centralized constants. Needs new node names, event types, and bilingual messages. |
| `backend/app/agent/routing.py` | Routing logic (`route_by_confidence`, `MAX_CLARIFICATIONS` guard). Needs update to route to AMPM subgraph. |
| `backend/app/agent/nodes.py` | Existing node implementations (528 lines). Reference for streaming patterns. |
| `backend/app/schemas/log.py` | Log schemas. May need updates if AMPM introduces new temporary fields. |

### Technical Decisions

*   **Subgraph Architecture:** Chosen to isolate AMPM state and logic from the main graph, keeping the core workflow clean.
*   **Subgraph State Handoff (Expert Panel):** The AMPM subgraph receives a *projected subset* of `AgentState`: `messages`, `nutritional_data`, `overall_confidence`, `clarification_count`, `ampm_data`, `complexity_score`, `language`. On exit, the subgraph writes back: `nutritional_data`, `clarification_count`, `ampm_data`, `needs_clarification`, `needs_review`. This must be explicitly defined in the subgraph input/output mapping.
*   **Adaptive Routing:** High confidence logs skip AMPM entirely to minimize user friction.
*   **State Separation:** `AMPMState` will track pass-specific data separate from the main `AgentState`.
*   **Dedicated AMPM Nodes File:** All AMPM-specific node implementations go in `backend/app/agent/ampm_nodes.py` (not mixed into existing `nodes.py`).
*   **`complexity_score` Derivation (Expert Panel):** Computed by the LLM during `analyze_input` as part of its structured output — NOT via a hardcoded formula. The LLM is asked to rate meal complexity on a 0.0–1.0 scale considering: number of items, composite dishes, ambiguous portions, mixed preparations. This leverages the LLM's contextual understanding (e.g., "pad thai" is inherently complex even as a single item).
*   **`ampm_data` Schema:** Typed as `AMPMPassData` (TypedDict), NOT a raw `dict`. Fields: `low_confidence_items: list[str]`, `questions_asked: list[str]`, `responses: list[str]`, `pass_count: int`.
*   **MAX_CLARIFICATIONS in AMPM Context:** The existing `MAX_CLARIFICATIONS` (2) applies as a *total budget across the entire AMPM subgraph*. If the Detail Cycle exhausts it, the subgraph exits to `finalize_log` with `needs_review=True`.
*   **Question Prioritization (Expert Panel):** The Detail Cycle must ask questions ordered by *nutritional variance impact*, not just lowest confidence. E.g., "Was the chicken fried or grilled?" (large calorie difference) is more impactful than "Was the lettuce romaine or iceberg?" (negligible difference). The LLM prompt for question generation should include this prioritization directive.
*   **Non-Answer Handling (Expert Panel):** Accept "I don't know" / "not sure" as valid responses. Log the non-answer, keep the current best estimate, and move on. Do NOT re-ask the same question.
*   **Conditional Final Probe (Shark Tank Refinement):** Do not blindly ask "Anything else?". Only trigger if:
    -   `complexity_score` > 0.7 (meal is inherently complex).
    -   Detail Cycle was inconclusive (items still below threshold after cycle).
*   **Final Probe Exact Wording (Expert Panel):** Must be: "Did you have anything else **with that**?" (not "anything else?" alone — the "with that" anchors it to the current meal and avoids confusion with a new meal). Localized: "Had je er nog iets anders **bij**?"

### Non-Functional Requirements (Shark Tank Refinement)

*   **Latency Budget**: The decision to enter/exit AMPM must incur < 2s overhead. Minimize round trips where possible.

## Implementation Plan

### Tasks

- [ ] Task 1: Update Constants, State, and Schemas
  - File: `backend/app/agent/constants.py`
  - Action:
    - Add node name constants: `AMPM_ENTRY = "ampm_entry"`, `DETAIL_CYCLE = "detail_cycle"`, `FINAL_PROBE = "final_probe"`.
    - Add SSE event types: `EVENT_DETAIL_CYCLE = "agent.detail_cycle"`, `EVENT_FINAL_PROBE = "agent.final_probe"`.
    - Add bilingual messages to `MESSAGES` dict:
      - `"detail_cycle_start"`: EN: "Let me ask about some details..." / NL: "Laat me wat details vragen..."
      - `"final_probe"`: EN: "Did you have anything else with that?" / NL: "Had je er nog iets anders bij?"
      - `"detail_cycle_question"`: EN: "About your {item}..." / NL: "Over je {item}..."
  - File: `backend/app/agent/state.py`
  - Action:
    - Add `AMPMPassData` TypedDict: `low_confidence_items: list[str]`, `questions_asked: list[str]`, `responses: list[str]`, `pass_count: int`.
    - Extend `AgentState` with: `ampm_data: AMPMPassData | None`, `current_pass: str | None`, `complexity_score: float`.

- [ ] Task 2: Create AMPM Subgraph Definition
  - File: `backend/app/agent/ampm_graph.py` [NEW]
  - Action:
    - Import `StateGraph`, `AgentState`, AMPM constants.
    - **Explicitly define input/output state mapping:**
      - Input (from parent): `messages`, `nutritional_data`, `overall_confidence`, `clarification_count`, `ampm_data`, `complexity_score`, `language`.
      - Output (to parent): `nutritional_data`, `clarification_count`, `ampm_data`, `needs_clarification`, `needs_review`.
    - Create `get_ampm_graph() -> CompiledGraph` function.
    - **Graph structure:**
      ```
      START -> detail_cycle -> [conditional]
        if all items above threshold OR max_clarifications reached -> [conditional]
          if complexity_score > 0.7 AND detail_cycle inconclusive -> final_probe -> END
          else -> END
        else -> detail_cycle (loop)
      ```
    - Wire nodes from `ampm_nodes.py`.

- [ ] Task 3: Create AMPM Node Implementations
  - File: `backend/app/agent/ampm_nodes.py` [NEW]
  - Action:
    - Implement `detail_cycle(state: AgentState) -> dict` (non-streaming).
    - Implement `detail_cycle_streaming(state: AgentState) -> AsyncGenerator[SSEEvent | dict, None]` (streaming variant).
      - Emit `EVENT_DETAIL_CYCLE` thought event.
      - Analyze `nutritional_data` for items with confidence < threshold.
      - **Prioritize questions by nutritional variance impact** (e.g., cooking method > lettuce type). Include this directive in the LLM prompt.
      - Generate a specific clarification question targeting the highest-impact low-confidence item.
      - **Handle non-answers:** If user responds "I don't know" / "not sure", accept the response, log it, keep current best estimate, and do NOT re-ask.
      - Update `ampm_data` with the question and response.
      - Increment `clarification_count`.
    - Implement `final_probe(state: AgentState) -> dict` (non-streaming).
    - Implement `final_probe_streaming(state: AgentState) -> AsyncGenerator[SSEEvent | dict, None]` (streaming variant).
      - Emit `EVENT_FINAL_PROBE` thought event.
      - Check `complexity_score > 0.7` AND detail cycle was inconclusive.
      - If triggered, ask the **exact localized phrasing**: "Did you have anything else **with that**?" / "Had je er nog iets anders **bij**?" via `get_message("final_probe")`.
      - If not triggered, pass through with no user interaction.
    - **Error handling:** Wrap LLM calls in try/except. On failure, emit `EVENT_ERROR`, set `needs_review=True`, and exit the subgraph gracefully.

- [ ] Task 4: Refactor Main Graph Routing
  - File: `backend/app/agent/routing.py`
  - Action:
    - Update `route_by_confidence` to return `AMPM_ENTRY` instead of `GENERATE_CLARIFICATION` when confidence < threshold.
    - Keep `MAX_CLARIFICATIONS` guard: if `clarification_count >= MAX_CLARIFICATIONS`, return `FINALIZE_LOG` (unchanged).
  - File: `backend/app/agent/graph.py`
  - Action:
    - In `get_agent_graph()`:
      - Remove `GENERATE_CLARIFICATION` node.
      - Add `AMPM_ENTRY` node pointing to the compiled AMPM subgraph from `get_ampm_graph()`.
      - Update conditional edges: `AMPM_ENTRY` replaces `GENERATE_CLARIFICATION` in the routing map.
      - Wire `AMPM_ENTRY -> FINALIZE_LOG -> END`.
      - **Add comment:** `# AMPM streaming logic mirrored in run_streaming_agent() — keep in sync`
    - In `run_streaming_agent()`:
      - Replace the `generate_clarification_streaming(state)` call with AMPM streaming logic:
        1. Call `detail_cycle_streaming(state)` in a loop (respecting `MAX_CLARIFICATIONS`).
        2. After detail cycle, check `complexity_score` and conditionally call `final_probe_streaming(state)`.
      - Maintain existing SSE event yielding pattern.
      - **Add comment:** `# AMPM graph logic mirrored in get_agent_graph() — keep in sync`

- [ ] Task 5: Update `analyze_input` to Output `complexity_score`
  - File: `backend/app/agent/nodes.py`
  - Action:
    - In `analyze_input` and `analyze_input_streaming`, update the LLM structured output schema to include a `complexity_score: float` field (0.0–1.0).
    - The LLM prompt addition: "Rate the meal complexity from 0.0 (simple, single item) to 1.0 (complex, multi-component) considering: number of distinct items, presence of composite dishes, ambiguous portions, and mixed preparations."
    - Add `complexity_score` to the returned state update dict.
    - Optionally add time/occasion context to the analysis prompt: "If identifiable, note the meal occasion (breakfast, lunch, dinner, snack) as it affects typical portion estimation."

### Acceptance Criteria

- [ ] AC 1: High Confidence Bypass
  - Given a clear meal image (confidence >= 0.85),
  - When the agent analyzes it,
  - Then it skips the AMPM subgraph and goes directly to `finalize_log`.

- [ ] AC 2: Low Confidence Trigger
  - Given a complex/ambiguous meal image (confidence < 0.85),
  - When the agent analyzes it,
  - Then it enters the AMPM subgraph and asks a clarification question (Detail Cycle).

- [ ] AC 3: Detail Cycle Iteration
  - Given the agent is in the Detail Cycle,
  - When the user answers a clarification question,
  - Then the agent updates the `nutritional_data` and conditionally asks another question OR moves to Final Probe.

- [ ] AC 4: Conditional Final Probe
  - Given the Detail Cycle is complete,
  - When the `complexity_score` is high (> 0.7) AND detail cycle was inconclusive,
  - Then the agent asks "Did you have anything else **with that**?" (Final Probe).
  - Given the `complexity_score` is low or detail cycle resolved all items,
  - Then the agent skips the Final Probe and finalizes.

- [ ] AC 5: MAX_CLARIFICATIONS Guard
  - Given the agent is in the AMPM subgraph,
  - When `clarification_count` reaches `MAX_CLARIFICATIONS` (2),
  - Then the subgraph exits immediately, sets `needs_review=True`, and routes to `finalize_log`.

- [ ] AC 6: Error Resilience
  - Given the agent is in the Detail Cycle or Final Probe,
  - When an LLM call fails,
  - Then the agent emits an `EVENT_ERROR`, sets `needs_review=True`, exits the subgraph gracefully, and routes to `finalize_log`.

- [ ] AC 7: Streaming Parity
  - Given a request processed via `run_streaming_agent()`,
  - When AMPM is triggered,
  - Then the streaming path produces the same AMPM behavior as the compiled graph path, including correct SSE events.

- [ ] AC 8: Localization
  - Given a user with `language="nl"`,
  - When the Detail Cycle or Final Probe emits a question,
  - Then the question is displayed in Dutch (NL).

- [ ] AC 9: Non-Answer Handling
  - Given the agent asks a detail question,
  - When the user responds "I don't know" or equivalent,
  - Then the agent accepts the response, keeps the current estimate, and does NOT re-ask the same question.

- [ ] AC 10: Question Prioritization
  - Given multiple low-confidence items exist,
  - When the Detail Cycle selects a question,
  - Then it targets the item with the highest nutritional variance impact first.

## Additional Context

### Dependencies

*   LangGraph (existing)

### Testing Strategy

-   **Unit Tests:**
    -   Test `get_ampm_graph()` compiles correctly.
    -   Test `route_by_confidence` returns `AMPM_ENTRY` when confidence < 0.85 and `FINALIZE_LOG` when >= 0.85.
    -   Test `route_by_confidence` returns `FINALIZE_LOG` when `clarification_count >= MAX_CLARIFICATIONS`.
    -   Test `detail_cycle` node logic with mocked LLM (verifies correct item targeting and nutritional variance prioritization).
    -   Test `final_probe` conditional logic (fires when `complexity_score > 0.7`, skips otherwise).
    -   Test `complexity_score` is included in LLM structured output and forwarded in state.
    -   Test error handling in `detail_cycle` and `final_probe` (mocked LLM failure -> graceful exit).
    -   Test `AMPMPassData` TypedDict validation.
    -   Test non-answer detection ("I don't know" -> accepted, not re-asked).
-   **Integration Tests:**
    -   Test full subgraph execution: `AMPM_ENTRY -> detail_cycle -> final_probe -> END` with mocked LLM.
    -   Test subgraph-to-main-graph handoff: verify state flows correctly from AMPM back to `finalize_log` (input/output mapping).
    -   Test streaming path (`run_streaming_agent`) produces correct SSE event sequence when AMPM is triggered.
-   **Manual Verification:**
    -   **Scenario A (Simple)**: Upload a clear apple photo. Verify it finalizes immediately. No AMPM SSE events.
    -   **Scenario B (Complex)**: Upload a messy dinner plate. Verify clarifying questions. Verify `EVENT_DETAIL_CYCLE` SSE events.
    -   **Scenario C (Forgotten Item)**: Complex meal with high `complexity_score`. Verify Final Probe: "Did you have anything else with that?"
    -   **Scenario D (NL Locale)**: Set language to NL. Verify Dutch questions.
    -   **Scenario E (Error)**: Simulate LLM timeout mid-Detail-Cycle. Verify graceful exit with `needs_review=True`.
    -   **Scenario F (Non-Answer)**: Answer "I don't know" to a detail question. Verify it moves on without re-asking.

### Notes

*   Latency is critical. The "Detail Cycle" prompts should be optimized for speed.
*   The existing `generate_clarification` and `generate_clarification_streaming` functions in `nodes.py` can be deprecated after AMPM is verified working. Do NOT delete them until AMPM is confirmed stable.
*   **Future consideration (Expert Panel):** Long-term, eliminate `run_streaming_agent()` entirely and migrate to LangGraph's `astream_events()` API to remove the dual execution path maintenance burden.
*   **Future consideration (Expert Panel):** Add Time & Occasion context ("Was this breakfast, lunch, dinner, or a snack?") as a low-cost addition to improve portion estimation accuracy.
