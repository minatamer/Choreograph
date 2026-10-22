import {chromium,expect} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
mkdirSync('.runtime/screens',{recursive:true});const browser=await chromium.launch({headless:true});const results=[];
try{
 for(const [label,width,height] of [['desktop',1440,1000],['short',1280,720],['phone',390,844],['small-phone',320,740]]){
  const context=await browser.newContext({viewport:{width,height},timezoneId:'Asia/Katmandu',locale:'en-US'});const page=await context.newPage();const errors=[];
  page.on('pageerror',error=>errors.push(error.message.slice(0,120)));
  await page.goto('http://127.0.0.1:45860/demo/workspace');
  await page.getByRole('button',{name:'Moving out, with pets',exact:false}).click();
  const composer=page.getByRole('textbox',{name:'Ask Juniper'});await expect(composer).toHaveValue(/two-bedroom/);
  let state=await (await context.request.get('http://127.0.0.1:45860/api/demo/session')).json();if(state.messages.length)throw Error('Selection dispatched');
  if(label==='desktop'){
    await composer.dispatchEvent('compositionstart');await composer.press('Enter');
    const untouched=await (await context.request.get('http://127.0.0.1:45860/api/demo/session')).json();if(untouched.messages.length)throw Error('IME Enter dispatched');
    await composer.dispatchEvent('compositionend');
  }
  await page.getByRole('button',{name:'Send message'}).click();
  await expect(page.getByRole('article',{name:'Juniper reply'}).last()).toContainText('occupied');
  await expect(page.locator('.answer-passages')).toContainText('separate safe room');
  const reader=page.getByRole('complementary',{name:'Document reader'});await expect(reader).toBeVisible();
  await expect(reader.locator('canvas')).toHaveAttribute('data-rendered-page',/^[1-9]$/,{timeout:20000});
  await page.waitForFunction(()=>document.getAnimations().every(animation=>animation.playState==='finished'));
  await page.screenshot({path:`.runtime/screens/chat-source-${label}.png`});
  await reader.getByRole('button',{name:'Close document reader'}).click();
  const calendar=page.getByRole('region',{name:'Available appointments'});await expect(calendar).toContainText('Both cleaners are booked.');
  state=await (await context.request.get('http://127.0.0.1:45860/api/demo/session')).json();
  await calendar.locator(`[data-date="${state.scenario.alternative_date}"]`).click();
  await calendar.locator('.time-options button').first().click();
  await expect(page.getByRole('status',{name:'Quote total'})).toContainText('185.00');
  await page.getByRole('button',{name:'Questions to try'}).click();
  if(await page.locator('.question-bank section>button').count()<18)throw Error('Question bank missing');
  await page.locator('.question-bank').getByRole('button',{name:'What cleaning supplies do you use?',exact:false}).click();
  await composer.press('Shift+Enter');await expect(composer).toHaveValue(/\n$/);
  await composer.press('Enter');await expect(page.getByRole('article',{name:'Juniper reply'}).last()).toContainText('From Juniper');
  await expect(reader).toBeVisible();await reader.getByRole('button',{name:'Close document reader'}).click();
  await expect(page.getByRole('status',{name:'Quote total'})).toContainText('185.00');
  await page.getByRole('checkbox',{name:'I’ve reviewed this quote.'}).check();
  await page.getByRole('button',{name:'Send request',exact:true}).click();
  await expect(page.getByText('Your request has been sent to Juniper.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Review in Business view',exact:true}).click();
  await page.getByRole('checkbox',{name:'I’ve reviewed this request.'}).check();
  await page.getByRole('button',{name:'Approve and book',exact:true}).click();
  await expect(page.getByRole('button',{name:'Reschedule',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Customer view',exact:true}).click();
  await expect(reader).toHaveCount(0);
  await expect(page.getByText('Booking confirmed',{exact:true})).toBeVisible();
  await expect(page.getByText('CRM not connected. No records were sent.',{exact:true})).toBeVisible();
  await page.locator('.booking-outcome').scrollIntoViewIfNeeded();
  await page.waitForFunction(()=>document.getAnimations().every(animation=>animation.playState==='finished'));
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);if(overflow||errors.length)throw Error(JSON.stringify({label,overflow,errors}));
  await page.screenshot({path:`.runtime/screens/chat-booked-${label}.png`});
  results.push({label,busyFirst:true,sources:true,questionBank:true,keyboard:true,context:true,booking:true,overflow,errors});await context.close();
 }
 const context=await browser.newContext({viewport:{width:390,height:844},timezoneId:'Pacific/Auckland'});const page=await context.newPage();await page.goto('http://127.0.0.1:45860/demo/workspace');
 await page.getByRole('button',{name:'Find a regular clean',exact:false}).click();await page.getByRole('button',{name:'Send message'}).click();
 await expect(page.getByRole('region',{name:'Available appointments'})).toBeVisible();await expect(page.getByRole('status',{name:'Quote total'})).toContainText('60.00');
 await page.waitForFunction(()=>document.getAnimations().every(animation=>animation.playState==='finished'));
 await page.screenshot({path:'.runtime/screens/chat-open-week-phone.png'});await context.close();
 writeFileSync('.runtime/chat-browser-check.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results));
}finally{await browser.close();}
