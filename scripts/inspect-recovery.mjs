import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { preparedRequest } from './browser-fixtures.mjs';

const receipts = () => JSON.parse(readFileSync('.runtime/services.json', 'utf8'));
const before = receipts();
function manage(action) {
  const result = spawnSync(process.execPath, ['scripts/local.mjs', action], {
    windowsHide: true, encoding: 'utf8', timeout: 45000,
  });
  if (result.error || result.status !== 0) throw Error('Owned runner lifecycle check failed.');
}
const browser = await chromium.launch({ headless: true });
let stopped = false;
try {
  manage('stop-runner'); stopped = true;
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 }, timezoneId: 'Africa/Cairo' });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:45860/demo');
  await page.getByRole('button', { name: 'Connect your HubSpot', exact: true }).click();
  await page.getByRole('button', { name: 'Connect simulated account', exact: true }).click();
  await page.getByRole('checkbox', { name: 'Allow these fictional contact and booking records in this account.' }).check();
  await page.getByRole('button', { name: 'Allow demo records', exact: true }).click();
  await expect(page.getByText('Sharing allowed', { exact: true })).toBeVisible();
  const prepared = await preparedRequest(context);
  await page.goto('http://127.0.0.1:45860/demo/workspace?view=business');
  await page.getByRole('checkbox', { name: 'I’ve reviewed this request.' }).check();
  await page.getByRole('button', { name: 'Approve and book', exact: true }).click();
  const state = async () => (await context.request.get('http://127.0.0.1:45860/api/demo/session')).json();
  let current = await state();
  if (current.requests[0].crm_state !== 'pending') throw Error('Work was not durably pending while runner was stopped.');
  await page.reload();
  current = await state();
  if (current.requests[0].id !== prepared.requestId || current.requests[0].crm_state !== 'pending') throw Error('Refresh changed pending booking.');
  manage('start-runner'); stopped = false;
  await page.getByRole('button', { name: 'Customer view', exact: true }).click();
  await expect(page.locator('.booking-outcome')).toContainText('Simulated CRM sync verified.', { timeout: 20000 });
  current = await state();
  const receipt = current.requests[0].crm_receipt;
  await page.reload();
  const refreshed = await state();
  if (JSON.stringify(refreshed.requests[0].crm_receipt) !== JSON.stringify(receipt)) throw Error('Refresh duplicated the verified receipt.');
  const after = receipts();
  if (after.runner.pid === before.runner.pid || after.api.pid !== before.api.pid || after.frontend.pid !== before.frontend.pid) throw Error('Runner restart changed the wrong services.');
  writeFileSync('.runtime/recovery-browser-check.json', JSON.stringify({ pendingSurvivedRefresh: true, newRunner: true, otherServicesPreserved: true, replayStable: true }, null, 2));
  console.log('Runner restart recovered the persisted booking export; API/frontend instances were preserved.');
  await context.close();
} finally {
  if (stopped) manage('start-runner');
  await browser.close();
}
