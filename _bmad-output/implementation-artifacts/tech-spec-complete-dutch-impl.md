---
title: 'Complete Dutch Language Implementation'
slug: 'complete-dutch-impl'
created: '2026-01-21'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Next.js', 'Typescript', 'FastAPI', 'Python', 'next-intl']
files_to_modify: 
  - 'frontend/lib/api.ts'
  - 'frontend/hooks/use-agent.ts'
  - 'frontend/app/(dashboard)/snap/page.tsx'
  - 'tests/e2e/e6-language.spec.ts'
code_patterns: ['API Payload Extension', 'Hook Props Extension']
test_patterns: ['E2E Response Verification']
---

# Complete Dutch Language Implementation

## Overview
**Problem Statement**: While the backend is capable of generating Dutch responses and the frontend UI is localized, the frontend does not yet pass the user's language preference to the backend API during analysis requests.

**Solution**: Update the frontend API layer and `useAgent` hook to propagate the active locale to the backend `upload` and `stream` endpoints.

**Scope**:
- Frontend API client updates (`api.ts`).
- Agent hook updates (`use-agent.ts`).
- `SnapPage` integration (`page.tsx`).
- E2E test enhancement.

**Out of Scope**:
- New translations (assuming existing `nl.json` is sufficient for now).
- Backend logic changes (confirmed ready).

## Context for Development

### Backend Readiness
The backend `StreamAnalysisRequest` schema already accepts a `language` field (defaulting to "nl"). The `llm_service` uses this to instruct the LLM:
```python
lang_instruction = f"IMPORTANT: Respond entirely in {lang_name}. " if language != "en" else ""
```
This logic is sound and requires no changes.

### Frontend Gaps
1.  `analysisApi.upload` in `frontend/lib/api.ts` does not send `language`.
2.  `useAgent` hook's `startStreaming` function does not accept or send `language`.
3.  `SnapPage` does not retrieve the current locale to pass to these functions.

## Proposed Changes


### 1. Update API Client (`frontend/lib/api.ts`)
Modify `upload` payload to include `language`:
```typescript
upload: async (payload: {
    image_path: string;
    audio_path?: string | null;
    client_timestamp: string;
    client_timestamp: string;
    language: 'en' | 'nl'; // Strict typing
})
```

### 2. Update Agent Hook (`frontend/hooks/use-agent.ts`)
### 2. Update Agent Hook (`frontend/hooks/use-agent.ts`)
- Import `useLocale` from `next-intl`.
- Inside `useAgent`, call `const locale = useLocale();`.
- Pass this `locale` in the `fetch` body to `/api/v1/analysis/stream` inside `startStreamingInternal`.
- **Note**: `stream` request language takes precedence as it is the immediate user context, though `upload` also records it for the log.


### 3. Integrate in Snap Page (`frontend/app/(dashboard)/snap/page.tsx`)
- Use `useLocale()` from `next-intl`.
- Pass `locale` to `handleUpload` (which calls `api.upload`).
- `useAgent` automatically picks up locale from context, so no prop needed there.

## Verification Plan

### Automated Tests
- **Enhance `tests/e2e/e6-language.spec.ts`**:
    - Add a test case that mocks the backend response (or runs against real backend) to verify the agent's *thought* events come back in Dutch when the toggle is set to NL.
    - Use regex matching for robustness (e.g., `/maaltijd/i`, `/herkennen/i`) rather than brittle exact string matches.

### Manual Verification
1.  Set language to Dutch in Admin.
2.  Go to "Maaltijd vastleggen" (Snap).
3.  Upload an image.
4.  Verify "Thinking" steps are in Dutch ("Ingrediënten herkennen...", etc.).
5.  Verify final resultタイトル and synthesis are in Dutch.
