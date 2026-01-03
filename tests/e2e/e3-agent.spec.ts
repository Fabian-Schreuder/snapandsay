import { test, expect } from '@playwright/test';

// These tests require a real Supabase instance for auth and are skipped in CI
// They verify agent streaming and clarification flows
test.describe.skip('Epic 3: LangGraph Agent Setup', () => {
  test.beforeEach(async ({ page, browserName }) => {
    // 1. Grant Permissions (only Chromium supports camera/microphone permissions)
    // WebKit and Firefox rely on fake media devices configured in playwright.config.ts
    if (browserName === 'chromium') {
        await page.context().grantPermissions(['camera', 'microphone']);
    }
    
    await page.addInitScript(() => {
        // @ts-ignore
        window.originalFetch = window.fetch;
        // @ts-ignore
        window.fetch = async (input, init) => {
            let url = input;
            if (typeof input === 'object' && input !== null && 'url' in input) {
                url = input.url;
            }
            const urlString = url.toString();
            // console.log('[MOCK] Fetch:', urlString); // Debug log in browser

            if (urlString.includes('/api/v1/analysis/stream')) {
                const stream = new ReadableStream({
                    start(controller) {
                        // @ts-ignore
                        window.streamController = controller;
                    }
                });
                return new Response(stream, { 
                    headers: { 'Content-Type': 'text/event-stream' } 
                });
            }
            // @ts-ignore
            return window.originalFetch(input, init);
        };
    });

    page.on('console', msg => console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`));
    page.on('pageerror', err => console.log(`[BROWSER ERROR] ${err.name}: ${err.message}`));

    await page.goto('/snap');
  });

  test('TS-3.1 & 3.2: Thinking Indicator & Agent Streaming', async ({ page }) => {
    // Mock Upload Endpoint
    await page.route('**/api/v1/analysis/upload', async route => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ analysis_id: "mock-log-123", status: "processing" })
        });
    });

    // --- Perform Capture Flow ---
    await page.locator('video').waitFor({ state: 'visible' });
    await page.waitForFunction(() => {
        const video = document.querySelector('video');
        return video && video.readyState >= 2;
    });

    // Take Photo & Confirm
    await page.getByRole('button', { name: /take photo|capture|shutter/i }).first().click();
    await page.getByLabel('Confirm').click();

    // Simulate Voice Recording (hold button)
    const voiceBtn = page.getByLabel('Hold to record voice note');
    await expect(voiceBtn).toBeVisible();
    await voiceBtn.dispatchEvent('mousedown');
    await page.waitForTimeout(1000);
    await voiceBtn.dispatchEvent('mouseup');

    // --- Verify Agent UI ---

    // 0. Wait for Stream Connection
    await page.waitForFunction(() => typeof (window as any).streamController !== 'undefined', null, { timeout: 10000 });

    // 1. Push "Thinking" Event
    await page.evaluate(() => {
        const encoder = new TextEncoder();
        const event = {
            type: "agent.thought",
            payload: { step: "1", message: "Analyzing food image...", timestamp: new Date().toISOString() }
        };
        // @ts-ignore
        window.streamController.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
    });

    // 2. Verify Thinking Indicator
    const thinkingIndicator = page.getByText('Analyzing food image...');
    await expect(thinkingIndicator).toBeVisible({ timeout: 10000 });

    // 3. Push "Clarification" Event
    await page.evaluate(() => {
        const encoder = new TextEncoder();
        const event = {
            type: "agent.clarification",
            payload: {
                question: "Is this a breakfast burrito?",
                options: ["Yes", "No"],
                context: {},
                log_id: "mock-log-123"
            }
        };
        // @ts-ignore
        window.streamController.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
         // @ts-ignore
        window.streamController.close();
    });

    // 4. Verify Clarification Prompt
    const clarification = page.getByText('Is this a breakfast burrito?');
    await expect(clarification).toBeVisible({ timeout: 10000 });
    
    // 5. Verify Options
    await expect(page.getByRole('button', { name: "Yes" })).toBeVisible();
  });

  test('TS-3.3: Submit Clarification', async ({ page }) => {
     // Mock Upload
     await page.route('**/api/v1/analysis/upload', async route => {
        await route.fulfill({ body: JSON.stringify({ analysis_id: "mock-log-123", status: "processing" }) });
    });

     // Mock Clarification Submission
    await page.route('**/api/v1/analysis/clarify/*', async route => {
         await route.fulfill({
             status: 200,
             body: JSON.stringify({ status: "processing" })
         });
    });

    // NOTE: Stream is mocked via window.fetch in beforeEach. 
    // We don't need page.route for 'stream'.

    // --- Capture Flow ---
    await page.locator('video').waitFor({ state: 'visible' });
    await page.waitForFunction(() => {
        const video = document.querySelector('video');
        return video && video.readyState >= 2;
    });

    // Use specific locator consistent with TS-3.1
    await page.getByRole('button', { name: /take photo|capture|shutter/i }).first().click();
    await page.getByLabel('Confirm').click();
    
    const voiceBtn = page.getByLabel('Hold to record voice note');
    await expect(voiceBtn).toBeVisible();
    await voiceBtn.dispatchEvent('mousedown');
    await page.waitForTimeout(500);
    await voiceBtn.dispatchEvent('mouseup');

    // --- Push Clarification Request directly ---
    await page.waitForFunction(() => typeof (window as any).streamController !== 'undefined', null, { timeout: 10000 });
    
    await page.evaluate(() => {
        const encoder = new TextEncoder();
        const event = {
             type: "agent.clarification",
             payload: {
                 question: "Is this correct?",
                 options: ["Yes"],
                 log_id: "mock-log-123"
             }
        };
        // @ts-ignore
        window.streamController.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
    });

    // Verify Prompt
    await expect(page.getByText('Is this correct?')).toBeVisible({ timeout: 10000 });

    // Click Option
    await page.getByRole('button', { name: "Yes" }).click();

    // Verify prompt disappears (submission handling)
    await expect(page.getByText('Is this correct?')).not.toBeVisible();
  });
});
