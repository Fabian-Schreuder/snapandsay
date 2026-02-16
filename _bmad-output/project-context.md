---
project_name: 'snapandsay'
user_name: 'Fabian'
date: '2026-02-16'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality_rules', 'workflow_rules', 'critical_rules']
status: 'complete'
rule_count: 48
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Frontend:** Next.js 15.5.9+ (App Router), React 19.1.1+, Tailwind CSS 3.4+, Shadcn/UI
    - *Constraint:* React 19 Compiler enabled; minimize manual memoization (`useMemo`, `useCallback`) unless necessary.
    - *Constraint:* Next.js 15 Async Request APIs: `cookies()`, `headers()`, and `params` are now **Promises** and must be awaited.
    - *Constraint:* strict `use client` boundaries for interactive components.
- **Backend:** Python 3.12+ (latest standard), FastAPI 0.115+, LangGraph 1.0+, SQLAlchemy 2.0+ (Async)
    - *Constraint:* `pydantic` v2.0+ (strict mode) required.
    - *Constraint:* `uv` package manager for deterministic builds.
- **Database:** Supabase PostgreSQL 15+
    - *Extension:* `vector` (pgvector) v0.5.0+ required.
    - *Constraint:* Schema managed by Supabase migrations, NOT by SQLAlchemy `metadata.create_all` in production/tests.
- **Infrastructure:**
    - Frontend: Vercel. Backend: Railway (Docker).
- **Package Managers:**
    - Frontend: `pnpm` — use `pnpm-lock.yaml` for reproducibility.
    - Backend: `uv` — use `uv sync` with `uv.lock` for deterministic builds.

## Critical Implementation Rules

### Language-Specific Rules

**TypeScript (Frontend):**
- **Strict Typing:** No `any`. Use `unknown` with narrowing if necessary. Explicit return types for all exported functions.
- **Next.js 15 Async Patterns:** `params`, `searchParams`, `cookies()`, and `headers()` are **Promises**. You MUST `await` them in Server Components and Route Handlers.
- **Imports:** Use `@/` alias for all local imports (e.g., `import { Button } from "@/components/ui/button"`).
- **Null Handling:** Prefer optional chaining (`?.`) and nullish coalescing (`??`) over explicit null checks.
- **Async Patterns:** Always use `async/await`. Avoid `.then()` chains.

**Python (Backend):**
- **Type Hints:** Mandatory for all function arguments and return values (including `None`). Use `typing.Annotated` for Dependency Injection.
- **Pydantic v2:** Use `model_validate` (NOT `parse_obj`), `field_validator` (NOT `validator`), and `ConfigDict(from_attributes=True)` for ORM mode.
- **Asyncio:** Use `async def` for all I/O bound operations. Prohibit blocking calls like `time.sleep` or synchronous `requests` (use `httpx`).
- **Docstrings:** Required for all public modules, classes, and functions (Google Style).

### Framework-Specific Rules

**Next.js (App Router):**
- **Server Components:** Default to Server Components. Use `use client` ONLY for interactivity (hooks, event listeners).
- **Data Fetching:** Fetch data in Server Components directly via `async/await`. Use Server Actions for mutations.
- **Shadcn/UI:** Do not modify `components/ui` primitives directly. Create wrapper components for custom logic.
- **Tailwind:** Use `cn()` from `lib/utils` for class merging. Avoid inline styles.
- **i18n:** Project uses `next-intl` for internationalization. All user-facing strings must use translation keys.
- **API Client:** Generated via `@hey-api/openapi-ts`. Run `pnpm generate-client` after backend API changes. Import from `app/openapi-client`.
- **State Management:** Use `@tanstack/react-query` for server state. Avoid global client state stores.

**FastAPI:**
- **Routers:** Use `APIRouter` for all endpoints, organized by domain in `backend/app/api/v1/endpoints`.
- **Dependency Injection:** Use `Depends()` for services, auth, and DB sessions via `get_async_session`.
- **Pydantic Models:** Separate `schemas` (API contracts in `app/schemas/`) from `models` (DB ORM in `app/models/`).
- **Error Handling:** Raise `HTTPException` with specific status codes. Do not return dictionaries for errors.
- **Config:** Use `pydantic-settings` (`app/config.py`). All env vars validated on startup. Access via the singleton `settings` object.

**LangGraph Agent:**
- **State:** Define agent state in `app/agent/state.py` using `TypedDict`.
- **Nodes:** Implement node functions in `app/agent/nodes.py` (and `ampm_nodes.py` for AMPM pass). Each node takes and returns state.
- **Graph:** Compile the graph in `app/agent/graph.py` using `StateGraph`. Use conditional edges in `routing.py`.
- **Constants:** Store prompt templates and configuration in `app/agent/constants.py`.

