---
title: 'Haptic & Sound Feedback System'
slug: 'haptic-sound-feedback'
created: '2026-01-28'
status: 'verification'
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
tech_stack: ['Next.js 14+', 'TypeScript', 'React 18', 'Web Vibration API', 'Web Audio API', 'localStorage']
files_to_modify:
  - frontend/hooks/use-feedback.ts (NEW)
  - frontend/hooks/use-agent.ts
  - frontend/components/features/voice/VoiceCaptureButton.tsx
  - frontend/components/features/camera/CameraCapture.tsx
  - frontend/components/FeedbackSettingsToggle.tsx (NEW)
  - frontend/public/sounds/success.mp3 (NEW)
  - frontend/public/sounds/error.mp3 (NEW)
  - frontend/public/sounds/start.mp3 (NEW)
  - frontend/public/sounds/stop.mp3 (NEW)
  - frontend/public/sounds/tap.mp3 (NEW)
  - frontend/messages/en.json
  - frontend/messages/nl.json
  - frontend/__tests__/hooks/use-feedback.test.ts (NEW)
code_patterns: ['Custom React hooks', 'localStorage for preferences', 'Preloaded audio']
test_patterns: ['Jest unit tests for hooks', 'Mocked navigator.vibrate']
---

# Tech-Spec: Haptic & Sound Feedback System

**Created:** 2026-01-28

## Overview

### Problem Statement

The current codebase has **ad-hoc vibration and sound feedback** scattered across multiple components (`VoiceCaptureButton`, `CameraCapture`, `use-agent`). The only sound file (`ding.mp3`) is a placeholder. There is no centralized feedback system, no user preference settings, and no way to extend feedback patterns consistently.

### Solution

Create a **centralized `useFeedback()` hook** that:
1. Provides semantic feedback methods (`success()`, `error()`, `tap()`, `start()`, `stop()`)
2. Combines vibration patterns + sound effects per feedback type
3. Reads user preferences from localStorage (sound on/off, vibration on/off)
4. Exposes a settings UI component for toggling preferences
5. Replaces all existing inline feedback calls with the centralized hook

### Scope

**In Scope:**
- Create `useFeedback()` hook with semantic methods
- Add sound files: success, error, recording-start, recording-stop, tap
- Create user settings UI for toggling sound/vibration
- Persist preferences in localStorage
- Add i18n strings for feedback settings
- Refactor existing feedback calls in `VoiceCaptureButton`, `CameraCapture`, `use-agent`
- Unit tests for the new hook

**Out of Scope:**
- Backend user preference storage (localStorage only for now)
- Accessibility announcements (screen reader integration)
- Custom sound selection by users

## Context for Development

### Codebase Patterns

| Pattern | Location | Notes |
|---------|----------|-------|
| Custom hooks | `frontend/hooks/` | Follow `use-*.ts` naming, export interface for return type |
| Vibration API | `navigator.vibrate()` | Always check `typeof navigator !== 'undefined' && navigator.vibrate` |
| Audio preload | `use-agent.ts:99` | `new Audio(URL); audio.preload = 'auto';` pattern |
| Settings persistence | `LanguageToggle.tsx` | Cookie pattern, but we'll use localStorage |
| i18n | `frontend/messages/*.json` | Add to existing `settings` namespace |
| Test mocks | `__tests__/hooks/use-agent.test.ts` | Mock `Audio` class + `navigator.vibrate` via `Object.defineProperty` |

### Files to Reference

