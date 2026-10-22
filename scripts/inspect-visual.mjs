import {chromium,expect} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
import {preparedRequest} from './browser-fixtures.mjs';

const origin='http://127.0.0.1:45860';
const evidence={profile:'local-existing-frontend-fake',syntheticSetup:'API-prepared request and guide conversation; actual UI approval',
  guestContexts:1,guestWorkspaces:1,crmSkipped:true,images:[],checks:{}};
let browser,context,stage='browser';
mkdirSync('.runtime/screens',{recursive:true});
try{
  browser=await chromium.launch({headless:true});
  context=await browser.newContext({viewport:{width:1440,height:900},timezoneId:'Africa/Cairo',locale:'en-US'});
  const start=await context.request.post(`${origin}/api/demo/session`,{headers:{origin},data:{timezone:'Africa/Cairo'}});
  expect(start.status()).toBe(200);let state=await start.json();expect(state.profile).toBe('fake');
  async function command(path,fields){
    const response=await context.request.post(`${origin}/api/demo/${path}`,{
      headers:{origin,'x-csrf-token':state.csrf,'idempotency-key':crypto.randomUUID()},
      data:{generation:state.generation,revision:state.revision,...fields},
    });expect(response.status()).toBe(200);state=(await response.json()).state;
  }
  await command('crm/skip',{});expect(state.crm_mode).toBe('skipped');expect(state.connection).toBeNull();
  await command('chat',{text:`I am moving out of my two-bedroom apartment on ${state.scenario.busy_date} at 09:00. Does that include carpet shampooing? I have two cats. Can you do the oven too?`});
  const fixture=await preparedRequest(context);
  expect(fixture.state.crm_mode).toBe('skipped');expect(fixture.state.connection).toBeNull();
  const page=await context.newPage();const pageErrors=[];
  page.on('pageerror',()=>pageErrors.push('PAGE_ERROR'));
  async function settle(){
    await page.evaluate(async()=>{await document.fonts.ready;await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));});
  }
  async function reachable(button,height){
    await button.scrollIntoViewIfNeeded();const box=await button.boundingBox();
    expect(box).not.toBeNull();expect(box.y).toBeGreaterThanOrEqual(-1);expect(box.y+box.height).toBeLessThanOrEqual(height+1);
  }
  async function capture(view,label,width,height,checks={}){
    await settle();
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+1);
    expect(overflow).toBe(false);expect(pageErrors).toHaveLength(0);
    const file=`.runtime/screens/visual-${view}-${label}.png`;
    await page.screenshot({path:file});
    evidence.images.push({view,label,viewport:{width,height},file,noHorizontalOverflow:true,pageErrors:0,...checks});
  }
  const reader=page.getByRole('complementary',{name:'Document reader'});
  async function closeReader(){if(await reader.count()){await reader.getByRole('button',{name:'Close document reader'}).click();await expect(reader).toHaveCount(0);}}

  stage='approval-desktop';
  await page.goto(`${origin}/demo/workspace?view=business`);
  await expect(page.getByRole('heading',{name:'Booking requests',exact:true})).toBeVisible();
  await page.getByRole('checkbox',{name:'I’ve reviewed this request.'}).check();
  const approve=page.getByRole('button',{name:'Approve and book',exact:true});await reachable(approve,900);await expect(approve).toBeEnabled();
  await capture('approval','desktop',1440,900,{approvalReachable:true});
  await approve.click();await expect(page.getByRole('button',{name:'Reschedule',exact:true})).toBeVisible();

  for(const [label,width,height] of [['desktop',1440,900],['short',1280,720],['phone',390,844]]){
    await page.setViewportSize({width,height});
    stage=`landing-${label}`;
    await page.goto(origin);await expect(page.getByRole('heading',{name:'Answer questions. Find a time. Book the job.'})).toBeVisible();
    await capture('landing',label,width,height);

    stage=`customer-${label}`;
    await page.goto(`${origin}/demo/workspace`);
    const composer=page.getByRole('textbox',{name:'Ask Juniper'});await expect(composer).toBeEnabled();
    await closeReader();
    await expect(page.locator('.chat-starters button')).toHaveCount(3);
    await expect(page.getByRole('article',{name:'Juniper reply'})).toHaveCount(1);
    await expect(page.getByText('Booking confirmed',{exact:true})).toBeVisible();
    const calendar=page.getByRole('region',{name:'Available appointments'});await expect(calendar.locator('.calendar-day')).toHaveCount(7);
    await composer.fill('What do I do before the cleaner arrives?');
    const send=page.getByRole('button',{name:'Send message'});await expect(send).toBeEnabled();await reachable(send,height);
    await page.locator('.chat-message.user').first().evaluate(node=>node.scrollIntoView({block:'start',behavior:'instant'}));
    await capture('customer',label,width,height,{sendReachable:true,threeStarters:true,groundedReply:true});
    await calendar.scrollIntoViewIfNeeded();
    await capture('calendar',label,width,height,{sevenDays:true,sendReachable:true});
    await composer.clear();

    stage=`business-${label}`;
    await page.getByRole('button',{name:'Business view',exact:true}).click();
    const record=page.locator('.request-record');await expect(record).toHaveCount(1);
    await expect(record.getByText('Confirmed',{exact:true})).toBeVisible();
    const reschedule=record.getByRole('button',{name:'Reschedule',exact:true});await reachable(reschedule,height);await expect(reschedule).toBeEnabled();
    await record.scrollIntoViewIfNeeded();
    await capture('business',label,width,height,{confirmedBooking:true,bookingActionReachable:true});

    stage=`documents-${label}`;
    await expect(page.locator('.document-card')).toHaveCount(6);
    await page.locator('.documents-area').scrollIntoViewIfNeeded();
    await capture('documents',label,width,height,{sixDocuments:true});
    if(label!=='short'){
      stage=`source-${label}`;
      const guide=page.locator('.document-card').filter({has:page.getByRole('heading',{name:'Service Guide',exact:true})});
      const read=guide.getByRole('button',{name:'Read guide',exact:true});await read.click();
      const canvas=reader.locator('canvas');
      await expect(canvas).toHaveAttribute('data-rendered-page','1',{timeout:20_000});
      await reader.getByRole('button',{name:'Next',exact:true}).click();
      await expect(canvas).toHaveAttribute('data-rendered-page','2',{timeout:20_000});
      await expect(reader.getByText('Loading page…',{exact:true})).toHaveCount(0);
      await expect(reader.locator('.supported-excerpt')).toContainText('Carpet shampooing');
      const ink=await canvas.evaluate(node=>{
        const pixels=node.getContext('2d').getImageData(0,0,node.width,node.height).data;let count=0;
        for(let i=0;i<pixels.length;i+=4)if(pixels[i]<180&&pixels[i+1]<180&&pixels[i+2]<180)count++;
        return count;
      });expect(ink).toBeGreaterThan(500);
      await capture('source-page2',label,width,height,{actualCanvasPage:2,actualInk:true,supportedExcerpt:true});
      await closeReader();await expect(read).toBeFocused();
    }
  }
  stage='persisted-outcome';
  const persisted=await (await context.request.get(`${origin}/api/demo/session`)).json();
  expect(persisted.workspace_id).toBe(fixture.state.workspace_id);expect(persisted.crm_mode).toBe('skipped');expect(persisted.connection).toBeNull();
  const record=persisted.requests.find(row=>row.id===fixture.requestId);expect(record.status).toBe('confirmed');expect(record.crm_state).toBe('not_connected');
  expect(persisted.requests).toHaveLength(1);expect(persisted.replacements_left).toBe(3);expect(pageErrors).toHaveLength(0);
  evidence.checks={oneConfirmedBooking:true,trueCRMSkip:true,noPrivateUploads:true,noPageErrors:true,allCapturesWithoutHorizontalOverflow:true};
  evidence.passed=true;
}catch(error){
  evidence.passed=false;evidence.failure={code:'VISUAL_CAPTURE_FAILED',stage,line:Number(error?.stack?.match(/inspect-visual\.mjs:(\d+):\d+/)?.[1])||undefined};
  process.exitCode=1;
}finally{
  await context?.close();await browser?.close();
  writeFileSync('.runtime/visual-review.json',JSON.stringify(evidence,null,2)+'\n');
  console.log(JSON.stringify({passed:evidence.passed,profile:evidence.profile,images:evidence.images.length,checks:evidence.checks,failure:evidence.failure}));
}
