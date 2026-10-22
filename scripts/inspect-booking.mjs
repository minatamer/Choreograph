import {chromium,expect} from '@playwright/test';
import {preparedRequest} from './browser-fixtures.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
mkdirSync('.runtime/screens',{recursive:true});const browser=await chromium.launch({headless:true});const evidence=[];
try{
  for(const [label,width,height] of [['desktop',1440,1000],['short',1280,720],['phone',390,844],['small-phone',320,740]]){
    const context=await browser.newContext({viewport:{width,height},timezoneId:'Africa/Cairo',locale:'en-US'});
    const {requestId}=await preparedRequest(context);const page=await context.newPage();const errors=[];
    page.on('pageerror',()=>errors.push('PAGE_ERROR'));
    await page.goto('http://127.0.0.1:45860/demo/workspace?view=business');
    await expect(page.getByRole('heading',{name:'Booking requests',exact:true})).toBeVisible();
    await page.getByRole('checkbox',{name:'I’ve reviewed this request.'}).check();
    const approve=page.getByRole('button',{name:'Approve and book',exact:true});await approve.scrollIntoViewIfNeeded();
    const box=await approve.boundingBox();if(!box||box.y<0||box.y+box.height>height+1)throw Error('Approve unreachable');
    await approve.click();await expect(page.getByRole('button',{name:'Reschedule',exact:true})).toBeVisible();
    await page.screenshot({path:`.runtime/screens/business-${label}.png`,fullPage:true});
    await page.reload();await expect(page.getByRole('heading',{name:'Booking requests',exact:true})).toBeVisible();
    await page.getByRole('button',{name:'Customer view',exact:true}).click();
    await expect(page.getByText('Booking confirmed',{exact:true})).toBeVisible();
    await expect(page.getByText('CRM not connected. No records were sent.',{exact:true})).toBeVisible();
    await page.screenshot({path:`.runtime/screens/booking-${label}.png`,fullPage:true});
    await page.getByRole('button',{name:'View in Business view',exact:true}).click();
    await page.getByRole('button',{name:'Reschedule',exact:true}).click();
    const calendar=page.getByRole('region',{name:'Available appointments'});
    const original=await (await context.request.get('http://127.0.0.1:45860/api/demo/session')).json();
    const record=original.requests.find(row=>row.id===requestId);const date=record.preferred_at.slice(0,10);
    // Choose its original local day, then a different valid full-duration option.
    const localDate=await page.evaluate(({instant,zone})=>new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(instant)),{instant:record.preferred_at,zone:original.timezone});
    await calendar.locator(`[data-date="${localDate}"]`).click();
    await calendar.locator('.time-options button').nth(1).click();
    await page.getByRole('checkbox',{name:'I’ve reviewed this request.'}).check();
    await page.getByRole('button',{name:'Confirm new time',exact:true}).click();
    await expect(page.getByRole('button',{name:'Reschedule',exact:true})).toBeVisible();
    const changed=await (await context.request.get('http://127.0.0.1:45860/api/demo/session')).json();
    if(changed.requests.find(row=>row.id===requestId).booking.starts_at===record.booking.starts_at)throw Error('Reschedule not applied');
    page.once('dialog',dialog=>dialog.accept());
    await page.getByRole('button',{name:'Cancel booking',exact:true}).click();
    await expect(page.getByText('Cancelled',{exact:true})).toBeVisible();
    if(label==='desktop'){
      await preparedRequest(context);await page.reload();
      await page.getByRole('checkbox',{name:'I’ve reviewed this request.'}).check();
      await page.getByRole('button',{name:'Approve and book',exact:true}).click();
      page.once('dialog',dialog=>dialog.accept());
      await page.getByRole('button',{name:'Mark completed',exact:true}).click();
      await expect(page.getByText('Completed',{exact:true})).toBeVisible();
    }
    if(await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth)||errors.length)throw Error('Visual booking check failed');
    evidence.push({label,width,height,approved:true,refresh:true,rescheduled:true,cancelled:true,approveReachable:true,errors});await context.close();
  }
}finally{await browser.close();}
writeFileSync('.runtime/booking-evidence.json',JSON.stringify(evidence,null,2));console.log(JSON.stringify(evidence));
