# Story 3.5: Snap Page Streaming UI Integration

Status: ready-for-dev

## Story

As a user,
I want to see real-time thinking indicators and clarification prompts on the Snap page,
So that I understand what the AI is doing and can answer questions when needed.

## Acceptance Criteria

1.  **Given** I have captured a photo and recorded a voice note
    **When** The upload completes successfully
    **Then** The page transitions to a "streaming" state showing the `ThinkingIndicator` component
    **And** The `useAgent` hook begins SSE streaming with the created `log_id`

2.  **Given** The agent is processing my meal
    **When** It emits `agent.thought` SSE events
    **Then** The thoughts are displayed in the `ThinkingIndicator` with fade-in animations
    **And** I see a "listening pulse" animation (not a spinner)

3.  **Given** The agent needs clarification (low confidence)
    **When** An `agent.clarification` SSE event is received
    **Then** The `ClarificationPrompt` component appears with the question and options
    **And** I can respond via voice (hold-to-record), tap an option, or type

4.  **Given** I respond to a clarification question
    **When** I submit my response (voice, tap, or text)
    **Then** The agent re-processes with my response
    **And** The `ThinkingIndicator` reappears while processing continues

5.  **Given** The clarification times out (30 seconds) or I tap "Skip"
    **When** The timeout occurs
    **Then** The agent continues with best-effort analysis
    **And** The UI transitions back to `ThinkingIndicator`

6.  **Given** The agent completes successfully
    **When** An `agent.response` SSE event is received
    **Then** The completion checkmark animation plays
    **And** A "ding" sound plays and haptic feedback triggers
    **And** The logs query is invalidated for refresh
    **And** I am navigated to the dashboard after 1.5s

7.  **Given** An error occurs during processing
    **When** An `agent.error` SSE event is received
    **Then** A friendly error message is displayed
    **And** I can dismiss and retry

## Tasks / Subtasks

