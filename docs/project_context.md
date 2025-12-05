---
project_name: 'snapandsay'
user_name: 'Fabian'
date: '2025-12-04'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality_rules', 'workflow_rules', 'critical_rules']
status: 'complete'
rule_count: 42
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Frontend:** Next.js 14.2+ (App Router, Server Actions enabled), React 18.3+, Tailwind CSS 3.4+, Shadcn/UI (latest)
    - *Constraint:* Must use `lucide-react` for icons.
    - *Constraint:* Strict `use client` directives for interactive components.
- **Backend:** Python 3.11+ (Required for optimized LangGraph async support), FastAPI 0.110+, LangGraph 0.1.5+, SQLAlchemy 2.0+ (Async only)
    - *Constraint:* `pydantic` v2.0+ required (strict mode).
- **Database:** Supabase PostgreSQL 15+
    - *Extension:* `vector` (pgvector) v0.5.0+ required for HNSW indexes.
- **Infrastructure:**
    - Frontend: Vercel (Edge Runtime compatible preferred).
    - Backend: Railway (Docker-based deployment).
- **Package Managers:**
    - Frontend: `pnpm` (latest) - *Constraint:* Use `pnpm-lock.yaml` for reproducibility.
    - Backend: `uv` (latest) - *Constraint:* Use `uv sync` with `uv.lock` for deterministic builds.

## Critical Implementation Rules

### Language-Specific Rules

**TypeScript (Frontend):**
- **Strict Typing:** No `any`. Use `unknown` with narrowing if necessary. Explicit return types for all exported functions.
- **Async Patterns:** Always use `async/await`. Avoid `.then()` chains.
- **Imports:** Use `@/` alias for all local imports (e.g., `import { Button } from "@/components/ui/button"`).
- **Null Handling:** Prefer optional chaining (`?.`) and nullish coalescing (`??`) over explicit null checks.

**Python (Backend):**
- **Type Hints:** Mandatory for all function arguments and return values (including `None`).
- **Pydantic v2:** Use `model_validate` instead of `parse_obj`. Use `field_validator` instead of `validator`.
- **Asyncio:** Use `async def` for all I/O bound operations (Database, External APIs).
- **Docstrings:** Required for all public modules, classes, and functions (Google Style).

### Framework-Specific Rules

**Next.js (App Router):**
- **Server Components:** Default to Server Components. Use `use client` ONLY for interactivity (hooks, event listeners).
- **Data Fetching:** Fetch data in Server Components directly via `async/await`. Use Server Actions for mutations.
- **Shadcn/UI:** Do not modify `components/ui` primitives directly. Create wrapper components for custom logic.
- **Tailwind:** Use `cn()` utility for class merging. Avoid inline styles.

**FastAPI:**
- **Routers:** Use `APIRouter` for all endpoints, organized by domain in `backend/app/api/v1/endpoints`.
- **Dependency Injection:** Use `Depends()` for services, auth, and DB sessions.
- **Pydantic Models:** Separate `schemas` (API) from `models` (DB). Use `ConfigDict(from_attributes=True)` for ORM mode.
- **Error Handling:** Raise `HTTPException` with specific status codes. Do not return dictionaries for errors.

### Testing Rules

**Frontend (Jest/React Testing Library):**
- **Location:** Co-locate tests with components in `__tests__` directory or `Component.test.tsx`.
- **Focus:** Test user interactions and accessibility (ARIA roles), not implementation details.
- **Mocks:** Mock all external API calls and complex hooks using `jest.mock`.

**Backend (Pytest):**
- **Location:** All tests in `backend/tests/`. Mirror app structure.
- **Fixtures:** Use `conftest.py` for shared fixtures (DB session, AsyncClient).
- **Async:** Use `pytest-asyncio` for all async route/service tests.
- **Database:** Use a separate test database or transaction rollbacks. Never test against dev DB.

### Code Quality & Style Rules

**Linting & Formatting:**
- **Frontend:** ESLint (Next.js Core Web Vitals) + Prettier. Run `pnpm lint` before commit.
- **Backend:** Ruff (Linting & Formatting). Run `ruff check .` and `ruff format .`.

**Naming Conventions:**
- **Files:** `kebab-case` for all files (e.g., `user-profile.tsx`, `auth_service.py`).
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
- **PRs:** Squash and merge. Ensure CI passes before requesting review.

**Environment Variables:**
- **Local:** `.env.local` (Frontend), `.env` (Backend). Never commit these.
- **Validation:** Validate all env vars on startup (using `zod` for TS, `pydantic-settings` for Python).

**Deployment:**
- **Frontend:** Auto-deploy to Vercel on push to `main`.
- **Backend:** Auto-deploy to Railway on push to `main`.

### Critical Don't-Miss Rules

**Anti-Patterns to Avoid:**
- **Direct DB Access in API:** NEVER access the database directly in API routes. Always use the Service layer.
- **Blocking Code:** NEVER use blocking I/O (e.g., `time.sleep`, `requests`) in async FastAPI endpoints. Use `asyncio.sleep` or `httpx`.
- **Secrets in Client:** NEVER expose API keys or secrets in Next.js Client Components.

**Security & Edge Cases:**
- **Input Validation:** Validate ALL inputs using Zod (Frontend) and Pydantic (Backend). Trust nothing.
- **Auth State:** Handle token expiration gracefully. Implement silent refresh logic.
- **Rate Limiting:** Handle 429 errors from external APIs (OpenAI, Supabase) with exponential backoff.
- **CORS:** Configure strict CORS in FastAPI. Allow only the specific frontend domain.

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

Last Updated: 2025-12-04
