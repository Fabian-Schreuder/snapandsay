# System-Level Test Design: Snap and Say

## 1. Introduction
This document defines the comprehensive test strategy for "Snap and Say," a conversational dietary assessment tool for older adults. It aligns with the project's architectural requirements (Next.js, FastAPI, LangGraph) and strict NFRs (Medical-grade fidelity, HIPAA compliance, WCAG AAA accessibility).

## 2. Testability Assessment

### Controllability: PASS
*   **Database**: Supabase allows programmatic reset and seeding via API/CLI for test isolation.
*   **Auth**: Anonymous auth (UUIDs) simplifies user creation without complex 3rd party flows.
*   **Time**: Date/Time mocking is possible in both Jest/Vitest and Python.

### Observability: PASS
*   **Logging**: Structured logging (JSON) in Backend allows parsing logs during tests.
*   **Tracing**: LangSmith integration (planned) will provide visibility into Agent reasoning steps.
*   **Frontend**: React DevTools and Playwright Traces provide deep UI state visibility.

### Reliability: PASS
*   **Isolation**: Tests can run in parallel (sharded) with unique user sessions.
*   **Determinism**: "Thinking" states are deterministic in logic, though LLM outputs vary (mitigated by mocking LLM responses in lower-level tests).

## 3. Architecturally Significant Requirements (ASRs)

| ASR ID | Requirement | Risk Score | Test Strategy |
| :--- | :--- | :--- | :--- |
| **ASR-01** | **Medical-Grade Fidelity**: Data must be accurate; no hallucinations. | **9 (Critical)** | Unit tests for prompts; E2E for clarification loops. |
| **ASR-02** | **HIPAA Compliance**: No PII in logs; de-identified storage. | **9 (Critical)** | Automated security scans; Data leakage integration tests. |
| **ASR-03** | **Accessibility (WCAG AAA)**: Usable by older adults (low vision/motor). | **9 (Critical)** | Automated Axe scans + Manual screen reader verification. |
| **ASR-04** | **Offline Resilience**: Must queue data when offline. | **6 (High)** | Playwright network emulation (Offline mode). |

## 4. Test Levels Strategy

*   **Unit Tests (L1): 60%**
    *   *Rationale*: Complex business logic (nutritional parsing, agent state machines) resides in backend functions. Fast feedback is crucial.
    *   *Tools*: Pytest (Backend), Vitest (Frontend).
*   **Integration Tests (L2): 30%**
    *   *Rationale*: Critical interactions between Next.js <-> FastAPI and FastAPI <-> Supabase.
    *   *Tools*: Pytest + TestClient, Playwright Component Tests.
*   **E2E Tests (L3): 10%**
    *   *Rationale*: Focus on critical user journeys (Onboarding, Logging, History) to verify the whole system. Expensive but necessary for "Agentic" flows.
    *   *Tools*: Playwright.

## 5. NFR Testing Approach

*   **Security**:
    *   *Auth*: Verify session expiry and anonymous token generation.
    *   *Privacy*: SQL checks to ensure no PII is persisted in plain text.
    *   *Tools*: Pytest, OWASP ZAP (optional later).
*   **Performance**:
    *   *Latency*: Measure "Time to Thinking" (<1.5s) and "Time to Response".
    *   *Load*: Simulate 50 concurrent users logging meals.
    *   *Tools*: k6, Playwright.
*   **Reliability**:
    *   *Offline*: Verify queueing and syncing mechanisms.
    *   *Error Handling*: Verify graceful degradation on API failures.
    *   *Tools*: Playwright (Network Interception).
*   **Maintainability**:
    *   *Coverage*: Enforce >80% code coverage on Backend.
    *   *Linting*: Strict ESLint/Ruff rules.
    *   *Tools*: SonarQube (or similar CI step), Pre-commit hooks.

## 6. Test Environment Requirements
*   **CI Environment**: GitHub Actions with access to Supabase Staging (or local Dockerized Supabase).
*   **Local**: Docker Compose for full stack (Frontend + Backend + DB).
*   **Secrets**: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `OPENAI_API_KEY` (mocked where possible).

## 7. Testability Concerns
*   **LLM Determinism**: Agent outputs can vary.
    *   *Mitigation*: Mock LLM calls in Unit/Integration tests. Use "Evals" for prompt quality, separate from functional tests.
*   **Voice Input**: Hard to automate real voice input.
    *   *Mitigation*: Inject pre-recorded audio files in Playwright tests.

## 8. Recommendations for Sprint 0
1.  **Scaffold Test Frameworks**: Initialize Playwright and Pytest configurations.
2.  **CI Pipeline**: Set up GitHub Actions for automated testing on PRs.
3.  **Base Fixtures**: Create `UserFactory` and `MealLogFactory` for easy test data generation.
