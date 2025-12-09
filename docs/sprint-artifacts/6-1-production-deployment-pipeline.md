# Story 6.1: Production Deployment Pipeline

Status: in-progress

## Story

As a developer,
I want to set up the production deployment pipeline,
so that code changes are automatically deployed to the production environment.

## Acceptance Criteria

1. **Frontend Deployment:** The frontend (`/frontend`) is automatically deployed to Vercel when code is pushed to `main`.
2. **Backend Deployment:** The backend (`/backend`) is automatically deployed to Railway when code is pushed to `main`.
3. **Database Migration:** Database migrations are applied automatically during the backend deployment process.
4. **Environment Configuration:** Both Vercel and Railway environments have all necessary secrets (SUPABASE_URL, OPENAI_API_KEY, etc.) configured.
5. **Clean Up:** Unused deployment configuration files (e.g., `backend/vercel.json`) are removed to prevent confusion.

## Tasks / Subtasks

- [ ] Task 1: Frontend Vercel Setup (AC: 1, 4)
  - [x] Configure `frontend/vercel.json` to allow deployment on `main`.
  - [x] Set up Vercel Project (link to repo).
  - [x] Add Environment Variables to Vercel (SUPABASE_URL, SUPABASE_ANON_KEY, NEXT_PUBLIC_API_URL).
- [ ] Task 2: Backend Railway Setup (AC: 2, 3, 4)
  - [x] clean up `backend/vercel.json` (Delete).
  - [ ] Set up Railway Project (link to repo).
  - [ ] Configure Railway Service (Docker-based build using `backend/Dockerfile`).
  - [ ] Add Environment Variables to Railway (DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY, SECRET_KEY).
  - [ ] Configure `CORS_ORIGINS` in Railway with the Vercel production domain (e.g., `https://snapandsay.vercel.app`).
  - [x] Implement database table creation on startup (ensure `create_db_and_tables` from `app/database.py` is called via `main.py` lifespan or init script).
  - [x] Ensure `backend/start.sh` is executable (`git update-index --chmod=+x backend/start.sh`).
  - [ ] Verify `start.sh` executes correctly in Railway environment.
- [ ] Task 3: Verification (AC: 1, 2)
  - [ ] Trigger a deployment by pushing to `main`.
  - [ ] Verify Frontend can access Backend (CORS check).
  - [ ] Verify Backend can access Database.

## Dev Notes

- **Architecture Compliance:**
  - Frontend -> Vercel.
  - Backend -> Railway.
  - This adheres to the "Modular Monolith" strategy defined in `architecture.md`.

- **Source Tree Components:**
  - `frontend/vercel.json`
  - `backend/vercel.json` (DELETE)
  - `backend/Dockerfile`
  - `backend/start.sh`
  - `backend/app/database.py` (contains `create_db_and_tables`, currently unused)

### Project Structure Notes

- The monorepo structure requires careful configuration in deployment platforms.
- **Vercel:** Root Directory: `frontend`.
- **Railway:** Root Directory: `backend` (or set Root Directory in Railway settings).

### References

- [Architecture Document](docs/architecture.md) - Infrastructure & Deployment Section.
- [Backend Dockerfile](backend/Dockerfile).
- [Backend Start Script](backend/start.sh).

## Dev Agent Record

### Context Reference

### Agent Model Used

Antigravity (simulated SM agent)

### Completion Notes List

- Created primarily based on Architecture definition and existing Docker configuration.
- identified `backend/vercel.json` as likely dead code to be removed.
