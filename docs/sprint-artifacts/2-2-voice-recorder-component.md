# Story 2.2: Voice Recorder Component

Status: ready-for-dev

## Story

As a user,
I want to record a voice note by holding a button,
So that I can describe my meal naturally.

## Acceptance Criteria

1.  **Given** The Voice Capture/Mic button is visible (after taking a photo or in "Say" mode)
    **When** I press and hold the button (Touch Start / Mouse Down)
    **Then** The app requests microphone permission (if not already granted)
    **And** The app starts recording audio immediately
    **And** The button shows a "Pulsing" animation (Visual Feedback)
    **And** I receive haptic feedback (short vibration) indicating start

2.  **Given** I am recording audio
    **When** I release the button (Touch End / Mouse Up)
    **Then** The recording stops
    **And** I receive distinct haptic feedback (e.g., "thud" or double vibration) indicating stop
    **And** The audio data (Blob) is captured and stored in local state
    **And** The UI transitions to a "Success" state (e.g., green checkmark) momentarily before "Recorded" state

3.  **Given** I am using a screen reader
    **When** The recording state changes
    **Then** The screen reader announces "Recording started" or "Recording stopped"

4.  **Given** I am on a mobile device
    **When** I interact with the button
    **Then** The "Hold" gesture handles touch events gracefully (avoiding context menus or text selection)

5.  **Given** An error occurs
    **When** The error is `NotAllowedError` (Permission Denied)
    **Then** A clear, senior-friendly error message appears ("We need your microphone to hear you.")
    **And** If the permission is permanently blocked, the message guides the user to System Settings (e.g., "Please enable microphone access in your browser settings") rather than just retrying

## Tasks / Subtasks

- [ ] Frontend: Infrastructure & Hooks
    - [ ] Create `src/hooks/use-audio.ts`.
        - [ ] Implement `startRecording`: Check `MediaRecorder.isTypeSupported` to prefer `audio/webm;codecs=opus` but fallback to `audio/mp4` for iOS Safari compatibility.
        - [ ] Implement `stopRecording`: Stop recorder, return Blob.
        - [ ] **CRITICAL**: Implement cleanup function that iterates `stream.getTracks()` and calls `.stop()` to release microphone resource on unmount or stop.
        - [ ] Handle `dataavailable` events to collect chunks.
        - [ ] Manage permissions and error states (`NotAllowedError`, `NotFoundError`) with specific flags for "Permanently Denied".
        - [ ] Return interface: `{ start, stop, isRecording, audioBlob, error, duration, isPermissionDenied }`.
- [ ] Frontend: Component Implementation (`src/components/features/voice/VoiceCaptureButton.tsx`)
    - [ ] Create component with `"use client"`.
    - [ ] Define Props: `interface VoiceCaptureButtonProps { onRecordingComplete: (audio: Blob) => void; }`.
    - [ ] Implement "Hold" interaction using `use-long-press` pattern or raw `onTouchStart`/`onTouchEnd` + `onMouseDown`/`onMouseUp`.
    - [ ] Integrate `use-audio` hook.
    - [ ] Implement Haptics (`navigator.vibrate([50])` start, `[20, 50, 20]` stop/success).
    - [ ] Style states using Tailwind:
        -   **Idle**: High contrast Mic icon (Lucide).
        -   **Recording**: `animate-pulse`, potentially color change (Red/Orange).
        -   **Success**: Green background/icon state for momentary feedback after recording.
        -   **Disabled**: Opacity reduced.
    - [ ] Ensure minimum 60x60px touch target.
- [ ] Frontend: Integration
    - [ ] Integrate `VoiceCaptureButton` into `src/app/(dashboard)/snap/page.tsx`.
    - [ ] **State Flow**: Show `VoiceCaptureButton` *after* `ImagePreview` is confirmed (or alongside if defining that UX). *Note: Epics imply "Snap then Say" or combined. UX Flow says: Snap -> Photo Captured -> Hold Mic Button (on same screen or next).*
    - [ ] Ensure state (Image + Audio) is ready for the next step (Upload).

## Dev Notes

### Architecture & Tech Stack

-   **Component Location**: `src/components/features/voice/VoiceCaptureButton.tsx`.
-   **Hook**: `src/hooks/use-audio.ts`.
-   **Dependencies**: `lucide-react` (Mic icon). Native `MediaRecorder` API.
-   **Browser Compatibility**:
    -   Target `audio/webm` (Chrome/Android) or `audio/mp4` (Safari/iOS).
    -   Must check `MediaRecorder.isTypeSupported()` to select optimal mime type dynamically.
-   **Accessibility**:
    -   `aria-label="Hold to record voice note"`
    -   `role="button"`
    -   Live region updates for screen readers.

### UX Specifications (from `docs/ux-design-specification.md`)

-   **"Snap & Say" Flow**: Step 1: Snap (Camera). Step 2: Say (Voice).
-   **Interaction**: Press-and-Hold. This limits the cognitive load of "Start... then Stop". It's a natural "Walkie-Talkie" mode.
-   **Visuals**: "Pulsing" animation is critical for feedback.
-   **Haptics**: Essential for tactile confirmation.

### Project Structure Notes

-   Do NOT introduce complex state management libraries (Redux) yet. Use React `useState` or `useContext` if sharing between Camera and Voice components is needed.
-   Keep `use-audio.ts` generic enough to be reused if needed, but focused on this story's requirements.

### References

-   [Epics: Story 2.2](docs/epics.md#story-22-voice-recorder-component)
-   [UX Design: Voice Capture Button](docs/ux-design-specification.md#1-voicecapturebutton)
-   [Architecture: Browser APIs](docs/architecture.md#technical-constraints--dependencies)

## Dev Agent Record

### Context Reference

-   `docs/epics.md`
-   `docs/ux-design-specification.md`
-   `docs/architecture.md`
-   `docs/sprint-artifacts/2-1-camera-capture-component.md` (Previous Story)

### Agent Model Used

-   **Model**: Gemini 2.0 Flash (Antigravity)
-   **Role**: Technical Scrum Master (Bob)

### Debug Log References

### Completion Notes List

### File List
