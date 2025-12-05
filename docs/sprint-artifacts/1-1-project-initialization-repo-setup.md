# Story 1.1: Project Initialization & Repo Setup

Status: Done

## Story

As a developer,
I want to initialize the project repository with the correct structure and dependencies,
so that the team can start building on a solid foundation.

## Acceptance Criteria

1.  **Given** I have the necessary permissions
    **When** I initialize the repository
    **Then** The project structure matches the Architecture definition (frontend/backend separation)
2.  **And** The `vintasoftware/nextjs-fastapi-template` is cloned and cleaned of unused boilerplate (specifically `fastapi-users`)
3.  **And** The backend directory structure includes `agent`, `services`, `core`, and `db` modules
4.  **And** CI/CD workflows are configured for linting (ESLint, Ruff)
5.  **And** The project is runnable locally with `pnpm run dev`

## Tasks / Subtasks

- [x] Task 1: Initialize Repository & Template (AC: 1, 2)
    - [x] Clone `vintasoftware/nextjs-fastapi-template`
    - [x] **CRITICAL:** Remove `fastapi-users` dependency and related code (we use Supabase Auth)
    - [x] **CRITICAL:** Remove Alembic configuration (`alembic.ini`, `migrations/` folder) - we use Supabase migrations
    - [x] Remove demo components and example routes
    - [x] Initialize git and create `.gitignore`
- [x] Task 2: Restructure Backend (AC: 3)
    - [x] Create `backend/app/agent/` (for LangGraph)
    - [x] Create `backend/app/services/` (for business logic)
    - [x] Create `backend/app/core/` (for config/security)
    - [x] Create `backend/app/db/` (for session/base)
    - [x] Add `langgraph` dependency (ensure `uv` is used for package management)
- [x] Task 3: Setup Supabase & Environment (AC: 5)
    - [x] Create `supabase/config.toml` for local dev
    - [x] Create `supabase/migrations/` directory
    - [x] Configure `frontend` and `backend` to run concurrently
- [x] Task 4: Setup Quality Tools (AC: 4)
    - [x] Configure `ruff` for Python backend
    - [x] Configure `eslint` for Next.js frontend

### Review Follow-ups (AI)

- [x] [AI-Review][CRITICAL] Fix git untracked files (backend, frontend, supabase)
- [x] [AI-Review][HIGH] Fix hollow application (wire up API router in main.py)
- [x] [AI-Review][MEDIUM] Fix architecture mismatch (move API to v1/endpoints)
- [x] [AI-Review][VERIFICATION] Add health check endpoint and tests

## Dev Notes

- **Template Source:** `https://github.com/vintasoftware/nextjs-fastapi-template`
- **Auth Strategy:**
    - **REMOVE** `fastapi-users`. The template uses it, but our Architecture mandates **Supabase Auth**.
    - **Check specific files for cleanup:** `backend/app/api/deps.py`, `backend/app/core/security.py`, `backend/app/models/user.py`.
    - We will implement custom JWT middleware in a later story, but for now, ensure the conflicting library is gone.
- **Tooling Standards:**
    - **Frontend:** Use `pnpm` exclusively (do not use `npm` or `yarn`).
    - **Backend:** Use `uv` for dependency management.
- **Architecture Alignment:**
    - **Backend Structure:** Must strictly follow `docs/architecture.md`.
        - `app/agent`: LangGraph definitions.
        - `app/services`: Service layer (e.g. `llm_service.py`).
    - **Dependencies:** Add `langgraph` now to ensure compatibility.

### Project Structure Notes

- **Root:** `snapandsay/`
- **Frontend:** `snapandsay/frontend/`
- **Backend:** `snapandsay/backend/`
- **Supabase:** `snapandsay/supabase/`

### References

- [Architecture: Project Structure](docs/architecture.md#complete-project-directory-structure)
- [Architecture: Technology Stack](docs/architecture.md#technical-constraints--dependencies)
- [Epics: Story 1.1](docs/epics.md#story-11-project-initialization--repo-setup)

## Dev Agent Record

### Context Reference

- **Architecture:** `docs/architecture.md`
- **Epics:** `docs/epics.md`

### Agent Model Used

- Agentic Mode (Sm Agent)

### One-Shot File List

#### [MODIFY] [pyproject.toml](file:///home/fabian/dev/work/snapandsay/backend/pyproject.toml)
#### [MODIFY] [config.py](file:///home/fabian/dev/work/snapandsay/backend/app/config.py)
#### [MODIFY] [models.py](file:///home/fabian/dev/work/snapandsay/backend/app/models.py)
#### [MODIFY] [email.py](file:///home/fabian/dev/work/snapandsay/backend/app/email.py)
#### [MODIFY] [conftest.py](file:///home/fabian/dev/work/snapandsay/backend/tests/conftest.py)
#### [MODIFY] [test_database.py](file:///home/fabian/dev/work/snapandsay/backend/tests/test_database.py)
#### [MODIFY] [test_email.py](file:///home/fabian/dev/work/snapandsay/backend/tests/test_email.py)
#### [DELETE] [alembic.ini](file:///home/fabian/dev/work/snapandsay/backend/alembic.ini)
#### [DELETE] [test_main.py](file:///home/fabian/dev/work/snapandsay/backend/tests/main/test_main.py)
#### [DELETE] [test_items.py](file:///home/fabian/dev/work/snapandsay/backend/tests/routes/test_items.py)
#### [NEW] [config.toml](file:///home/fabian/dev/work/snapandsay/supabase/config.toml)
#### [NEW] [test_cleanup.py](file:///home/fabian/dev/work/snapandsay/backend/tests/test_cleanup.py)
#### [NEW] [test_task2.py](file:///home/fabian/dev/work/snapandsay/backend/tests/test_task2.py)
#### [NEW] [health.py](file:///home/fabian/dev/work/snapandsay/backend/app/api/v1/endpoints/health.py)
#### [NEW] [api.py](file:///home/fabian/dev/work/snapandsay/backend/app/api/v1/api.py)
#### [NEW] [test_health.py](file:///home/fabian/dev/work/snapandsay/backend/tests/api/v1/test_health.py)
#### [MODIFY] [main.py](file:///home/fabian/dev/work/snapandsay/backend/app/main.py)

### Completion Notes List

- [x] Confirmed `fastapi-users` removal
- [x] Verified backend structure matches Architecture
- [x] Verified local run
- [x] Installed `langgraph` dependency
- [x] Created `supabase/config.toml`
- [x] Cleaned up demo tests and components