### Testing Rules

**Frontend (Jest + React Testing Library):**
- **Location:** Tests in `frontend/__tests__/` directory and co-located `*.test.tsx` files.
- **Environment:** `jsdom` (configured in `jest.config.ts`). Uses `jest.setup.ts` for setup.
- **Focus:** Test user interactions and accessibility (ARIA roles), not implementation details.
- **Mocks:** Mock all external API calls and complex hooks using `jest.mock`.
- **Path Aliases:** `@/` alias mapped in `jest.config.ts` via `moduleNameMapper`.

**Backend (Pytest):**
- **Location:** All tests in `backend/tests/`. Mirror app structure (e.g., `tests/agent/`, `tests/api/`, `tests/services/`).
- **Fixtures:** Use `conftest.py` for shared fixtures (`engine`, `db_session`, `test_client`).
- **Async:** `asyncio_mode = auto` in `pytest.ini`. All test functions can be `async def` without decorator.
- **Database:** Uses `TEST_DATABASE_URL`. Session fixture rolls back after each test. Schema managed by Supabase, not SQLAlchemy.
- **Test Client:** `httpx.AsyncClient` with `ASGITransport` for in-process API testing. Dependency overrides via `app.dependency_overrides`.

**E2E (Playwright):**
- **Location:** Root-level `pnpm test:e2e`. Configuration at project root.

### Code Quality & Style Rules

**Linting & Formatting:**
- **Frontend:** ESLint (Next.js Core Web Vitals + TypeScript + Prettier). Run `cd frontend && pnpm lint`.
- **Backend:** Ruff (linting & formatting, line-length 110). Run `cd backend && uv run ruff check .` and `uv run ruff format .`.

**Naming Conventions:**
- **Files:** `kebab-case` for frontend files (e.g., `user-profile.tsx`). `snake_case` for backend files (e.g., `auth_service.py`).
- **Variables/Functions:** `camelCase` (TS), `snake_case` (Python).
- **Classes/Components:** `PascalCase` (Both).
- **Constants:** `UPPER_SNAKE_CASE` (Both).

**Documentation:**
- **Comments:** Explain "Why", not "What".
- **TODOs:** Format as `# TODO(user): description`.

### Development Workflow Rules

**Git & Version Control:**
- **Branch Naming:** `type/description` (e.g., `feat/voice-input`, `fix/auth-error`).
- **Commit Messages:** Conventional Commits (e.g., `feat: add voice recorder component`).
- **PRs:** Squash and merge. Ensure CI passes.

**Environment Variables:**
- **Local:** `.env.local` (Frontend), `.env` (Backend). Never commit these.
- **Validation:** All env vars validated on startup — `zod` (TS), `pydantic-settings` (Python).

**Deployment:**
- **Frontend:** Auto-deploy to Vercel on push to `main`.
- **Backend:** Auto-deploy to Railway on push to `main`.

**Running Locally:**
- **From root:** `pnpm dev` runs both frontend and backend via `concurrently`.
- **Frontend only:** `cd frontend && pnpm dev`.
- **Backend only:** `cd backend && uv run uvicorn app.main:app --reload`.

### Critical Don't-Miss Rules

**Anti-Patterns to Avoid:**
- **Direct DB Access in API:** NEVER access the database directly in API routes. Always use the Service layer (`app/services/`).
- **Blocking Code:** NEVER use blocking I/O (e.g., `time.sleep`, `requests`) in async FastAPI endpoints. Use `asyncio.sleep` or `httpx`.
- **Secrets in Client:** NEVER expose API keys or secrets in Next.js Client Components.
- **SQLAlchemy Schema Management:** NEVER use `Base.metadata.create_all` for production or test DB schema. Schema is managed by Supabase migrations.

**Database & Connection Pooling:**
- **asyncpg + PgBouncer:** Use `NullPool` and `statement_cache_size=0` to avoid `DuplicatePreparedStatementError`. UUID-based prepared statement names are generated via `_generate_uuid_name` in `database.py`.
- **Supabase Migrations:** Database schema changes go through Supabase migration tooling, not SQLAlchemy.

**Security & Edge Cases:**
- **Input Validation:** Validate ALL inputs using Zod (Frontend) and Pydantic (Backend). Trust nothing.
- **Auth State:** Handle token expiration gracefully. JWT validation via `SUPABASE_JWT_SECRET`.
- **Rate Limiting:** Handle 429 errors from external APIs (Google Gemini, Supabase) with exponential backoff.
- **CORS:** Configured in `app/config.py` via `CORS_ORIGINS`. Allow only specific frontend domains.

---

## Usage Guidelines

**For AI Agents:**
- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**
- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-02-16
