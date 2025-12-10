# Test Plan: Epic 2 - Media Capture

**Version:** 1.0
**Date:** 2025-12-10
**Author:** Antigravity (Test Design Agent)
**Status:** Draft

## 1. Introduction
This test plan validates **Epic 2: Media Capture**, covering camera photo capture, voice recording, and the integrated upload process.
**Stories:**
- 2.1: Camera Capture
- 2.2: Voice Recorder
- 2.3: Combined Capture & Upload

## 2. Test Objectives
- Verify users can take a photo and retake it if needed.
- Verify users can record audio, stop it, and get feedback.
- Verify that confirming both inputs triggers an upload to Supabase Storage.
- Verify that a `DietaryLog` record is created after upload.

## 3. Test Strategy
**Strategy:** Hybrid (Component Tests + E2E Tests).
**Challenge:** Browser APIs (`getUserMedia`, `MediaRecorder`) require permissions and are hard to mock in headless implementation without flags.
**Approach:**
- **Mocking:** Use Playwright's `page.addInitScript` or browser args to fake media streams.
- **Bypass:** For E2E, we might assume the "file" is pre-selected or simulated if we can't get a fake stream easily.
- **Upload Validation:** Intercept network requests to `v1/analysis/upload` to verify payload.

## 4. Test Scenarios

### TS-2.1: Camera Flow (Mocked)
**Goal:** Verify camera UI interaction.
- **Steps:**
    1. Navigate to `/app/snap`.
    2. Click "Shutter".
    3. Verify "Retake" / "Next" buttons appear.
    4. Click "Retake" -> UI resets to camera view.

### TS-2.2: Voice Flow (Mocked)
**Goal:** Verify voice recording interaction.
- **Pre-req:** Photo token.
- **Steps:**
    1. Hold "Mic" button (simulate long press).
    2. Release button.
    3. Verify "Success" state.

### TS-2.3: Upload Integration
**Goal:** Verify end-to-end upload sequence.
- **Steps:**
    1. Complete Camera Flow (Mocked image).
    2. Complete Voice Flow (Mocked audio).
    3. Click "Done" / Trigger Upload.
    4. Verify request to `POST /api/v1/analysis/upload`.
    5. Verify Success UI.

## 5. Execution Plan
- Implement `tests/e2e/e2-media.spec.ts`.
- Use `fake-device-for-media-stream` launch flag for Playwright.
