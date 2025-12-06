# Story 2.1: Camera Capture Component

Status: done

## Story

As a user,
I want to take a photo of my meal with a simple, large interface,
so that I can visually log what I'm eating.

## Acceptance Criteria

1.  **Given** I am on the "Snap" page (`/app/snap`)
    **When** The component mounts
    **Then** The camera view is active full-screen
    **And** I see a large (60px+) white shutter button centered at the bottom
    **And** A permission request for camera access is handled gracefully (if not already granted)

2.  **Given** The camera is active
    **When** I tap the shutter button
    **Then** The camera captures an image immediately (< 200ms shutter lag)
    **And** I receive haptic feedback (if supported by device)
    **And** The UI transitions to show the captured image preview
    **And** The shutter button is replaced by "Retake" and "Next/Mic" options (or similar flow as per UX)

3.  **Given** I have captured a photo
    **When** I tap "Retake"
    **Then** The preview is discarded
    **And** The live camera view is restored

4.  **Given** I am on a mobile device
    **When** I access the camera
    **Then** The rear-facing camera is used by default environment setting

5.  **Given** A capture error occurs (e.g., permission denied)
    **When** The error happens
    **Then** A clear, senior-friendly error message is displayed (e.g., "We need camera access to see your meal.") with a retry button

## Tasks / Subtasks

- [x] Frontend: Infrastructure & Dependencies
    - [x] Install `react-webcam` using `pnpm add react-webcam` (Verify strict lockfile usage).
    - [x] Verify `lucide-react` is available for icons (Camera, X, Check).
- [x] Frontend: Component Implementation (`src/components/features/camera/CameraCapture.tsx`)
    - [x] Create `CameraCapture` component. **CRITICAL**: Must use `"use client"` directive at the top.
    - [x] Configure `react-webcam` props:
        -   `audio={false}`
        -   `screenshotFormat="image/jpeg"`
        -   `videoConstraints={{ facingMode: "environment" }}`
    - [x] Implement `ShutterButton` sub-component: 60x60px minimum touch target, high contrast.
    - [x] Implement capture logic using `getScreenshot()`.
    - [x] Define interface: `interface CameraCaptureProps { onCapture: (imageSrc: string) => void; }`
- [x] Frontend: Preview State (`src/components/features/camera/ImagePreview.tsx`)
    - [x] Create component to display captured base64/blob image.
    - [x] Add "Retake" button (Secondary style).
    - [x] Add "Confirm" transition hook (Next step in "Snap & Say" flow).
- [x] Frontend: Page Integration
    - [x] Create/Update `src/app/(dashboard)/snap/page.tsx`.
    - [x] Integrate `CameraCapture` as the default view.
    - [x] Handle permissions state (Loading / Error / Active).

## Dev Notes

-   **Architecture Compliance**:
    -   **Component Location**: `src/components/features/camera/`.
    -   **Styling**: Use Tailwind CSS with `cn()` utility.
    -   **Icons**: Use `lucide-react`.
    -   **Next.js Client Components**: `react-webcam` and `navigator` APIs **require** the `"use client"` directive. This is a common source of build errors.
    -   **PWA/Mobile Constraints**: Camera APIs require a **Secure Context** (HTTPS or `localhost`). Testing on a real device via local IP (e.g., `192.168.x.x`) will **FAIL** unless you use a tunneling service (like ngrok) or enable "Insecure origins treated as secure" in `chrome://flags` on the device.

-   **UX Specifications (from `docs/ux-design-specification.md`)**:
    -   **Touch Targets**: Minimum 60px height/width for the shutter button.
    -   **Feedback**: Visual shutter effect (flash or brief opacity change) + Haptic feedback (`navigator.vibrate(20)`) on capture.
    -   **Color**: Button should be high contrast (White on dark overlay or standard Primary color).
    -   **Error Messages**: Friendly, non-technical (No "Error 500").

-   **Technical Requirements**:
    -   **Library**: `react-webcam` is recommended for React wrapper convenience over raw `navigator.mediaDevices.getUserMedia`, but raw API is acceptable if lighter weight is desired. For now, `react-webcam` is standard and safe.
    -   **Image Quality**: Capture at sufficient resolution for AI analysis (e.g., 720p or 1080p), but optimize for upload speed (jpeg, 0.8 quality).
    -   **State**: Manage `imageSrc` in local state or parent context (if lifting state up for the multi-step flow).

### Project Structure Notes

-   **Feature Integration**: This story focuses only on the CAMERA CAPTURE. The "Voice" part (Story 2.2) and "Upload" part (Story 2.3) are separate.
-   **State Handoff**: Prepare the component to pass the captured `Blob` or `base64` string to a parent handler (`onCapture(image: string | Blob)`).

### References

-   [Epics: Story 2.1](docs/epics.md#story-21-camera-capture-component)
-   [PRD: FR4 (Multimodal Ingestion)](docs/prd.md#2-multimodal-ingestion)
-   [UX Design: The "Snap & Say" Flow](docs/ux-design-specification.md#1-the-snap--say-flow-primary)

## Dev Agent Record

### Context Reference

-   `docs/epics.md`
-   `docs/prd.md`
-   `docs/ux-design-specification.md`
-   `docs/architecture.md`

### Agent Model Used

-   **Model**: Gemini 2.0 Flash (Antigravity)
-   **Role**: Technical Scrum Master (Bob)

### Debug Log References

-   N/A

### Completion Notes List

### Completion Notes List

-   Implemented `CameraCapture` component with `react-webcam` and custom shutter button.
-   Implemented `ImagePreview` component with "Retake" and "Confirm" actions.
-   Integrated components into `src/app/(dashboard)/snap/page.tsx` with state management for capture/preview flow.
-   Added comprehensive unit tests for all components and integration test for the page flow.
-   **Code Review Fixes (2025-12-06):**
    -   Implemented `onUserMediaError` handling in `CameraCapture` for permission denied scenarios.
    -   Added "Camera Access Needed" UI with retry button.
    -   Enforced HD resolution constraints (`1280x720` min) for higher quality capture.
    -   Verified fixes with updated tests.
-   **AI Code Review Fixes (2025-12-06) - [Fixed Automatically]:**
    -   Implemented `navigator.vibrate(50)` for haptic feedback (AC2).
    -   Implemented visual shutter flash overlay (AC2).
    -   Improved retry logic to reset internal state instead of `window.location.reload()`.
    -   Removed performance-heavy `console.log` of Base64 strings.
    -   Updated tests to verify haptics, flash, and retry logic.
-   All Acceptance Criteria satisfied.

### File List

-   Frontend: Infrastructure & Dependencies
    -   `frontend/package.json`
    -   `frontend/pnpm-lock.yaml`
-   Frontend: Component Implementation
    -   `frontend/components/features/camera/CameraCapture.tsx`
    -   `frontend/__tests__/CameraCapture.test.tsx`
-   Frontend: Preview State
    -   `frontend/components/features/camera/ImagePreview.tsx`
    -   `frontend/__tests__/ImagePreview.test.tsx`
-   Frontend: Page Integration
    -   `frontend/app/(dashboard)/snap/page.tsx`
    -   `frontend/__tests__/SnapPage.test.tsx`
