import { test, expect } from '@playwright/test';

test.describe('Epic 5: Admin Oversight', () => {
    // --- Mock Data ---
    const MOCK_LOGS = [
        { 
            id: 'log-1', 
            user_id: 'user-A', 
            description: 'Log 1 Description', 
            calories: 500, 
            created_at: '2025-05-20T10:00:00Z',
            image_path: 'img1.jpg',
            protein: 20, carbs: 50, fats: 10
        },
        { 
            id: 'log-2', 
            user_id: 'user-B', 
            description: 'Log 2 Description', 
            calories: 300, 
            created_at: '2025-05-21T12:00:00Z',
            image_path: 'img2.jpg',
            protein: 10, carbs: 30, fats: 5
        }
    ];

    const MOCK_ANON_SESSION = {
        access_token: "anon-token",
        token_type: "bearer",
        expires_in: 3600,
        refresh_token: "anon-refresh",
        user: { 
            id: "anon-user",
            aud: "authenticated",
            role: "anon",
            is_anonymous: true,
            email: "",
            app_metadata: { provider: "email" },
            user_metadata: {},
            created_at: new Date().toISOString()
        }
    };

    const MOCK_ADMIN_SESSION = {
        access_token: "admin-access-token",
        token_type: "bearer",
        expires_in: 3600,
        refresh_token: "admin-refresh-token",
        user: { 
            id: "admin-user",
            aud: "authenticated",
            role: "authenticated",
            is_anonymous: false, 
            email: "admin@example.com",
            app_metadata: { provider: "email" },
            user_metadata: { role: "admin" },
            created_at: new Date().toISOString()
        }
    };

    // --- Helpers ---

    async function loginAsAdmin(page: any) {
        // 1. Visit /admin (AuthGuard signs in anonymously -> AdminGuard shows Login Form)
        await page.goto('/admin');
        await expect(page.getByRole('heading', { name: 'Admin Access' })).toBeVisible();

        // 2. Fill Form
        await page.getByLabel('Email').fill('admin@example.com');
        await page.getByLabel('Password').fill('password123');
        
        // 3. Submit
        await page.getByRole('button', { name: 'Sign In' }).click();

        // 4. Wait for Dashboard to confirm login success
        await expect(page.getByRole('heading', { name: 'Beheer' })).toBeVisible();
    }

    test.beforeEach(async ({ page }) => {
        // 1. Mock Auth Endpoints
        
        // POST /signup (for AuthGuard anonymous fallback)
        await page.route('**/auth/v1/signup', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(MOCK_ANON_SESSION)
            });
        });

        // POST /token (for login, refresh, anonymous)
        await page.route('**/auth/v1/token*', async route => {
            const req = route.request();
            const postData = req.postDataJSON();
            
            // Check for password login (signInWithPassword often sends { email, password } without explicit grant_type in some versions, or with it)
            if (postData && (postData.grant_type === 'password' || postData.password)) {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(MOCK_ADMIN_SESSION)
                });
                return;
            }

            // Default fallback (e.g. anonymous or refresh)
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(MOCK_ANON_SESSION)
            });
        });

        // GET /user (session verification)
        await page.route('**/auth/v1/user', async route => {
             const headers = route.request().headers();
             const authHeader = headers['authorization'] || '';
             
             if (authHeader.includes('admin-access-token')) {
                 await route.fulfill({ status: 200, body: JSON.stringify(MOCK_ADMIN_SESSION.user) });
             } else {
                 await route.fulfill({ status: 200, body: JSON.stringify(MOCK_ANON_SESSION.user) });
             }
        });

        // 2. Mock Admin Logs API
        await page.route(/\/api\/v1\/admin\/logs/, async route => {
             const url = route.request().url();
             let filteredLogs = [...MOCK_LOGS];

             if (url.includes('user_id=user-A')) {
                 filteredLogs = filteredLogs.filter(l => l.user_id === 'user-A');
             }

             await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ 
                    data: filteredLogs,
                    meta: { 
                        total: filteredLogs.length, 
                        page: 1, 
                        limit: 20, 
                        pages: 1 
                    }
                })
            });
        });

        // 3. Mock Export API
        await page.route('**/api/v1/admin/export*', async route => {
             await route.fulfill({
                 status: 200,
                 contentType: 'text/csv',
                 headers: {
                     'Content-Disposition': 'attachment; filename="export.csv"'
                 },
                 body: 'id,user_id,description\nlog-1,user-A,test'
             });
        });
    });

    // --- Tests ---

    test('TS-5.1: Admin Access & Dashboard View', async ({ page }) => {
        // Manually performing login to verify the flow
        await page.goto('/admin');
        await expect(page.getByRole('heading', { name: 'Admin Access' })).toBeVisible();

        await page.getByLabel('Email').fill('admin@example.com');
        await page.getByLabel('Password').fill('password123');
        await page.getByRole('button', { name: 'Sign In' }).click();

        await expect(page.getByRole('heading', { name: 'Beheer' })).toBeVisible();
        await expect(page.getByText('Log 1 Description')).toBeVisible();
        await expect(page.getByText('user-A')).toBeVisible();
    });

    test('TS-5.2: Filtering Logs', async ({ page }) => {
        await loginAsAdmin(page);

        // 1. Filter by User ID
        // Use Label selector as it's more robust than placeholder
        const filterInput = page.getByLabel('User ID'); 
        await expect(filterInput).toBeVisible();
        await filterInput.fill('user-A');
        
        const responsePromise = page.waitForResponse(resp => 
            resp.url().includes('/api/v1/admin/logs') && resp.url().includes('user_id=user-A')
        );

        // Click Apply Filters button (more robust than Enter key sometimes)
        await page.getByRole('button', { name: 'Apply Filters' }).click();
        
        await responsePromise;

        // 2. Verify Results
        await expect(page.getByText('Log 1 Description')).toBeVisible();
        await expect(page.getByText('Log 2 Description')).not.toBeVisible();
    });

    test('TS-5.3: Data Export', async ({ page }) => {
        await loginAsAdmin(page);

        // Track export request
        let exportRequested = false;
        await page.route('**/api/v1/admin/export*', async route => {
             exportRequested = true;
             await route.fulfill({
                 status: 200,
                 contentType: 'text/csv',
                 body: 'csv-data'
             });
        });

        // Click Export Dropdown Trigger
        await page.getByRole('button', { name: 'Export Data' }).click();
        // Click CSV Option
        await page.getByRole('menuitem', { name: 'Export as CSV' }).click();
        
        await expect(async () => {
            expect(exportRequested).toBe(true);
        }).toPass();
    });
});
