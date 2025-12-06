# Epic 1 Retrospective: Foundation & Core Infrastructure

**Date:** 2025-12-06
**Participants:** Fabian (Project Lead), Bob (Scrum Master), Alice (PO), Charlie (Senior Dev), Dana (QA), Elena (Junior Dev)
**Epic Status:** Complete (100%)

## Executive Summary

Epic 1 successfully established the "Foundation" for Snap and Say. We delivered a clean, architecture-compliant specific implementation of Next.js and FastAPI, integrated with Supabase. While we faced friction "un-building" the opinionated boilerplate of the starter template and navigating Supabase security nuances, the adversarial code review process caught critical issues before they reached "Done."

## Metrics

| Metric | Value | Notes |
| :--- | :--- | :--- |
| **Stories Completed** | 3 / 3 | 100% Completion |
| **Critical Bug Fixes** | ~4 | Caught in Review (Race conditions, JWT Secret, Default Configs) |
| **Velocity Impact** | Medium | Template cleanup slowed down initial setup |

## What Went Well (Wins)

*   **Critical Fixes:** The review process prevented serious bugs (e.g., `AuthGuard` race condition, `SUPABASE_JWT_SECRET` misuse) from shipping.
*   **Architecture Alignment:** We successfully stripped the template of `fastapi-users` and `alembic` to match our "Supabase Native" architecture.
*   **Foundation Quality:** We have a robust, linted, and type-checked repo (Ruff, ESLint) that is "built on rock, not sand."

## Challenges (Friction)

*   **Template Deviation:** "Fighting the starter kit" was a major time sink. untangling dependencies took longer than building from scratch in some areas.
*   **Test Environment:** Setting up `pytest` to play nicely with a local Supabase instance (and RLS policies) was complex and required siginificant effort in Story 1.2.
*   **Security Nuances:** Differentiating between `SUPABASE_KEY` (Anon) and `SUPABASE_JWT_SECRET` (Service) caused initial confusion in Story 1.3.

## Key Insights & Patterns

*   **"Batteries Included" Trap:** Using a heavy template (Next.js + FastAPI) caused more work than it saved because we had to remove half the "batteries."
*   **Adversarial Review Value:** The "Round 3" reviews are catching high-value issues that standard reviews miss. This is a keeper.
*   **Security First:** Auth and RLS cannot be an afterthought; they require precise configuration in the "Foundation" phase.

## Action Items

| ID | Action | Owner | Priority | Status |
| :--- | :--- | :--- | :--- | :--- |
| **AI-1** | **Create "Spike 2.0"** to prototype Camera/Mic capture before starting Story 2.1 implementation. | Charlie | **Critical** | New |
| **AI-2** | **Maintain Adversarial Reviews** for Epic 2, focusing on "Media Upload" security (file types, size limits). | Dana | High | Ongoing |
| **AI-3** | **Update Documentation** to explicitly document the `SUPABASE_JWT_SECRET` vs `ANON_KEY` distinction for future devs. | Charlie | Medium | To Do |

## Next Steps (Epic 2 Prep)

We have decided to **PAUSE** the direct start of Story 2.1 to conduct a technical **SPIKE** first.

*   **Risk:** Browser hardware permissions (Camera/Mic) vary wildly across devices and contexts (PWA vs Web).
*   **Plan:** Execute "Spike 2.0" to validate `MediaRecorder` API and Supabase Storage upload flow.
