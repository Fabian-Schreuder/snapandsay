# Test Plan: Epic 1 - Foundation

**Version:** 1.0
**Date:** 2025-12-10
**Author:** Antigravity (Test Design Agent)
**Status:** Draft

## 1. Introduction

This test plan covers the validation of **Epic 1: Foundation**, specifically focusing on **Story 1.3: Authentication Foundation (Anonymous)**. The goal is to ensure the anonymous authentication mechanism works correctly, session persistence is reliable, and users can access the application without friction.

**Scope:**
- **In Scope:**
    - Anonymous Sign-in functionality (Frontend & Backend integration).
    - Session persistence across page reloads.
    - Automatic user creation (Supabase Triggers).
    - Protected route handling (Middleware).
- **Out of Scope:**
    - Deployment pipelines (Story 1.1 - Verified separately).
    - Database schema validation (Story 1.2 - Verified separately).
    - Social login or Email login (Future Epics).

## 2. Test Objectives

- Verify that a new user is automatically authenticated anonymously upon visiting the app.
- Verify that a unique User ID and Anonymous ID are generated and stored.
- Verify that the session persists after reloading the page.
- Verify that the application gracefully handles lack of credentials by signing in.

## 3. Test Strategy

**Level:** System-Level / E2E
**Tool:** Playwright (TypeScript)
**Environment:** Local Development (handling Supabase Local Instance)

### 3.1 Test Data
- **New User:** Simulated by a fresh browser context (cleared storage).
- **Returning User:** Simulated by reusing the state of a previous browser context.

## 4. Test Scenarios

### TS-1.3.1: Anonymous Auto-Login (Happy Path)
**Description:** Verify a new user is automatically signed in when visiting the landing page.
- **Pre-conditions:** No active session (fresh context).
- **Steps:**
    1. Navigate to the application root (`/`).
    2. Wait for the application to load.
- **Expected Results:**
    1. User is signed in (check Supabase session).
    2. LocalStorage/Cookies contain Supabase auth tokens.
    3. UI does not show "Sign In" prompts (if any).

### TS-1.3.2: User Persistence
**Description:** Verify the user identity remains the same after a page reload.
- **Pre-conditions:** User is signed in (from TS-1.3.1).
- **Steps:**
    1. Capture the current User ID / Anonymous ID.
    2. Reload the page.
    3. Capture the User ID again.
- **Expected Results:**
    1. User ID matches the ID captured before reload.
    2. No new user record is created in the backend (optional validation if observable).

### TS-1.3.3: Middleware Protection
**Description:** Verify that accessing a restricted page triggers the auth flow (auto-login).
- **Pre-conditions:** No active session.
- **Steps:**
    1. Navigate directly to a protected route (e.g., `/app/snap` - assuming it exists or uses the layout).
- **Expected Results:**
    1. Request is intercepted.
    2. Auto-login occurs.
    3. User effectively lands on the requested page (or redirected appropriately after login).

## 5. Risk Assessment Matrix

| ID | Risk Description | Probability | Impact | Mitigation Strategy |
|----|------------------|-------------|--------|---------------------|
| R1 | **Supabase Service Down:** Auth fails entirely. | Low (Managed) | High | Implement error boundary in UI; Manual test blocking case. |
| R2 | **LocalStorage cleared:** User loses "account". | Medium | High | "By Design" for anonymous users. Scope is to ensure it *re-creates* a new account seamlessly. |
| R3 | **Race Condition:** Double sign-in on fast reloads. | Low | Low | Backend triggers handle uniqueness; Frontend `AuthGuard` debouncing (already implemented). |
| R4 | **Token Expiry:** Session expires while using. | Medium | Medium | Verify silent refresh logic in Supabase client. |

## 6. Execution Plan

- **Automated:**
    - Create `tests/e2e/e1-auth.spec.ts`.
    - Implement scenarios using `test`, `expect`, and fixture factories.
- **Manual:**
    - Clear application data in DevTools -> Reload -> Verify persistence.

## 7. Deliverables
- `tests/e2e/e1-auth.spec.ts` (Code)
- Execution Report (Post-execution)
