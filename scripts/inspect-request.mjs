import {chromium,expect} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
mkdirSync('.runtime/screens',{recursive:true});
const browser=await chromium.launch({headless:true});const evidence=[];
try{
  for(const [label,width,height,timezoneId] of [['desktop',1440,1000,'Asia/Kathmandu'],['short',1280,720,'Africa/Cairo'],['phone',390,844,'Africa/Cairo'],['small-phone',320,740,'Pacific/Auckland']]){
    if(process.argv[2]&&label!==process.argv[2])continue;
    const context=await browser.newContext({viewport:{width,height},timezoneId,locale:'en-US'});const page=await context.newPage();const errors=[];
    page.on('pageerror',()=>errors.push('PAGE_ERROR'));
    await page.goto('http://127.0.0.1:45860/demo/workspace');
    const cleaning=page.getByLabel('Cleaning',{exact:true}),size=page.getByLabel('Home size',{exact:true});
    await cleaning.selectOption('move-out');await expect(cleaning).toHaveValue('move-out');await expect(size).toBeEnabled();
    await size.selectOption('2');await expect(page.getByLabel('Quote total').filter({hasText:'$160.00'})).toBeVisible();
    await page.getByLabel('Add inside oven').click();await expect(page.getByLabel('Add inside oven')).toBeChecked();await expect(page.getByLabel('Quote total').filter({hasText:'$185.00'})).toBeVisible();
    const state=await (await context.request.get('http://127.0.0.1:45860/api/demo/session')).json();
    const detected=await page.evaluate(()=>Intl.DateTimeFormat().resolvedOptions().timeZone);
    if(state.timezone!==detected)throw Error('Visitor timezone was not saved');
    // The 7-day card can move when the guided day belongs to the following local week.
    let busy=page.locator(`[data-date="${state.scenario.busy_date}"]`);
    if(await busy.count()===0){await page.getByRole('button',{name:'Next week',exact:true}).click();}
    await expect(busy).toBeVisible();await busy.click();await expect(page.getByText('Both cleaners are booked. Choose another day.')).toBeVisible();
    const alternative=page.locator(`[data-date="${state.scenario.alternative_date}"]`);
    if(await alternative.count()===0)await page.getByRole('button',{name:'Next week',exact:true}).click();
    await alternative.click();await page.locator('.time-options button').first().click();
    await expect(page.getByLabel('I’ve reviewed this quote.')).toBeEnabled();
    await page.getByLabel('I’ve reviewed this quote.').check();
    const send=page.getByRole('button',{name:'Send request',exact:true});await send.scrollIntoViewIfNeeded();
    const bounds=await send.boundingBox();if(!bounds||bounds.y<0||bounds.y+bounds.height>height+1)throw Error('Send was unreachable');
    await page.screenshot({path:`.runtime/screens/request-${label}.png`,fullPage:true});
    await send.click();await expect(page.getByText('Your request has been sent to Juniper.')).toBeVisible();
    await page.reload();await expect(page.getByRole('button',{name:'Review in Business view'})).toBeVisible();
    const restored=await (await context.request.get('http://127.0.0.1:45860/api/demo/session')).json();
    if(restored.requests.length!==1||restored.requests[0].status!=='awaiting_review')throw Error('Request restoration failed');
    await page.getByRole('button',{name:'Review in Business view'}).click();await expect(page.getByText('Awaiting review',{exact:true})).toBeVisible();
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth);
    if(overflow||errors.length)throw Error('Responsive request flow failed');
    evidence.push({label,width,height,timezoneId,restored:true,awaitingReview:true,sendReachable:true,errors});await context.close();
  }
}finally{await browser.close();}
writeFileSync('.runtime/request-evidence.json',JSON.stringify(evidence,null,2));console.log(JSON.stringify(evidence));
