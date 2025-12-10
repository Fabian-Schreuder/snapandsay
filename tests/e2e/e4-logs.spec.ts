import { test, expect } from '@playwright/test';

test.describe('Epic 4: Dietary Log Management', () => {
  const MOCK_DATE = '2025-05-15';
  
  // Mock Data
  const mockLogs = [
    {
      id: 'log-1',
      user_id: 'user-123',
      image_path: 'placeholder.jpg',
      audio_path: null,
      food_item_recall: [
        { item: 'Oatmeal', quantity: '1 bowl', calories: 150, confidence: 0.95 },
        { item: 'Berries', quantity: '1/2 cup', calories: 40, confidence: 0.90 }
      ],
      description: 'Morning oatmeal with berries',
      created_at: `${MOCK_DATE}T08:30:00Z`,
      calories: 190,
      protein: 5,
      carbs: 30,
      fats: 3
    },
    {
      id: 'log-2',
      user_id: 'user-123',
      image_path: 'placeholder-2.jpg',
      audio_path: null,
      food_item_recall: [
        { item: 'Grilled Chicken Salad', quantity: '1 plate', calories: 450, confidence: 0.92 }
      ],
      description: 'Healthy lunch',
      created_at: `${MOCK_DATE}T12:30:00Z`,
      calories: 450
    }
  ];

  test.beforeEach(async ({ page }) => {
    // 1. Mock Authentication
    const mockSession = {
        access_token: "fake-access-token",
        token_type: "bearer",
        expires_in: 3600,
        refresh_token: "fake-refresh-token",
        user: { 
            id: "user-123",
            aud: "authenticated",
            role: "authenticated",
            email: "test@example.com",
            app_metadata: { provider: "email" },
            user_metadata: {},
            created_at: new Date().toISOString()
        }
    };

    await page.route('**/auth/v1/user', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSession.user)
      });
    });

    await page.route('**/auth/v1/signup', async route => {
         await route.fulfill({ status: 200, body: JSON.stringify(mockSession) });
    });
    
    await page.route('**/auth/v1/token*', async route => {
         await route.fulfill({ status: 200, body: JSON.stringify(mockSession) });
    });

    // 2. Mock GET Logs (List)
    await page.route(/\/api\/v1\/logs(\?.*)?$/, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
            data: mockLogs,
            meta: { total: mockLogs.length }
        })
      });
    });

    // 3. Mock GET Request for Single Log
    await page.route(/\/api\/v1\/logs\/log-\d+/, async route => {
      const logId = route.request().url().split('/').pop();
      const log = mockLogs.find(l => l.id === logId);
      if (log) {
        await route.fulfill({ status: 200, body: JSON.stringify(log) });
      } else {
        await route.fulfill({ status: 404 });
      }
    });

    // 4. Mock Image Storage
    await page.route('**/storage/v1/object/public/**', async route => {
        await route.fulfill({ status: 200, body: 'fake-image-data' }); 
    });

    // Navigate to Dashboard
    await page.goto('/');
  });

  test('TS-4.1: View Daily Log List', async ({ page }) => {
    // Assertions for List View
    await expect(page.getByText('Morning oatmeal with berries')).toBeVisible();
    await expect(page.getByText('190 cal')).toBeVisible(); 
    await expect(page.getByText('Healthy lunch')).toBeVisible();
  });

  test('TS-4.2: Delete Meal Log', async ({ page }) => {
    // Mock DELETE endpoint (and GET to avoid network fallback)
    let deletedId = '';
    await page.route(/\/api\/v1\/logs\/log-\d+/, async route => {
        const method = route.request().method();
        const id = route.request().url().split('/').pop();

        if (method === 'DELETE') {
            deletedId = id || '';
            await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
        } else if (method === 'GET') {
             // Replicate GET logic from beforeEach or simplier
             const log = mockLogs.find(l => l.id === id);
             if (log) {
               await route.fulfill({ status: 200, body: JSON.stringify(log) });
             } else {
               await route.fulfill({ status: 404 });
             }
        } else {
            // Should not happen, but fallback just in case - fail fast instead of hanging
            console.warn(`Unmocked method ${method} for logs endpoint`);
            await route.fulfill({ status: 500, body: 'Unmocked method in test' });
        }
    });

    // 1. Click the first card
    await page.getByText('Morning oatmeal with berries').click();

    // 2. Wait for Navigation to Detail Page
    await expect(page).toHaveURL(/\/log\/log-1/);
    await expect(page.getByRole('heading', { name: 'Meal Details' })).toBeVisible();

    // 3. Click Delete (Bottom bar)
    await page.getByRole('button', { name: 'Delete' }).click();

    // 4. Verify Dialog
    await expect(page.getByRole('alertdialog')).toBeVisible();
    await expect(page.getByText('This action cannot be undone')).toBeVisible();

    // 5. Confirm Delete
    const confirmBtn = page.getByRole('alertdialog').getByRole('button', { name: 'Delete' });
    await confirmBtn.click();

    // 6. Verify API Call
    await expect(async () => {
        expect(deletedId).toBe('log-1');
    }).toPass();

    // 7. Verify Redirect to Home
    await expect(page).toHaveURL('http://localhost:3000/'); 
  });

  test('TS-4.3: Edit Meal Log', async ({ page }) => {
    // Mock PUT and GET (Stateful)
    let putData: any = null;
    let getCallCount = 0;

    await page.route(/\/api\/v1\/logs\/log-1/, async route => {
        const method = route.request().method();
        
        if (method === 'PUT') {
            putData = route.request().postDataJSON();
            await route.fulfill({ 
                status: 200, 
                body: JSON.stringify({ ...mockLogs[0], ...putData }) 
            });
            return;
        }

        if (method === 'GET') {
             getCallCount++;
             if (getCallCount > 1 && putData) {
                 // Return updated data
                 await route.fulfill({ 
                     status: 200, 
                     body: JSON.stringify({ ...mockLogs[0], ...putData }) 
                 });
             } else {
                 // Initial load
                 await route.fulfill({ status: 200, body: JSON.stringify(mockLogs[0]) });
             }
             return;
        }
        
        await route.continue();
    });

    // 1. Navigate to log
    await page.getByText('Morning oatmeal with berries').click();
    await expect(page).toHaveURL(/\/log\/log-1/);

    // 2. Click Edit
    await page.getByRole('button', { name: 'Edit' }).click();
    
    // 3. Verify Sheet
    await expect(page.getByRole('heading', { name: 'Edit Meal' })).toBeVisible();

    // 4. Edit Description
    await page.getByLabel('Description').fill('Updated Oatmeal Delight');
    
    // 5. Save
    await page.getByRole('button', { name: 'Save' }).click();

    // 6. Verify PUT payload
    await expect(async () => {
        expect(putData).toBeTruthy();
        expect(putData.description).toBe('Updated Oatmeal Delight');
    }).toPass();

    // 7. Verify UI Update (on Detail Page)
    await expect(page.getByRole('heading', { name: 'Edit Meal' })).not.toBeVisible();
    await expect(page.getByRole('heading', { name: 'Updated Oatmeal Delight' })).toBeVisible();
  });
});
