# 🔥 CODE REVIEW FINDINGS

**Story:** `docs/sprint-artifacts/1-3-authentication-foundation-anonymous.md`
**Git vs Story Discrepancies:** 0 found
**Issues Found:** 0 High, 3 Medium, 2 Low

## 🟡 MEDIUM ISSUES
1. **Broken Swagger UI Auth**: `backend/app/api/deps.py` sets `tokenUrl="/api/v1/auth/token"`, but this endpoint does not exist.
2. **Hardcoded Audience**: `backend/app/core/security.py` hardcodes `audience="authenticated"`. This prevents verifying tokens with other audiences (e.g., 'anon' if configured differently).
3. **Test Anti-pattern**: `backend/tests/test_auth.py` modifies `settings.SUPABASE_JWT_SECRET` at module level, which may affect other tests.

## 🟢 LOW ISSUES
4. **Console Logs**: `frontend/components/AuthGuard.tsx` contains `console.log` statements.
5. **Runtime Config Error**: `frontend/middleware.ts` throws runtime exceptions instead of safe initialization failures.