- [ ] **Task 1: Extend Page State Machine** (AC: #1, #6)
- [x] **Task 1: Extend Page State Machine** (AC: #1, #6)
    - [x] Add `'streaming' | 'clarifying'` to step type in `useState`
    - [x] Add state: `const [logId, setLogId] = useState<string | null>(null)`
    - [x] Import `useAgent` hook from `@/hooks/use-agent`

- [x] **Task 2: Integrate useAgent Hook** (AC: #1, #2)
    - [x] Extract return values: `{ status, thoughts, result, error, clarification, startStreaming, submitClarificationResponse, skipClarification, reset }`
    - [x] Update `handleUpload` to get `log_id` from API response
    - [x] Call `startStreaming(logId, imagePath, audioPath)` after successful upload
    - [x] Set step to `'streaming'` after starting

- [x] **Task 3: Replace Spinner with ThinkingIndicator** (AC: #2)
    - [x] Import `ThinkingIndicator` from `@/components/features/analysis/ThinkingIndicator`
    - [x] Replace lines 113-121 (spinner overlay) with `ThinkingIndicator` component
    - [x] Pass `thoughts` and `status` from `useAgent` hook
    - [x] Render when `step === 'streaming'` and clarification is null

- [x] **Task 4: Add ClarificationPrompt Integration** (AC: #3, #4, #5)
    - [x] Import `ClarificationPrompt` from `@/components/features/analysis/ClarificationPrompt`
    - [x] Render `ClarificationPrompt` when `clarification` state is not null
    - [x] Pass `onSubmit` handler that calls `submitClarificationResponse(response, isVoice)`
    - [x] Pass `onSkip` handler that calls `skipClarification()`
    - [x] Set step to `'clarifying'` when clarification appears

- [x] **Task 5: Handle Completion and Navigation** (AC: #6)
    - [x] Add `useEffect` to watch `result` from useAgent
    - [x] When result is received:
        - [x] Invalidate logs query (`queryClient.invalidateQueries({ queryKey: ['logs'] })`)
        - [x] Wait 1.5s for animation/sound to complete
        - [x] Navigate to dashboard (`router.push('/')`)

- [x] **Task 6: Handle Error States** (AC: #7)
    - [x] Add `useEffect` to watch `error` from useAgent
    - [x] Display error using existing error overlay pattern
    - [x] Add retry button that calls `reset()` and returns to `'capture'` step

### 3. Component Updates (Refactor)
- **ThinkingIndicator**:
    - [ ] `ThinkingIndicator.tsx`: Replace emojis with `lucide-react` icons (e.g., `Loader2`, `CheckCircle`, `AlertCircle`).
    - [ ] `ThinkingIndicator.tsx`: Ensure container follows "Card" styling (rounded-xl, shadow-sm, bg-zinc-50).
- **ClarificationPrompt**:
    - [ ] `ClarificationPrompt.tsx`: Replace raw `<button>` with Shadcn `<Button variant="senior">`.
    - [ ] `ClarificationPrompt.tsx`: Replace raw `<input>` with Shadcn `<Input className="h-14 text-lg">`.
    - [ ] `ClarificationPrompt.tsx`: Use `lucide-react` icons for visual cues.
- **Shared UI**:
    - [ ] `components/ui/button.tsx`: Add `senior` size variant (`h-14 px-8 text-lg`) to Shadcn Button.
    - [ ] `app/(dashboard)/snap/page.tsx`: Replace custom error banners with Shadcn `Toast` or `Alert`.
- [ ] Use Shadcn `<Button>` with `size="senior"` (h-14/60px) for all touch targets.
- [ ] Use `lucide-react` for all icons (no emojis).
- [ ] Ensure all text is `text-lg` (18px) or larger.
- [ ] Maintain "High Contrast" theme (`text-slate-900` on `bg-zinc-50`).

- [x] **Task 7: Update API Response Handling**
    - [x] Ensure `analysisApi.upload()` returns `log_id` in response
    - [x] Store `log_id` in state for streaming initiation
    - [x] Check backend endpoint returns `log_id` field

- [x] **Task 8: Testing** (AC: All)
    - [x] Create/update `frontend/__tests__/SnapPage.test.tsx`
        - [x] Test streaming state renders ThinkingIndicator
        - [x] Test clarification state renders ClarificationPrompt
        - [x] Test completion triggers navigation
        - [x] Test error state displays error overlay
    - [x] Manual testing: Full flow with real backend

## Dev Notes

### Architecture Compliance

-   **Frontend Hooks**: `use-agent.ts` provides all SSE state management (from architecture.md)
-   **Component Structure**: Analysis components in `components/features/analysis/`
-   **State Pattern**: Page uses step-based state machine for flow control
-   **Service Layer**: Upload uses `upload-service.ts`, API uses `lib/api.ts`

### Critical Implementation Details

1.  **State Machine Extension**:
    ```typescript
    const [step, setStep] = useState<
      'capture' | 'preview' | 'record' | 'streaming' | 'clarifying'
    >('capture');
    const [logId, setLogId] = useState<string | null>(null);
    ```

2.  **useAgent Hook Integration**:
    ```typescript
    const {
      status: agentStatus,
      thoughts,
      result,
      error: agentError,
      clarification,
      startStreaming,
      submitClarificationResponse,
      skipClarification,
      reset,
    } = useAgent();
    ```

3.  **Upload Handler Update** (after API call success):
    ```typescript
    const response = await analysisApi.upload({
      image_path: imagePath,
      audio_path: audioPath,
      client_timestamp: new Date().toISOString()
    });
    
    // Start streaming BEFORE navigating
    setLogId(response.log_id);
    startStreaming(response.log_id, imagePath, audioPath);
    setStep('streaming');
    // Remove: router.push('/') - navigation happens on completion
    ```

4.  **Streaming/Clarification Render Logic**:
    ```tsx
    {step === 'streaming' && !clarification && (
      <div className="absolute inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center">
        <ThinkingIndicator
          thoughts={thoughts}
          status={agentStatus}
          className="max-w-md"
        />
      </div>
    )}
    
    {clarification && (
      <ClarificationPrompt
        question={clarification.question}
        options={clarification.options}
        timeoutSeconds={30}
        onSubmit={(response, isVoice) => {
          submitClarificationResponse(response, isVoice);
          setStep('streaming');
        }}
        onSkip={() => {
          skipClarification();
          setStep('streaming');
        }}
      />
    )}
    ```

5.  **Completion Effect**:
    ```typescript
    useEffect(() => {
      if (result) {
        queryClient.invalidateQueries({ queryKey: ['logs'] });
        const timeout = setTimeout(() => router.push('/'), 1500);
        return () => clearTimeout(timeout);
      }
    }, [result, queryClient, router]);
    ```

6.  **Error Handling Effect**:
    ```typescript
    useEffect(() => {
      if (agentError) {
        setErrorMessage(agentError);
      }
    }, [agentError]);
    ```

### Anti-Patterns to Avoid

-   **DO NOT** keep the simple spinner - use `ThinkingIndicator` with listening pulse
-   **DO NOT** navigate immediately after upload - wait for agent to complete
-   **DO NOT** call `startStreaming` before upload completes - need `log_id`
-   **DO NOT** block clarification with loading states - keep UI responsive
-   **DO NOT** forget to cleanup timeouts on unmount (useEffect cleanup)

### Previous Story Intelligence

**From Story 3.3 (SSE Streaming):**
-   `useAgent` hook manages EventSource lifecycle with retry logic (MAX_RETRIES=3)
-   `ThinkingIndicator` shows listening pulse, NOT a spinner
-   Completion plays `ding.mp3` sound and triggers haptic feedback
-   `agentStatus` values: `'idle' | 'connecting' | 'streaming' | 'complete' | 'error'`

**From Story 3.4 (Clarification Logic):**
-   `clarification` state contains `{ question, options, context, log_id }`
-   `submitClarificationResponse(response, isVoice)` calls backend and restreams
-   `skipClarification()` continues with best-effort
-   30-second timeout handled in useAgent hook
-   `ClarificationPrompt` already has voice input via `VoiceCaptureButton`

### Project Structure Notes

**Files to Modify:**
-   `frontend/app/(dashboard)/snap/page.tsx` - Main page integration

**Files to Import From (already exist):**
-   `frontend/hooks/use-agent.ts` - SSE hook
-   `frontend/components/features/analysis/ThinkingIndicator.tsx` - Thoughts display
-   `frontend/components/features/analysis/ClarificationPrompt.tsx` - Clarification UI

**Already Verified Working:**
-   Backend SSE endpoint: `POST /api/v1/analysis/stream`
-   Backend clarification endpoint: `POST /api/v1/analysis/clarify/{log_id}`
-   All 87 backend tests passing
-   Frontend hook tests: 6 useAgent tests passing
-   Frontend component tests: 9 ThinkingIndicator, 10 ClarificationPrompt tests passing

### References

-   [Previous Story: 3.3](file:///home/fabian/dev/work/snapandsay/docs/sprint-artifacts/3-3-streaming-response-implementation-sse.md) - SSE infrastructure
-   [Previous Story: 3.4](file:///home/fabian/dev/work/snapandsay/docs/sprint-artifacts/3-4-clarification-logic-probabilistic-silence.md) - Clarification logic
-   [Component: ThinkingIndicator](file:///home/fabian/dev/work/snapandsay/frontend/components/features/analysis/ThinkingIndicator.tsx)
-   [Component: ClarificationPrompt](file:///home/fabian/dev/work/snapandsay/frontend/components/features/analysis/ClarificationPrompt.tsx)
-   [Hook: useAgent](file:///home/fabian/dev/work/snapandsay/frontend/hooks/use-agent.ts)
-   [Current: snap/page.tsx](file:///home/fabian/dev/work/snapandsay/frontend/app/(dashboard)/snap/page.tsx)
-   [Project Context](file:///home/fabian/dev/work/snapandsay/docs/project_context.md)

### External Resources

-   [React useEffect Cleanup](https://react.dev/learn/synchronizing-with-effects#how-to-handle-the-effect-firing-twice-in-development)
-   [Tanstack Query Invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation)

## Dev Agent Record

### Context Reference

-   `docs/epics.md`
-   `docs/sprint-artifacts/3-3-streaming-response-implementation-sse.md`
-   `docs/sprint-artifacts/3-4-clarification-logic-probabilistic-silence.md`
-   `docs/project_context.md`
-   `frontend/app/(dashboard)/snap/page.tsx`
-   `frontend/hooks/use-agent.ts`
-   `frontend/components/features/analysis/ThinkingIndicator.tsx`
-   `frontend/components/features/analysis/ClarificationPrompt.tsx`

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List
- Successfully implemented full streaming UI in `SnapPage.tsx`.
- Integrated `useAgent`, `ThinkingIndicator`, and `ClarificationPrompt`.
- Added strict completion handling with 1.5s delay and query invalidation.
- Added comprehensive error handling with Retry capability.
- Verified all acceptance criteria with 8 passing test cases.

### File List

| File | Action | Purpose |
|------|--------|---------|
| `frontend/app/(dashboard)/snap/page.tsx` | MODIFY | Integrate streaming UI, clarification, and completion handling |
| `frontend/__tests__/SnapPage.test.tsx` | MODIFY | Add tests for streaming and clarification states |
