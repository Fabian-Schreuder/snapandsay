---
project_name: 'snapandsay'
user_name: 'Fabian'
date: '2026-02-16'
sections_completed: ['technology_stack']
existing_patterns_found: 7
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Frontend:** Next.js 15.5.9+ (App Router), React 19.1.1+, Tailwind CSS 3.4+, Shadcn/UI
    - *Constraint:* React 19 Compiler enabled; minimize manual memoization (`useMemo`, `useCallback`) unless necessary.
    - *Constraint:* Next.js 15 Async Request APIs: `cookies()`, `headers()`, and `params` are now **Promises** and must be awaited.
    - *Constraint:* strict `use client` boundaries for interactive components.
- **Backend:** Python 3.12+ (latest standard), FastAPI 0.115+, LangGraph 0.2+, SQLAlchemy 2.0+ (Async)
    - *Constraint:* `pydantic` v2.0+ (strict mode) required.
    - *Constraint:* `uv` package manager for deterministic builds.
- **Database:** Supabase PostgreSQL 15+
    - *Extension:* `vector` (pgvector) v0.5.0+ required.
- **Tools:** Use `pnpm` (Frontend) and `uv` (Backend).

## Critical Implementation Rules

### Language-Specific Rules

_Documented after discovery phase_

### Framework-Specific Rules

_Documented after discovery phase_

### Testing Rules

_Documented after discovery phase_

### Code Quality & Style Rules

_Documented after discovery phase_

### Development Workflow Rules

_Documented after discovery phase_

### Critical Don't-Miss Rules

_Documented after discovery phase_
