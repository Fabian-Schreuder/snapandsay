---
title: 'Verify & Fix Dutch Support'
slug: 'verify-fix-dutch-support'
created: '2026-01-21'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python', 'FastAPI', 'OpenAI Whisper', 'Next.js', 'Typescript', 'next-intl']
files_to_modify: ['backend/app/services/voice_service.py', 'backend/app/agent/nodes.py', 'frontend/components/features/logs/DailySummary.tsx', 'frontend/messages/en.json', 'frontend/messages/nl.json']
code_patterns: ['Service Layer pattern', 'State management in nodes', 'React Hooks', 'i18n']
test_patterns: ['End-to-end verification via voice input', 'Visual inspection of UI', 'Unit tests for voice service']
---

# Verify & Fix Dutch Support

## Overview

### Problem Statement
The application claims Dutch support, but the voice transcription service relies on Whisper's auto-detection (ignoring user language preference). Additionally, user-facing text in the dashboard (dates, "Total calories") is hardcoded in English, and translation files need parity verification.

### Solution
1. **Backend**: Strictly enforce user's selected language in `voice_service.py` by passing it to Whisper.
2. **Frontend**: Refactor `DailySummary.tsx` to use `next-intl` for date formatting and text (with pluralization).
3. **Parity**: Perform strict key-parity check using a script.
4. **Testing**: Add backend unit tests to verify language parameter passing.

### Scope
**In Scope:**
- Backend: `voice_service.py` (add required param), `nodes.py` (pass param).
- Frontend: `DailySummary.tsx` (localize dates & strings).
- I18n: Add missing keys (`dashboard.total` with pluralization, `dashboard.startTracking`) to `en.json` and `nl.json`.
- Verification: Script-based parity check, Backend unit test, End-to-end voice test.

**Out of Scope:**
- Adding support for languages other than Dutch and English.

## Context for Development

### Files to Reference

| Component | File | Status | Notes |
|Data| `backend/app/services/voice_service.py` | **Needs Mod** | Update `transcribe_audio` sig. |
|Data| `backend/app/agent/nodes.py` | **Needs Mod** | Pass `state.get('language')`. |
|UI| `frontend/components/features/logs/DailySummary.tsx` | **Needs Mod** | Fix hardcoded date/text. |
|I18n| `frontend/messages/*.json` | **Needs Mod** | Add keys & pluralization. |

### Technical Decisions
- **Date Formatting**: Use `new Date().toLocaleDateString(locale, ...)` where `locale` comes from `useLocale()`.
- **Whisper API**: Pass `language` param to force specific model usage. Make this parameter **Required** to avoid implicit defaults.
- **Pluralization**: Use ICU plural format for calories count.

## Implementation Plan

### 1. Update Voice Service
- [ ] **Task 1: Update `transcribe_audio` signature**
    - **File**: `backend/app/services/voice_service.py`
    - **Action**: Modify `transcribe_audio(..., language: str)` to make it **required**.
    - **Logic**: Pass `language` to `client.audio.transcriptions.create`. Remove default value to enforce explicit intent.

### 2. Update Agent Nodes
- [ ] **Task 2: Pass language from State**
    - **File**: `backend/app/agent/nodes.py`
    - **Action**: Extract `state.get("language", "nl")` and pass to `transcribe_audio`.

### 3. Update Translations for Dashboard
- [ ] **Task 3: Add `dashboard.total` and `dashboard.startTracking`**
    - **File**: `frontend/messages/en.json`
        - add `"total": "Total: {calories, plural, =0 {No calories} =1 {1 calorie} other {# calories}}"`
        - add `"startTracking": "Start tracking your meals"`
    - **File**: `frontend/messages/nl.json`
        - add `"total": "Totaal: {calories, plural, =0 {Geen calorieën} =1 {1 calorie} other {# calorieën}}"`
        - add `"startTracking": "Begin met het loggen van je maaltijden"`

### 4. Localize DailySummary
- [ ] **Task 4: Refactor `DailySummary.tsx`**
    - **File**: `frontend/components/features/logs/DailySummary.tsx`
    - **Action**:
        - Import `useLocale`, `useTranslations` from `next-intl`.
        - Replace `toLocaleDateString('en-US'...)` with `toLocaleDateString(locale...)`.
        - Replace hardcoded "Total..." with `t('dashboard.total', {calories: totalCalories})`.
        - Replace "Start tracking..." with `t('dashboard.startTracking')`.

### 5. Verification & Testing
- [ ] **Task 5: Parity Check Script**
    - **File**: `scripts/verify_i18n.py` (Create new)
    - **Action**: Script to load both JSONs and assert `set(en.keys()) == set(nl.keys())`. Run it.
- [ ] **Task 6: Backend Unit Test**
    - **File**: `backend/app/tests/services/test_voice_service.py` (Create/Update)
    - **Action**: Mock `AsyncOpenAI` and verify `transcribe_audio` calls it with `language='nl'`.

## Acceptance Criteria

### Backend Voice Logic
- [ ] **AC 1**: `transcribe_audio` raises TypeError if language is missing (static check) or enforced via strict typing.
- [ ] **AC 2**: Backend calls Whisper with `language='nl'` when Dutch is selected.
- [ ] **AC 3**: Unit test follows AC 2 pattern and passes.

### Frontend UI
- [ ] **AC 4**: Date in dashboard defaults to Dutch locale (e.g., "dinsdag 21 januari") when selected.
- [ ] **AC 5**: "Total: ... calories" appears as "Totaal: ... calorieën" in Dutch.
- [ ] **AC 6**: "1 calorie" is singular, "0" or "2+ calories" is plural (in both languages).

## Testing Strategy
1.  **Automated**:
    - Run `python scripts/verify_i18n.py` to ensure parity.
    - Run `pytest backend/app/tests/services/test_voice_service.py`.
2.  **Manual Verification**:
    - Login, toggle language to Dutch.
    - Record Voice: Verify backend logs show `language='nl'`.
