import {chromium,expect} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
mkdirSync('.runtime/screens',{recursive:true});const browser=await chromium.launch({headless:true});const results=[];
try{
 for(const [label,width,height] of [['desktop',1440,1000],['phone',390,844]]){
  const context=await browser.newContext({viewport:{width,height},timezoneId:'Africa/Cairo'});const page=await context.newPage();const errors=[];page.on('pageerror',()=>errors.push('PAGE_ERROR'));
  await page.goto('http://127.0.0.1:45860/demo');
  await page.getByRole('button',{name:'Connect your HubSpot',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Simulate a HubSpot connection'})).toBeVisible();
  await page.getByRole('button',{name:'Cancel connection',exact:true}).click();
  await expect(page.getByText('Connection cancelled. No CRM records were sent.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Connect your HubSpot',exact:true}).click();await page.getByRole('button',{name:'Connect simulated account',exact:true}).click();
  await expect(page.getByText('Simulated HubSpot connected. No records have been shared.',{exact:true})).toBeVisible();
  await page.getByRole('checkbox',{name:'Allow these fictional contact and booking records in this account.'}).check();
  await page.getByRole('button',{name:'Allow demo records',exact:true}).click();await expect(page.getByText('Sharing allowed',{exact:true})).toBeVisible();
  await page.screenshot({path:`.runtime/screens/crm-entry-${label}.png`,fullPage:true});
  await page.getByRole('button',{name:'Continue to the front desk',exact:true}).click();
  await expect(page.getByRole('button',{name:'Moving out, with pets',exact:false})).toBeVisible();
  await page.getByRole('button',{name:'Business view',exact:true}).click();const controls=page.getByRole('region',{name:'HubSpot connection'});
  await controls.getByRole('button',{name:'Finish demo',exact:true}).click();await expect(page.getByText('HubSpot emails account admins after a real uninstall.',{exact:false})).toBeVisible();
  await controls.getByRole('button',{name:'Disconnect this workspace',exact:true}).click();
  await expect(controls.getByText('Disconnected from this workspace.',{exact:false})).toBeVisible();
  const state=await (await context.request.get('http://127.0.0.1:45860/api/demo/session')).json();if(state.crm_mode!=='skipped'||state.connection.state!=='detached')throw Error('Disconnect not persisted');
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);if(overflow||errors.length)throw Error(JSON.stringify({label,overflow,errors}));
  results.push({label,denial:true,simulated:true,consent:true,detach:true,overflow,errors});await context.close();
 }
 writeFileSync('.runtime/crm-browser-check.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results));
}finally{await browser.close();}
