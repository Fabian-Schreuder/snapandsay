# Test Suite Documentation

This directory contains the End-to-End (E2E) test suite for Snap and Say, built with **Playwright**.

## Setup

1.  **Install Dependencies**:
    ```bash
    pnpm install
    ```

2.  **Environment Configuration**:
    Copy `.env.example` to `.env` and configure your environment variables:
    ```bash
    cp .env.example .env
    ```
    Ensure `BASE_URL` points to your running application (default: `http://localhost:3000`).

3.  **Install Browsers**:
    If this is your first time running Playwright, install the browser binaries:
    ```bash
    npx playwright install
    ```

## Running Tests

*   **Run all E2E tests**:
    ```bash
    pnpm test:e2e
    ```

*   **Run in UI mode** (Interactive):
    ```bash
    npx playwright test --ui
    ```

*   **Run in Headed mode** (Watch execution):
    ```bash
    npx playwright test --headed
    ```

*   **Debug mode**:
    ```bash
    npx playwright test --debug
    ```

*   **Show Report**:
    ```bash
    npx playwright show-report
    ```

## Architecture Overview

### Directory Structure
*   `tests/e2e/`: Contains the actual test files (`*.spec.ts`).
*   `tests/support/`: Contains shared infrastructure.
    *   `fixtures/`: Test fixtures that extend the base Playwright test object.
    *   `fixtures/factories/`: Data factories for generating test data (e.g., `UserFactory`).
    *   `helpers/`: Utility functions.

### Fixture Pattern
We use Playwright's fixture extension pattern to inject dependencies into tests.
Instead of importing `test` from `@playwright/test`, import it from `../support/fixtures`.

```typescript
import { test, expect } from '../support/fixtures';

test('example', async ({ page, userFactory }) => {
  // userFactory is available here
});
```

### Data Factories
We use the **Factory Pattern** to generate test data. Factories use `@faker-js/faker` to generate realistic random data and include an `auto-cleanup` mechanism.

**Example UserFactory:**
```typescript
const user = await userFactory.createUser(); // Creates user via API
// ... run test ...
// user is automatically deleted after test finishes
```

## Best Practices

1.  **Selectors**: Use `data-testid` attributes for stable selectors.
    *   Good: `page.getByTestId('submit-button')`
    *   Avoid: `page.locator('.btn-primary')`
2.  **Isolation**: Each test should be independent. Use factories to create fresh data for each test.
3.  **Network-First**: Mock or intercept network requests where appropriate to ensure determinism, but prefer real API calls for critical flows.
4.  **Artifacts**: Screenshots and videos are retained only on failure to save space.

## CI Integration
Tests are configured to run in CI with:
*   `forbidOnly`: Prevents committing focused tests (`test.only`).
*   `retries`: 2 retries on CI.
*   `workers`: 1 worker on CI (to avoid resource contention/flakiness).
