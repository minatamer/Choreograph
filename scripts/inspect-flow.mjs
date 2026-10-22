import { chromium, expect } from '@playwright/test';
import { writeFileSync } from 'node:fs';

const root = 'http://127.0.0.1:45860';
const browser = await chromium.launch({ headless: true });
const evidence = [];
try {
  for (const [branch, width, height, zone] of [
    ['connected-busy', 1440, 900, 'Africa/Cairo'],
    ['skipped-open-week', 768, 1024, 'Asia/Kathmandu'],
  ]) {
    const context = await browser.newContext({ viewport: { width, height }, timezoneId: zone });
    const page = await context.newPage();
    const detectedZone = await page.evaluate(() => Intl.DateTimeFormat().resolvedOptions().timeZone);
    const errors = [];
    page.on('pageerror', () => errors.push('PAGE_ERROR'));
    const session = async () => (await context.request.get(`${root}/api/demo/session`)).json();
    await page.goto(root);
    await page.locator('.hero-invitation').getByRole('link', { name: 'Try demo', exact: true }).click();
    if (branch.startsWith('connected')) {
      await page.getByRole('button', { name: 'Connect your HubSpot', exact: true }).click();
      await page.getByRole('button', { name: 'Connect simulated account', exact: true }).click();
      await page.getByRole('checkbox', { name: 'Allow these fictional contact and booking records in this account.' }).check();
      await page.getByRole('button', { name: 'Allow demo records', exact: true }).click();
      await page.getByRole('button', { name: 'Continue to the front desk', exact: true }).click();
    } else await page.getByRole('button', { name: 'Continue without CRM', exact: true }).click();
    await page.getByRole('button', { name: branch.startsWith('connected') ? 'Moving out, with pets' : 'Find a regular clean', exact: false }).click();
    if ((await session()).messages.length) throw Error('Starter selection dispatched automatically.');
    await page.getByRole('button', { name: 'Send message' }).click();
    const reader = page.getByRole('complementary', { name: 'Document reader' });
    if (branch.startsWith('connected')) {
      await expect(page.getByRole('article', { name: 'Juniper reply' }).last()).toContainText('occupied');
      await expect(reader.locator('canvas')).toHaveAttribute('data-rendered-page', /^[1-9]$/, { timeout: 20000 });
      await reader.getByRole('button', { name: 'Close document reader' }).click();
      await page.locator('.answer-passages').getByRole('button', { name: /Service Guide/ }).first().click();
      await expect(reader.locator('canvas')).toHaveAttribute('data-rendered-page', '2', { timeout: 20000 });
      await expect(reader.locator('.supported-excerpt')).toContainText('Carpet');
      await reader.getByRole('button', { name: 'Close document reader' }).click();
    }
    const calendar = page.getByRole('region', { name: 'Available appointments' });
    await expect(calendar.locator('.calendar-day')).toHaveCount(7);
    if (branch.startsWith('connected')) {
      const state = await session();
      const alternative = calendar.locator(`[data-date="${state.scenario.alternative_date}"]`);
      if (!await alternative.count()) await calendar.getByRole('button', { name: 'Next week' }).click();
      await alternative.click();
    } else {
      if (!await calendar.locator('.calendar-day.available').count()) await calendar.getByRole('button', { name: 'Next week' }).click();
      await calendar.locator('.calendar-day.available').first().click();
    }
    await calendar.locator('.time-options button').first().click();
    await expect(page.getByRole('status', { name: 'Quote total' })).toContainText(branch.startsWith('connected') ? '185.00' : '60.00');
    await page.getByRole('checkbox', { name: 'I’ve reviewed this quote.' }).check();
    await page.getByRole('button', { name: 'Send request', exact: true }).click();
    await page.getByRole('button', { name: 'Review in Business view', exact: true }).click();
    await page.getByRole('checkbox', { name: 'I’ve reviewed this request.' }).check();
    await page.getByRole('button', { name: 'Approve and book', exact: true }).click();
    await page.getByRole('button', { name: 'Customer view', exact: true }).click();
    const outcome = page.locator('.booking-outcome');
    await expect(outcome).toContainText('Booking confirmed');
    await expect(outcome).toContainText(branch.startsWith('connected') ? 'Simulated CRM sync verified.' : 'CRM not connected. No records were sent.', { timeout: 20000 });
    const booked = await session();
    if (booked.timezone !== detectedZone || booked.requests.length !== 1) throw Error('Booking or detected scheduling timezone changed.');
    await page.reload();
    await expect(outcome).toContainText('Booking confirmed');
    const refreshed = await session();
    if (JSON.stringify(refreshed.requests) !== JSON.stringify(booked.requests)) throw Error('Refresh replayed or changed the booking.');
    if (branch.startsWith('connected')) {
      await outcome.getByRole('button', { name: 'View in Business view' }).click();
      await page.getByRole('button', { name: 'Use revised preparation guide' }).click();
      await expect(page.getByText('The new guide is ready.', { exact: true })).toBeVisible();
      await page.getByRole('button', { name: 'Customer view', exact: true }).click();
      await page.getByRole('textbox', { name: 'Ask Juniper' }).fill('What should I do with my pets?');
      await page.getByRole('button', { name: 'Send message' }).click();
      await expect(page.locator('.answer-passages').last()).toContainText('outside the home');
      await expect(reader).toContainText('Your replacement');
      await reader.getByRole('button', { name: 'Close document reader' }).click();
      const replaced = await session();
      if (JSON.stringify(replaced.requests) !== JSON.stringify(booked.requests)) throw Error('Document guidance changed the reservation.');
    }
    await page.screenshot({ path: `.runtime/screens/full-flow-${branch}.png`, fullPage: true });
    page.once('dialog', dialog => dialog.accept());
    await page.getByRole('button', { name: 'Reset demo', exact: true }).click();
    await expect(page.getByRole('textbox', { name: 'Ask Juniper' })).toHaveValue('');
    await expect(outcome).toHaveCount(0);
    const reset = await session();
    if (reset.workspace_id === booked.workspace_id || reset.requests.length || reset.messages.length) throw Error('Reset did not retire the old workspace.');
    if (errors.length || await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)) throw Error('Complete flow visual/runtime failure.');
    evidence.push({ branch, width, height, browserZone: zone, savedZone: detectedZone, landingToBooking: true, explicitSend: true, sameRecordsAfterRefresh: true,
      replacementReask: branch.startsWith('connected'), reset: true, errors });
    writeFileSync('.runtime/full-flow-check.json', JSON.stringify(evidence, null, 2));
    await context.close();
  }
  writeFileSync('.runtime/full-flow-check.json', JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify(evidence));
} finally { await browser.close(); }
