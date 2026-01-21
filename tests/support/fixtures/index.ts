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
    // Navigate to root to trigger AuthGuard auto-login
    await page.goto('/');
    
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
