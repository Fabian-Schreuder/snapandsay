# CI/CD Pipeline

This project uses GitHub Actions for Continuous Integration.

## Pipeline Stages

1.  **Lint**: Checks code quality (ESLint, Prettier).
2.  **Test**: Runs E2E tests in parallel (4 shards).
3.  **Burn-in**: Runs tests 10 times to detect flakiness (on PRs).
4.  **Report**: Aggregates results.

## Running Locally

To mirror the CI pipeline locally:

```bash
./scripts/ci-local.sh
```

To run burn-in locally:

```bash
./scripts/burn-in.sh 5 # Run 5 iterations
```

## Debugging Failures

-   **Artifacts**: Check the "Artifacts" section in GitHub Actions run for traces, screenshots, and videos of failed tests.
-   **Local Mirror**: Use `scripts/ci-local.sh` to reproduce failures locally.

## Secrets

See `docs/ci-secrets-checklist.md` for required secrets.
