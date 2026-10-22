import { chromium, expect } from '@playwright/test';
import { writeFileSync } from 'node:fs';

const root = 'http://127.0.0.1:45860';
const browser = await chromium.launch({ headless: true });
const evidence = [];
try {
  for (const [scenario, width, height] of [['capacity', 390, 844], ['unavailable', 1280, 720]]) {
    const context = await browser.newContext({ viewport: { width, height }, timezoneId: 'Africa/Cairo' });
    const page = await context.newPage();
    if (scenario === 'capacity') await page.route('**/api/demo/session', async route => {
      const response = await route.fetch();
      const state = await response.json();
      state.crm_available = false; // Explicit UI injection; DB capacity is covered separately.
      await route.fulfill({ response, json: state });
    });
    await page.goto(`${root}/demo${scenario === 'unavailable' ? '?crm=unavailable' : ''}`);
    if (scenario === 'capacity') await expect(page.getByRole('button', { name: 'Connection temporarily unavailable' })).toBeDisabled();
    else await expect(page.getByText('The HubSpot connection could not be completed. You can continue without CRM.', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Continue without CRM', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Moving out, with pets', exact: false })).toBeVisible();
    const state = await (await context.request.get(`${root}/api/demo/session`)).json();
    if (state.crm_mode !== 'skipped' || state.connection) throw Error('CRM recovery did not preserve the skipped path.');
    evidence.push({ scenario, capacityResponseInjected: scenario === 'capacity', unavailableRedirectNotice: scenario === 'unavailable', actualSkip: true });
    await context.close();
  }
  writeFileSync('.runtime/crm-recovery-check.json', JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify(evidence));
} finally { await browser.close(); }
