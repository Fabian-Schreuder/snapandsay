# Tech-Spec: Robust Camera Permission Handling

**Created:** 2025-12-11
**Status:** Ready for Development

## Overview

### Problem Statement
Users who deny camera permissions (accidentally or intentionally) are currently reaching a "dead end" in the application. While the app displays an error message, the "Try Again" functionality is often insufficient because browsers typically persist the "Denied" state, preventing simple programmatic retries from triggering a new permission prompt. The user is left unable to use the core "Snap" functionality.

### Solution
Enhance the `CameraCapture` component to provide a more robust and helpful experience when permissions are denied. This includes:
1.  **Distinguish Error Types:** Clearer differentiation between "Permission Denied" (user action) and "Device Error" (hardware/system issue).
2.  **Educational UI:** If permission is denied, show specific instructions on how to re-enable it (e.g., "Tap the lock icon in your address bar").
3.  **Hard Retry Strategy:** Since re-prompting often requires a page reload or user interaction after clearing settings, update the "Try Again" behavior to potentially reload the page or guide the user to system settings.
4.  **Graceful Exit:** Allow users to navigate back to the dashboard if they cannot or choose not to enable the camera.

### Scope (In/Out)
**In:**
- `frontend/components/features/camera/CameraCapture.tsx`: Update error handling and UI.
- `frontend/components/features/camera/PermissionErrorState.tsx`: (New) dedicated component for the permission error state to keep `CameraCapture` clean.

**Out:**
- Backend changes (this is a client-side browser API issue).
- Changes to audio permissions (though patterns could be reused later).

## Context for Development

### Codebase Patterns
- **Frontend:** Next.js with Tailwind CSS and Lucide icons.
- **State Management:** React `useState` and `useCallback` within components.
- **Camera Library:** `react-webcam` is used for media handling.

### Files to Reference
- `frontend/components/features/camera/CameraCapture.tsx`: Main logic for camera initialization and error trapping.
- `frontend/app/(dashboard)/snap/page.tsx`: Parent page managing the snap flow.

### Technical Decisions
- **`react-webcam` Error Handling:** We will leverage the `onUserMediaError` callback more effectively.
- **Browser-Specific Instructions:** We may add basic detection (mobile vs desktop) to show relevant help text (e.g., "Check site settings" vs "Check system preferences"), but keep it generic enough to be maintainable.

## Implementation Plan

### Tasks

- [ ] **Refactor Error State:** Create a dedicated `PermissionErrorState` component to handle the UI for denied/error states.
- [ ] **Detect Permission Status:** Use the Permissions API (`navigator.permissions.query({ name: 'camera' })`) where possible to proactively check state before loading `react-webcam`.
- [ ] **Improve "Try Again":**
    - If `NotAllowedError` occurred, the "Try Again" button should likely reload the page (`window.location.reload()`) as this is often the only way to re-trigger a prompt after a change in browser settings.
    - Add a "Cancel" or "Go Back" button to `router.push('/')`.
- [ ] **Update Instructions:** Add visual guides or text explaining how to reset permissions for the origin.

### Acceptance Criteria

- [ ] **AC 1:** If user denies permission, they see a clear "Permission Denied" screen with instructions on how to fix it (e.g. "Enable in browser settings").
- [ ] **AC 2:** The "Try Again" button on the error screen effectively triggers a meaningful retry (e.g. page reload) rather than just re-rendering the blocked component.
- [ ] **AC 3:** Users have a way to exit the camera screen ("Go Back") to the dashboard if they cannot enable the camera.
- [ ] **AC 4:** Verify that `OverconstrainedError` (resolution issues) handling is preserved and distinct from permission denial.

## Additional Context

### Dependencies
- None. Uses standard Web APIs.

### Testing Strategy
- **Manual Testing:**
    1.  Open app in Incognito (or reset permissions).
    2.  Click "Snap".
    3.  When prompted, click "Block/Deny".
    4.  Verify the customized error screen appears.
    5.  Verify "Go Back" works.
    6.  Change browser setting to "Ask" or "Allow".
    7.  Click "Try Again" (verify it reloads/retries and works).

### Notes
- Permissions API support for 'camera' varies by browser (Firefox has had historic issues), so robust fallback (try/catch `getUserMedia`) is still primary. The Permissions API check is an optimization.
