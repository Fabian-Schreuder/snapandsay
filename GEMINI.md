# Snap and Say - Gemini Context

## Project Overview

**Snap and Say** is a conversational dietary assessment tool designed for older adults (65+). It leverages Agentic AI to enable voice-first, conversational logging of meals. The system actively reasons about missing details and asks clarifying questions to ensure medical-grade data fidelity.

**Key Technologies:**
*   **Frontend:** Next.js 14+ (App Router), TypeScript, Tailwind CSS, Shadcn/UI.
*   **Backend:** Python 3.12+, FastAPI, LangGraph (Agent Orchestration).
*   **Database:** Supabase (PostgreSQL + pgvector).
*   **Package Managers:** `pnpm` (JavaScript/TypeScript), `uv` (Python).

## Architecture

*   **Monorepo:** Managed via `pnpm` workspaces.
*   **Frontend (`/frontend`):** Next.js PWA. Handles UI, Voice/Camera input, and SSE streaming from the agent.
*   **Backend (`/backend`):** FastAPI application. Hosts the LangGraph agent, API endpoints, and database interactions (SQLAlchemy + Pydantic).
*   **Documentation (`/docs`):** Extensive documentation including PRD, Architecture Decision Records (ADR), and user journeys.

## Building and Running

### Prerequisites
*   Node.js (via `.nvmrc`)
*   Python 3.12+
*   `pnpm`
*   `uv`

### Development
The project uses `concurrently` to run both services from the root.

```bash
# Install dependencies
pnpm install

# Start both frontend and backend
pnpm dev
```

### Individual Services

**Frontend:**
```bash
cd frontend
pnpm dev
```

**Backend:**
```bash
cd backend
uv run uvicorn app.main:app --reload
```

### Testing

**End-to-End (E2E):**
```bash
# Runs Playwright tests
pnpm test:e2e
```

**Frontend Unit Tests:**
```bash
cd frontend
pnpm test
```

**Backend Unit Tests:**
```bash
cd backend
uv run pytest
```

### Code Quality & Maintenance

**Linting:**
*   **Frontend:** `cd frontend && pnpm lint` (ESLint)
*   **Backend:** `cd backend && uv run ruff check .` (Ruff)

**Client Generation:**
To regenerate the TypeScript API client after backend changes:
```bash
cd frontend
pnpm generate-client
```

## Conventions

### Coding Style
*   **Python:** Follow `snake_case` for variables/functions. Use `ruff` for linting/formatting.
*   **TypeScript:** Follow `camelCase` for variables/functions, `PascalCase` for components. Use `eslint` and `prettier`.
*   **Commits:** Use clear, descriptive commit messages.

### Architecture Patterns
*   **Privacy First:** User data is de-identified. No PII is stored centrally.
*   **Agentic Workflow:** The backend uses LangGraph to orchestrate the "Reason -> Clarify -> Log" loop.
*   **Streaming:** Agent responses are streamed via Server-Sent Events (SSE) to the frontend.
*   **Type Safety:** End-to-end type safety using Pydantic (Backend) and Zod/Generated Types (Frontend).
