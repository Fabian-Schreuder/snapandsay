import { test as base } from '@playwright/test';
import { UserFactory } from './factories/user-factory';

type TestFixtures = {
  userFactory: UserFactory;
  authenticatedPage: import('@playwright/test').Page;
};

export const test = base.extend<TestFixtures>({
  userFactory: async ({}, use) => {
    const factory = new UserFactory();
    await use(factory);
    await factory.cleanup(); // Auto-cleanup
  },
  authenticatedPage: async ({ page }, use) => {
    // Verify we are mocking if in CI, or just robustly handling it
    // Intercept Supabase signup requests (used for anonymous login)
    await page.route('**/auth/v1/signup', async route => {
      console.log('Intercepted Supabase signup request');
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: "mock-access-token",
          token_type: "bearer",
          expires_in: 3600,
          refresh_token: "mock-refresh-token",
          user: {
            id: "mock-user-id",
            aud: "authenticated",
            role: "authenticated",
            email: "anonymous@example.com",
            confirmed_at: new Date().toISOString(),
            last_sign_in_at: new Date().toISOString(),
            app_metadata: { provider: "email", providers: ["email"] },
            user_metadata: {},
            identities: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            is_anonymous: true
          }
        })
      });
    });

    // Intercept logs request to return empty list (prevents error state in CI/frontend-only mode)
    await page.route('**/api/v1/logs', async route => {
      console.log('Intercepted logs request');
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [],
          pagination: { total: 0, page: 1, size: 50, pages: 1 }
        })
      });
    });

    // Navigate to root to trigger AuthGuard auto-login
    await page.goto('/');
    
    // Pipe console logs to terminal for debugging
    page.on('console', msg => {
        const type = msg.type();
        if (type === 'error' || type === 'warning' || msg.text().includes('Auth state')) {
            console.log(`BROWSER [${type}]: ${msg.text()}`);
        }
    });

    // Wait for Supabase auth cookie to be established
    await base.step('Wait for anonymous login', async () => {
      await base.expect(async () => {
        const cookies = await page.context().cookies();
        const sbCookie = cookies.find(c => c.name.startsWith('sb-') && c.name.endsWith('-auth-token'));
        base.expect(sbCookie).toBeTruthy();
      }).toPass({ timeout: 15000 });
    });

    await use(page);
  },
});

export { expect } from '@playwright/test';