| File | Purpose |
| ---- | ------- |
| [use-agent.ts](file:///home/fabian/dev/work/snapandsay/frontend/hooks/use-agent.ts#L174-186) | `triggerCompletionFeedback()` pattern: audio + vibrate |
| [VoiceCaptureButton.tsx](file:///home/fabian/dev/work/snapandsay/frontend/components/features/voice/VoiceCaptureButton.tsx#L52-54) | Vibration on recording success |
| [CameraCapture.tsx](file:///home/fabian/dev/work/snapandsay/frontend/components/features/camera/CameraCapture.tsx#L67-68) | Vibration on shutter |
| [LanguageToggle.tsx](file:///home/fabian/dev/work/snapandsay/frontend/components/LanguageToggle.tsx) | Settings UI pattern (Select component) |
| [use-agent.test.ts](file:///home/fabian/dev/work/snapandsay/frontend/__tests__/hooks/use-agent.test.ts#L8-19) | Mock patterns for Audio + vibrate |

### Technical Decisions

1. **localStorage over cookies**: Simpler, no backend needed, instant read
2. **Preload all sounds on mount**: Better PWA experience, avoid latency on first trigger
3. **Silent failures**: If vibrate/audio not supported, log warning but don't throw
4. **SSR safety**: Check `typeof window !== 'undefined'` before accessing browser APIs

---

## Implementation Plan

### Tasks

#### Phase 1: Sound Assets

- [ ] **Task 1**: Add placeholder sound files
  - Files: `frontend/public/sounds/{success,error,start,stop,tap}.mp3`
  - Action: Source or generate 5 short MP3 sound effects (~100KB each max)
  - Notes: Can use free sources like [freesound.org](https://freesound.org) or generate with `ffmpeg`. Keep files small for PWA performance. Delete the placeholder `ding.mp3`.

---

#### Phase 2: Core Hook

- [ ] **Task 2**: Create `useFeedback()` hook
  - File: `frontend/hooks/use-feedback.ts` (NEW)
  - Action: Implement hook with:
    - Interface: `UseFeedbackReturn` with methods `success()`, `error()`, `tap()`, `start()`, `stop()`
    - localStorage keys: `feedback_sound_enabled`, `feedback_vibration_enabled` (default both `true`)
    - Sound preloading on mount using `useRef<HTMLAudioElement[]>`
    - Vibration patterns per type (e.g., success: `[20, 50, 20]`, error: `[100, 50, 100]`, tap: `50`)
    - SSR-safe guards for `window`, `navigator.vibrate`, `Audio`
  - Notes: Follow `use-agent.ts` audio preload pattern

- [ ] **Task 3**: Create unit tests for `useFeedback()`
  - File: `frontend/__tests__/hooks/use-feedback.test.ts` (NEW)
  - Action: Test cases:
    - Default preferences are `true`
    - Methods call `navigator.vibrate` when enabled
    - Methods call `audio.play()` when enabled
    - Methods do NOT call vibrate/audio when disabled
    - Preferences persist to localStorage
  - Notes: Follow mock patterns from `use-agent.test.ts`

---

#### Phase 3: Settings UI

- [x] **Task 4**: Add i18n strings for feedback settings
  - Files: `frontend/messages/en.json`, `frontend/messages/nl.json`
  - Action: Add to `settings` namespace:
    ```json
    "feedback": "Feedback",
    "feedbackDescription": "Control sound and vibration feedback",
    "soundEnabled": "Sound",
    "vibrationEnabled": "Vibration"
    ```
  - Notes: Dutch translations: `"Geluidsterugkoppeling"`, `"Trillingsterugkoppeling"`, etc.

- [x] **Task 5**: Create `FeedbackSettingsToggle` component
  - File: `frontend/components/FeedbackSettingsToggle.tsx` (NEW)
  - Action: Create component with:
    - Two `Switch` components (from Shadcn/UI) for sound and vibration
    - Uses `useFeedback()` to read/write preferences
    - Follows `LanguageToggle.tsx` structure
  - Notes: Use `useTranslations('settings')` for i18n

---

#### Phase 4: Refactor Existing Code

- [x] **Task 6**: Refactor `use-agent.ts`
  - File: `frontend/hooks/use-agent.ts`
  - Action:
    - Import and use `useFeedback()` hook
    - Replace `triggerCompletionFeedback()` implementation (lines 174-186) to call `feedback.success()`
    - Remove direct `Audio` instantiation and `navigator.vibrate` calls
    - Keep `audioRef` cleanup logic
  - Notes: Ensure tests in `use-agent.test.ts` still pass or are updated

- [x] **Task 7**: Refactor `VoiceCaptureButton.tsx`
  - File: `frontend/components/features/voice/VoiceCaptureButton.tsx`
  - Action:
    - Import and use `useFeedback()` hook
    - Replace line 52-54 (success vibration) with `feedback.success()`
    - Replace line 73-74 (start vibration) with `feedback.start()`
  - Notes: Component should no longer directly call `navigator.vibrate`

- [x] **Task 8**: Refactor `CameraCapture.tsx`
  - File: `frontend/components/features/camera/CameraCapture.tsx`
  - Action:
    - Import and use `useFeedback()` hook
    - Replace line 67-68 (shutter vibration) with `feedback.tap()`
  - Notes: The "tap" feedback is appropriate for shutter-like actions

---

#### Phase 5: Integration

- [ ] **Task 9**: Wire settings into settings page/modal
  - File: Determine existing settings location (likely same place as `LanguageToggle`)
  - Action: Add `<FeedbackSettingsToggle />` below `<LanguageToggle />`
  - Notes: If no dedicated settings page exists, may need to create one or add to an existing modal

---

### Acceptance Criteria

- [ ] **AC1**: Given sound/vibration are enabled (default), when `feedback.success()` is called, then both sound plays AND device vibrates
- [ ] **AC2**: Given sound is disabled in settings, when any feedback method is called, then no sound plays but vibration still works
- [ ] **AC3**: Given vibration is disabled in settings, when any feedback method is called, then no vibration occurs but sound still plays
- [ ] **AC4**: Given both sound and vibration are disabled, when any feedback method is called, then neither sound nor vibration occurs
- [ ] **AC5**: Given user toggles a setting, when they reload the page, then the preference persists
- [ ] **AC6**: Given device doesn't support vibration, when feedback methods are called, then sound still plays and no error is thrown
- [ ] **AC7**: Given photo is captured, when shutter button is pressed, then `tap` feedback triggers
- [ ] **AC8**: Given voice recording starts, when recording button is pressed, then `start` feedback triggers
- [ ] **AC9**: Given agent analysis completes, when result is received, then `success` feedback triggers
- [ ] **AC10**: Given settings UI is visible, when user toggles switches, then changes take effect immediately

---

## Additional Context

### Dependencies

- No new npm packages required
- Sound files needed (MP3 format, <100KB each)
- Shadcn/UI `Switch` component (already installed)

### Testing Strategy

**Automated Tests:**
```bash
# Run unit tests for the new hook
cd frontend && pnpm test -- --testPathPattern="use-feedback"

# Run all hook tests to ensure no regressions
cd frontend && pnpm test -- --testPathPattern="hooks"
```

**Manual Verification:**
1. Open app on mobile device (iOS/Android)
2. Navigate to Settings (or wherever `FeedbackSettingsToggle` is placed)
3. Verify both toggles default to ON
4. Take a photo → verify tap vibration + sound
5. Start voice recording → verify start vibration + sound
6. Complete agent analysis → verify success vibration + sound
7. Toggle sound OFF → repeat above, verify NO sound but vibration still works
8. Toggle vibration OFF → repeat above, verify NO vibration but sound still works
9. Reload page → verify settings persist

### Notes

- **Target demographic**: Older adults (65+) — sounds should be clear, gentle, not startling
- **Haptic patterns**: Keep vibrations short and noticeable but not aggressive
- **PWA consideration**: Preload sounds on first interaction to avoid audio context issues on mobile Safari
- **Future**: Could add more feedback types (e.g., `warning`, `notification`) if needed
