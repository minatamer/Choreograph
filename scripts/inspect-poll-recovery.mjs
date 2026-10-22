import { chromium, expect } from '@playwright/test';
import { writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { preparedRequest } from './browser-fixtures.mjs';

const root = 'http://127.0.0.1:45860';
const browser = await chromium.launch({ headless: true });
const evidence = [];
try {
  for (const scenario of ['transient', 'expired', 'expired-mutation']) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, timezoneId: 'Africa/Cairo' });
    const { state, requestId } = await preparedRequest(context);
    const record = state.requests.find(row => row.id === requestId);
    const approval = await context.request.post(`${root}/api/demo/requests/${requestId}/approve`, {
      headers: { origin: root, 'x-csrf-token': state.csrf, 'idempotency-key': crypto.randomUUID() },
      data: { generation: state.generation, revision: state.revision, request_revision: record.revision, confirm: true },
    });
    if (approval.status() !== 200) throw Error('Isolated booking setup failed.');
    let polls = 0;
    function expireFixture() {
      const python = process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python';
      const expired = spawnSync(python, ['-B', 'scripts/expire-browser-fixture.py', state.workspace_id], { encoding: 'utf8', windowsHide: true, timeout: 15000 });
      if (expired.status !== 0) throw Error('Fresh fake-browser fixture could not be expired.');
    }
    const page = await context.newPage();
    // Explicit browser-only status injection; persisted booking uses real API/DB
    // and skipped CRM. This does not claim a real provider outage or expiry.
    await page.route('**/api/demo/session', async route => {
      if (route.request().method() === 'POST') {
        const response = await route.fetch();
        const body = await response.json();
        if (scenario !== 'expired-mutation') body.requests[0].crm_state = 'pending';
        await route.fulfill({ response, json: body });
      } else if (++polls === 1) {
        if (scenario === 'expired') {
          expireFixture();
          await route.continue();
        } else await route.fulfill({ status: 503, contentType: 'application/json',
          body: JSON.stringify({ code: 'INJECTED_UNAVAILABLE', message: 'The connection is briefly unavailable. Try again.' }) });
      } else await route.continue();
    });
    await page.goto(`${root}/demo/workspace`);
    await expect(page.getByText('Booking confirmed', { exact: true })).toBeVisible();
    const composer = page.getByRole('textbox', { name: 'Ask Juniper' });
    await composer.fill('Keep this unsent question.');
    if (scenario === 'expired-mutation') { expireFixture(); await page.getByRole('button', { name: 'Send message' }).click(); }
    const error = page.locator('.error-banner');
    await expect(error).toBeVisible({ timeout: 7000 });
    if (scenario === 'transient') {
      await expect(error).toHaveCount(0, { timeout: 7000 });
      await expect(composer).toHaveValue('Keep this unsent question.');
      if (polls < 2) throw Error('Polling did not recover after the injected failure.');
    } else {
      await expect(page.locator('.booking-outcome')).toHaveCount(0);
      await page.unroute('**/api/demo/session');
      await page.getByRole('button', { name: 'Start a new demo', exact: true }).click();
      await expect(page.getByRole('textbox', { name: 'Ask Juniper' })).toHaveValue('');
      const next = await (await context.request.get(`${root}/api/demo/session`)).json();
      if (next.workspace_id === state.workspace_id) throw Error('Expired-session restart reused the old workspace.');
    }
    evidence.push({ scenario, pendingStatusInjected: scenario !== 'expired-mutation', failureInjected: scenario === 'transient', freshFixtureExpired: scenario !== 'transient', polls, recovered: true });
    await context.close();
  }
  writeFileSync('.runtime/poll-recovery-check.json', JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify(evidence));
} finally { await browser.close(); }
