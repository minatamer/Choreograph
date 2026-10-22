import {chromium,expect} from '@playwright/test';
import {preparedRequest} from './browser-fixtures.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
mkdirSync('.runtime/screens',{recursive:true});const browser=await chromium.launch({headless:true});const results=[];
try{
 for(const [label,width,height] of [['desktop',1440,1000],['short',1280,720],['phone',390,844],['small-phone',320,740]]){
  const context=await browser.newContext({viewport:{width,height},timezoneId:'Africa/Cairo'});const page=await context.newPage();const errors=[];page.on('pageerror',()=>errors.push('PAGE_ERROR'));
  await page.goto('http://127.0.0.1:45860/demo');await page.getByRole('button',{name:'Connect your HubSpot',exact:true}).click();await page.getByRole('button',{name:'Connect simulated account',exact:true}).click();
  await page.getByRole('checkbox',{name:'Allow these fictional contact and booking records in this account.'}).check();await page.getByRole('button',{name:'Allow demo records',exact:true}).click();
  await expect(page.getByText('Sharing allowed',{exact:true})).toBeVisible();await preparedRequest(context);
  await page.goto('http://127.0.0.1:45860/demo/workspace?view=business');await page.getByRole('checkbox',{name:'I’ve reviewed this request.'}).check();await page.getByRole('button',{name:'Approve and book',exact:true}).click();
  await page.getByRole('button',{name:'Customer view',exact:true}).click();const outcome=page.locator('.booking-outcome');
  await expect(outcome).toContainText('Simulated CRM sync verified. Nothing was sent to HubSpot.',{timeout:20000});
  await outcome.getByText('Sync details',{exact:true}).click();await expect(outcome).toContainText('sim-');if(await outcome.locator('a[href*="hubspot.com"]').count())throw Error('Fake native link');
  await outcome.scrollIntoViewIfNeeded();await page.screenshot({path:`.runtime/screens/sync-${label}.png`});
  await outcome.getByRole('button',{name:'View in Business view',exact:true}).click();const controls=page.getByRole('region',{name:'HubSpot connection'});
  await controls.getByRole('button',{name:'Finish demo',exact:true}).click();await controls.getByRole('checkbox',{name:'Uninstall the app from this HubSpot account.'}).check();
  await controls.getByRole('button',{name:'Finish with these choices',exact:true}).click();
  await expect(controls).toContainText('Demo records: removed',{timeout:20000});await expect(controls).toContainText('Account uninstall: removed');
  await expect(controls.locator('.crm-notice')).toHaveCount(0);
  await controls.scrollIntoViewIfNeeded();await page.screenshot({path:`.runtime/screens/cleanup-${label}.png`});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);if(overflow||errors.length)throw Error(JSON.stringify({label,overflow,errors}));
  results.push({label,simulatedReadback:true,noFakeNativeLink:true,cleanup:true,uninstall:true,overflow,errors});await context.close();
 }
 writeFileSync('.runtime/sync-browser-check.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results));
}finally{await browser.close();}
