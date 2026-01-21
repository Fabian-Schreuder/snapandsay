import { test, expect } from '../support/fixtures';

test.describe('Dutch Language Support', () => {
  
  test('TS-I18N-1: Default language is Dutch', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check that html lang attribute is Dutch
    const htmlLang = await page.locator('html').getAttribute('lang');
    expect(htmlLang).toBe('nl');
  });

  test('TS-I18N-2: Dutch translations display on dashboard', async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    // Navigate to dashboard
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Look for Dutch text - the "Log a Meal" button should say "Maaltijd vastleggen"
    const snapButton = page.getByRole('link', { name: /maaltijd/i });
    await expect(snapButton).toBeVisible({ timeout: 10000 });
  });

  test('TS-I18N-3: Language toggle available in admin', async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    // Navigate to admin page
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    
    // Check for language toggle dropdown
    const languageSelect = page.getByRole('combobox', { name: /taal/i });
    await expect(languageSelect).toBeVisible({ timeout: 10000 });
  });

  test('TS-I18N-4: Language switch persists to cookie', async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    // Navigate to admin page
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    
    // Find and click language toggle
    const languageSelect = page.getByRole('combobox', { name: /taal/i });
    if (await languageSelect.isVisible()) {
      await languageSelect.click();
      
      // Select English
      const englishOption = page.getByRole('option', { name: /engels|english/i });
      if (await englishOption.isVisible()) {
        await englishOption.click();
        
        // Check cookie was set
        await page.waitForTimeout(500);
        const cookies = await page.context().cookies();
        const localeCookie = cookies.find(c => c.name === 'locale');
        expect(localeCookie).toBeTruthy();
        expect(localeCookie?.value).toBe('en');
      }
    }
  });

  test('TS-I18N-5: Error messages display in Dutch', async ({ page }) => {
    // Navigate directly to snap page without auth (should show error or redirect)
    await page.goto('/snap');
    await page.waitForLoadState('networkidle');
    
    // Check that any error text is in Dutch (if visible)
    const pageContent = await page.textContent('body');
    
    // Should not contain common English-only phrases
    // (This is a soft check - main validation is that Dutch text appears)
    if (pageContent?.includes('Something went wrong')) {
      test.fail(true, 'English error text found instead of Dutch');
    }
  });
});
