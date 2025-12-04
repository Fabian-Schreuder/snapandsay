# Story 1.1: Project Initialization & Repo Setup

Status: ready-for-dev

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
5.  **And** The project is runnable locally with `npm run dev`

## Tasks / Subtasks

- [ ] Task 1: Initialize Repository & Template (AC: 1, 2)
    - [ ] Clone `vintasoftware/nextjs-fastapi-template`
    - [ ] **CRITICAL:** Remove `fastapi-users` dependency and related code (we use Supabase Auth)
    - [ ] Remove demo components and example routes
    - [ ] Initialize git and create `.gitignore`
- [ ] Task 2: Restructure Backend (AC: 3)
    - [ ] Create `backend/app/agent/` (for LangGraph)
    - [ ] Create `backend/app/services/` (for business logic)
    - [ ] Create `backend/app/core/` (for config/security)
    - [ ] Create `backend/app/db/` (for session/base)
    - [ ] Add `langgraph` to `backend/requirements.txt`
- [ ] Task 3: Setup Supabase & Environment (AC: 5)
    - [ ] Create `supabase/config.toml` for local dev
    - [ ] Create `supabase/migrations/` directory
    - [ ] Configure `frontend` and `backend` to run concurrently
- [ ] Task 4: Setup Quality Tools (AC: 4)
    - [ ] Configure `ruff` for Python backend
    - [ ] Configure `eslint` for Next.js frontend

## Dev Notes

- **Template Source:** `https://github.com/vintasoftware/nextjs-fastapi-template`
- **Auth Strategy:**
    - **REMOVE** `fastapi-users`. The template uses it, but our Architecture mandates **Supabase Auth**.
    - We will implement custom JWT middleware in a later story, but for now, ensure the conflicting library is gone.
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

### Completion Notes List

- [ ] Confirmed `fastapi-users` removal
- [ ] Verified backend structure matches Architecture
- [ ] Verified local run
