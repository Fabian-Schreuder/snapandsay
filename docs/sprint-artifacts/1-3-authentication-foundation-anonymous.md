# Story 1.3: Authentication Foundation (Anonymous)

Status: ready-for-review

## Story

As a user,
I want to use the app without creating an account (Anonymous Login),
so that I can start logging immediately without friction.

## Acceptance Criteria

1.  **Given** I am a new user opening the app
    **When** The app loads
    **Then** I am automatically signed in anonymously via Supabase Auth
    **And** A unique User ID is generated and stored
    **And** My session persists across reloads

2.  **Given** I am a returning user
    **When** I reopen the app
    **Then** I remain logged in with the same User ID (session persistence)

3.  **Given** I try to access protected routes (e.g., `/app/snap`)
    **When** I am not authenticated
    **Then** I am redirected to the login process (or auto-logged in)

4.  **Given** The backend receives a request
    **When** The request contains a valid Supabase JWT
    **Then** The backend verifies the token using `HS256` algorithm and `SUPABASE_JWT_SECRET`
    **And** The extracted User ID matches the authenticated user context

## Tasks / Subtasks

- [x] Frontend: Implement Anonymous Auth
    - [x] Create/Update `src/lib/supabase.ts` to expose `signInAnonymously`.
    - [x] Update `src/app/(auth)/login/page.tsx` (or root layout) to trigger auto-login on mount if no session.
    - [x] Implement `src/middleware.ts` using `@supabase/ssr` `createServerClient` to handle cookie persistence and route protection.
- [x] Backend: Implement Auth Middleware
    - [x] Add `SUPABASE_JWT_SECRET` to `app/core/config.py` (Required).
    - [x] Create `app/core/security.py` handling JWT verification using `PyJWT` with `HS256` algorithm.
    - [x] Create Pydantic model `UserContext` (id: UUID, aud: str, role: str) for type-safe user object.
    - [x] Implement `get_current_user` dependency in `app/api/v1/endpoints/auth.py` (or shared dependency).
- [x] Database: Verify Users Table (covered in Story 1.2, but verify access)
    - [x] Ensure RLS policies allow anonymous users to Insert/Select their own rows.

## Dev Notes

- **Architecture Compliance**:
    - **Frontend**: Use `src/lib/supabase.ts` singleton. Use `@supabase/ssr` for middleware cookie handling.
    - **Backend**: **CRITICAL**: Use `SUPABASE_JWT_SECRET` (from Supabase Project Settings -> API) for verification, NOT the `SUPABASE_KEY` (Anon Key).
    - **Security**: Algorithm must be `HS256`.
- **Environment Variables**:
    - `NEXT_PUBLIC_SUPABASE_URL`
    - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
    - `SUPABASE_JWT_SECRET` (Backend Only - Critical for verification)
- **Supabase Auth**:
    - `supabase.auth.signInAnonymously()` is the native method.
- **Testing**:
    - **Frontend**: Manual test - Clear storage -> Reload -> Check LocalStorage/Cookies.
    - **Backend**:
        - Pass: Curl with valid Bearer token signed with JWT secret.
        - Fail: Curl with Anon Key as Bearer token (Should fail validation).

### Project Structure Notes

- **Frontend**: `src/lib/supabase.ts` should already exist. `src/middleware.ts` is critical for PWA peristence.
- **Backend**: `app/core/security.py` is the standard place for JWT logic.

### References

- [Epics: Story 1.3](docs/epics.md#story-13-authentication-foundation-anonymous)
- [PRD: FR1, FR2, FR3](docs/prd.md#1-authentication--identity)
- [Architecture: Auth & Security](docs/architecture.md#authentication--security)

## Dev Agent Record

### Context Reference

- `docs/epics.md`
- `docs/prd.md`
- `docs/architecture.md`
- `docs/ux-design-specification.md`

### Agent Model Used

- **Model**: Gemini 2.0 Flash (Antigravity)
- **Role**: Technical Scrum Master (Bob)

### Completion Notes List

- Ensure `@supabase/ssr` is properly installed (`npm install @supabase/ssr`) for Next.js middleware compatibility.
- Backend verification must explicitly check `aud=authenticated` (or relevant audience) if distinguishing anon vs auth users matters later, though both use same audience usually.
- Implemented `AuthGuard` in `layout.tsx` to handle auto-login for all pages.
- Created `backend/app/api/deps.py` for shared `get_current_user` dependency.
- Backend tests added in `backend/tests/test_auth.py` covering JWT verification.

### File List

- `frontend/lib/supabase.ts`
- `frontend/middleware.ts`
- `frontend/components/AuthGuard.tsx`
- `frontend/app/layout.tsx`
- `backend/app/config.py`
- `backend/app/core/security.py`
- `backend/app/api/deps.py`
- `backend/tests/test_auth.py`
- `backend/pyproject.toml`
- `frontend/package.json`

