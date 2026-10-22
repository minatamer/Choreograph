import {chromium,expect} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
import {preparedRequest} from './browser-fixtures.mjs';

const origin='http://127.0.0.1:45860';
const retiredOnly=process.argv.includes('--retired-upload-only');
const improved=process.argv.includes('--after');
const mode=retiredOnly?'retired-upload':improved?'after':'baseline';
const output=`.runtime/performance-browser-${mode}.json`;
const evidence={profile:'local-existing-frontend-fake',browserOnlyPendingStatusInjection:!retiredOnly,
  mode,guestContexts:1,guestWorkspaces:1,source:[],polling:[],checks:{}};
let stage='browser';let browser;let context;
const counters=Object.fromEntries(['source','detail','availability','session','worker'].map(name=>[name,{started:0,completed:0,failed:0}]));
const inFlight=new Set();
function classify(url){
  const {pathname}=new URL(url);
  if(/^\/api\/demo\/documents\/[0-9a-f-]{36}\/source$/.test(pathname))return 'source';
  if(/^\/api\/demo\/documents\/[0-9a-f-]{36}$/.test(pathname))return 'detail';
  if(/^\/api\/demo\/(?:requests\/[0-9a-f-]{36}\/)?availability$/.test(pathname))return 'availability';
  if(pathname==='/api/demo/session')return 'session';
  if(pathname==='/vendor/pdfjs/pdf.worker.min.mjs')return 'worker';
}
const snapshot=()=>structuredClone(counters);
async function retiredUpload(page,workspace){
  let sampleHeld=false,sampleReleased=false,sampleAborted=false,chatHeld=false,replacePOSTs=0;
  let releaseSample,releaseChat;
  const sampleGate=new Promise(resolve=>{releaseSample=resolve;});
  const chatGate=new Promise(resolve=>{releaseChat=resolve;});
  const errors=[];page.on('pageerror',()=>errors.push('PAGE_ERROR'));
  page.on('request',request=>{if(new URL(request.url()).pathname==='/api/demo/documents/preparation/replace'&&request.method()==='POST')replacePOSTs++;});
  page.on('requestfailed',request=>{if(new URL(request.url()).pathname==='/samples/preparation-guide-v2.pdf')sampleAborted=true;});
  try{
    stage='retired-upload-prepare';
    await page.goto(`${origin}/demo/workspace?view=business`);
    await expect(page.locator('.document-card')).toHaveCount(6);
    await page.route('**/samples/preparation-guide-v2.pdf',async route=>{
      const response=await route.fetch();expect(response.status()).toBe(200);sampleHeld=true;
      await sampleGate;
      try{await route.fulfill({response});}catch{/* The retired sample fetch is expected to be aborted. */}
      sampleReleased=true;
    });
    await page.getByRole('button',{name:'Use revised preparation guide',exact:true}).click();
    await expect.poll(()=>sampleHeld,{timeout:20_000}).toBe(true);
    stage='retired-upload-reset';
    page.once('dialog',dialog=>dialog.accept());
    await page.getByRole('button',{name:'Reset demo',exact:true}).click();
    await expect(page.getByRole('button',{name:'Reset demo',exact:true})).toBeEnabled();
    let next;
    await expect.poll(async()=>{
      next=await (await context.request.get(`${origin}/api/demo/session`)).json();return next.workspace_id!==workspace;
    }).toBe(true);
    expect(next.profile).toBe('fake');expect(next.crm_mode).toBe('skipped');expect(next.connection).toBeNull();
    await expect.poll(()=>sampleAborted).toBe(true);
    stage='retired-upload-new-operation';
    await page.route('**/api/demo/chat',async route=>{
      const response=await route.fetch();expect(response.status()).toBe(200);chatHeld=true;
      await chatGate;await route.fulfill({response});
    });
    await page.getByRole('button',{name:'Customer view',exact:true}).click();
    const composer=page.getByRole('textbox',{name:'Ask Juniper'});
    await composer.fill('Hello.');await page.getByRole('button',{name:'Send message'}).click();
    await expect.poll(()=>chatHeld,{timeout:20_000}).toBe(true);
    releaseSample();await expect.poll(()=>sampleReleased).toBe(true);
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    expect(replacePOSTs).toBe(0);evidence.checks.retiredReplacementPOSTs=0;
    releaseChat();await expect(page.getByRole('article',{name:'Juniper reply'})).toHaveCount(1);
    await expect(composer).toHaveValue('');await expect(page.locator('.error-banner')).toHaveCount(0);
    await page.unroute('**/samples/preparation-guide-v2.pdf');await page.unroute('**/api/demo/chat');
    stage='retired-upload-current-replacement';
    await page.getByRole('button',{name:'Business view',exact:true}).click();
    await page.getByRole('button',{name:'Use revised preparation guide',exact:true}).click();
    const preparation=page.locator('.document-card').filter({has:page.getByRole('heading',{name:'Preparation Guide',exact:true})});
    await expect(preparation).toContainText('Guest 1');expect(replacePOSTs).toBe(1);
    const current=await (await context.request.get(`${origin}/api/demo/session`)).json();
    expect(current.workspace_id).toBe(next.workspace_id);expect(current.replacements_left).toBe(2);
    expect(current.crm_mode).toBe('skipped');expect(current.connection).toBeNull();
    await expect(page.locator('.error-banner')).toHaveCount(0);expect(errors).toHaveLength(0);
    evidence.guestWorkspaces=2;evidence.checks.sampleFetchAbortedOnReset=true;
    evidence.checks.newWorkspaceOperationNotAborted=true;evidence.checks.currentReplacementWorks=true;
    evidence.checks.currentReplacementPOSTs=1;evidence.checks.pageErrors=0;evidence.checks.noCRMInstallation=true;
  }finally{releaseSample();releaseChat();}
}
try{
  browser=await chromium.launch({headless:true});
  context=await browser.newContext({viewport:{width:1440,height:900},timezoneId:'Africa/Cairo',locale:'en-US'});
  const start=await context.request.post(`${origin}/api/demo/session`,{headers:{origin},data:{timezone:'Africa/Cairo'}});
  expect(start.status()).toBe(200);
  const initial=await start.json();expect(initial.profile).toBe('fake');expect(initial.timezone).toBe('Africa/Cairo');
  const skip=await context.request.post(`${origin}/api/demo/crm/skip`,{
    headers:{origin,'x-csrf-token':initial.csrf,'idempotency-key':crypto.randomUUID()},
    data:{generation:initial.generation,revision:initial.revision},
  });
  expect(skip.status()).toBe(200);expect((await skip.json()).state.crm_mode).toBe('skipped');
  if(retiredOnly){await retiredUpload(await context.newPage(),initial.workspace_id);evidence.passed=true;}
  else{
  const fixture=await preparedRequest(context);
  expect(fixture.state.profile).toBe('fake');expect(fixture.state.connection).toBeNull();expect(fixture.state.crm_mode).toBe('skipped');
  const guide=fixture.state.documents.find(row=>row.slot==='service');expect(guide?.pages).toBe(2);
  const page=await context.newPage();const pageErrors=[];
  page.on('pageerror',()=>pageErrors.push('PAGE_ERROR'));
  page.on('request',request=>{const kind=classify(request.url());if(kind){counters[kind].started++;if(kind!=='session')inFlight.add(request);}});
  for(const event of ['requestfinished','requestfailed'])page.on(event,request=>{
    const kind=classify(request.url());if(kind){counters[kind][event==='requestfinished'?'completed':'failed']++;inFlight.delete(request);}
  });
  async function settle(){
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    await expect.poll(()=>inFlight.size,{timeout:20_000}).toBe(0);
  }
  stage='document-initial';
  await page.goto(`${origin}/demo/workspace?view=business`);
  const card=page.locator('.document-card').filter({has:page.getByRole('heading',{name:'Service Guide',exact:true})});
  const read=card.getByRole('button',{name:'Read guide',exact:true});await read.click();
  const reader=page.getByRole('complementary',{name:'Document reader'});const canvas=reader.locator('canvas');
  async function rendered(number){
    await expect(canvas).toHaveAttribute('data-rendered-page',String(number),{timeout:20_000});
    await expect(reader.getByText('Loading page…',{exact:true})).toHaveCount(0,{timeout:20_000});
    await expect(reader.locator('.supported-excerpt mark')).not.toBeEmpty();
    await settle();
  }
  async function sourceStep(name,action,number=1){
    stage=`document-${name}`;await action();await rendered(number);
    evidence.source.push({step:name,counts:snapshot(),canvasPage:number,excerpt:true});
  }
  await rendered(1);evidence.source.push({step:'initial',counts:snapshot(),canvasPage:1,excerpt:true});
  const initialSource=counters.source.started;const initialDetail=counters.detail.started;
  for(const [name,value] of [['zoom125','1.25'],['zoom150','1.5']])await sourceStep(name,async()=>{
    const before=await canvas.evaluate(node=>node.width);
    await reader.getByLabel('Zoom').selectOption(value);
    await expect.poll(()=>canvas.evaluate(node=>node.width),{timeout:20_000}).toBeGreaterThan(before);
  });
  await sourceStep('page2',()=>reader.getByRole('button',{name:'Next',exact:true}).click(),2);
  await expect(reader.locator('.supported-excerpt')).toContainText('Carpet shampooing');
  const ink=await canvas.evaluate(node=>{
    const pixels=node.getContext('2d').getImageData(0,0,node.width,node.height).data;let count=0;
    for(let i=0;i<pixels.length;i+=4)if(pixels[i]<180&&pixels[i+1]<180&&pixels[i+2]<180)count++;
    return count;
  });expect(ink).toBeGreaterThan(500);
  await sourceStep('page1',()=>reader.getByRole('button',{name:'Previous',exact:true}).click());
  for(const [name,width,height] of [['short-laptop',1280,720],['narrow',640,740],['phone',390,844]]){
    await sourceStep(name,async()=>{
      const before=await reader.locator('.source-page').evaluate(node=>node.getBoundingClientRect().width);
      await page.setViewportSize({width,height});
      if(width<700)await expect.poll(()=>reader.locator('.source-page').evaluate(node=>node.getBoundingClientRect().width)).not.toBe(before);
    });
  }
  if(improved)await sourceStep('rapid-render-cancellation',async()=>{
    await reader.getByLabel('Zoom').selectOption('1');
    await reader.getByRole('button',{name:'Next',exact:true}).click();
    await reader.getByRole('button',{name:'Previous',exact:true}).click();
  });
  evidence.checks.actualMultipageCanvas=true;evidence.checks.zoomAndResponsiveCanvas=true;
  evidence.checks.sourceRequestsAfterInitial=counters.source.started-initialSource;
  evidence.checks.detailRequestsAfterInitial=counters.detail.started-initialDetail;
  if(improved){expect(initialSource).toBe(1);expect(counters.source.started).toBe(1);expect(counters.detail.started).toBe(initialDetail);}
  stage='document-close-focus';
  await reader.getByRole('button',{name:'Close document reader'}).click();
  await expect(reader).toHaveCount(0);await expect(read).toBeFocused();
  evidence.checks.closeReturnsFocus=true;

  stage='calendar-prepare';
  // One real guest/request; only the browser-visible CRM state is injected below.
  const current=await (await context.request.get(`${origin}/api/demo/session`)).json();
  expect(current.crm_mode).toBe('skipped');expect(current.connection).toBeNull();
  const chat=await context.request.post(`${origin}/api/demo/chat`,{
    headers:{origin,'x-csrf-token':current.csrf,'idempotency-key':crypto.randomUUID()},
    data:{generation:current.generation,revision:current.revision,text:'When is this service free this week?'},
  });expect(chat.status()).toBe(200);
  let polls=0;let fulfilled=0;let releaseFirst;
  const gate=new Promise(resolve=>{releaseFirst=resolve;});
  const injectedRevisions=[];
  await page.route('**/api/demo/session',async route=>{
    const response=await route.fetch();expect(response.status()).toBe(200);
    const body=await response.json();expect(body.profile).toBe('fake');expect(body.crm_mode).toBe('skipped');expect(body.connection).toBeNull();
    if(route.request().method()==='GET'){
      polls++;if(polls===1)await gate;
      injectedRevisions.push(body.revision);
    }
    if(route.request().method()==='POST'||polls<=3)body.requests.find(row=>row.id===fixture.requestId).crm_state='pending';
    await route.fulfill({response,json:body});
    if(route.request().method()==='GET')fulfilled++;
  });
  await page.setViewportSize({width:1280,height:720});
  await page.goto(`${origin}/demo/workspace`);
  const calendar=page.getByRole('region',{name:'Available appointments'});
  await expect(calendar.locator('.calendar-day')).toHaveCount(7,{timeout:20_000});await settle();
  const beforePolls=counters.availability.started;
  evidence.polling.push({step:'initial',availabilityRequests:beforePolls,fulfilledPolls:0});
  releaseFirst();
  for(let number=1;number<=4;number++){
    stage=number<=3?`poll-${number}`:'poll-restore';
    await expect.poll(()=>fulfilled,{timeout:12_000}).toBeGreaterThanOrEqual(number);
    await settle();await expect(calendar.locator('.calendar-day')).toHaveCount(7);
    evidence.polling.push({step:number<=3?`pending-${number}`:'restored-real-status',
      availabilityRequests:counters.availability.started,fulfilledPolls:fulfilled});
  }
  await page.unroute('**/api/demo/session');
  expect(polls).toBe(4);expect(new Set(injectedRevisions).size).toBe(1);
  const persisted=await (await context.request.get(`${origin}/api/demo/session`)).json();
  expect(persisted.crm_mode).toBe('skipped');expect(persisted.connection).toBeNull();
  expect(persisted.requests.find(row=>row.id===fixture.requestId).crm_state).toBe('not_connected');
  evidence.checks.unchangedRevisionPolls=3;evidence.checks.realStatusRestored=true;
  evidence.checks.availabilityRequestsDuringPolling=counters.availability.started-beforePolls;
  if(improved)expect(counters.availability.started).toBe(beforePolls);
  evidence.countsBeforeLifetime=snapshot();
  if(improved){
    stage='private-pdf-lifetime';
    await page.setViewportSize({width:1440,height:900});
    await page.getByRole('button',{name:'Business view',exact:true}).click();
    const preparation=page.locator('.document-card').filter({has:page.getByRole('heading',{name:'Preparation Guide',exact:true})});
    await page.getByRole('button',{name:'Use revised preparation guide',exact:true}).click();
    await expect(preparation).toContainText('Guest 1');
    await preparation.getByRole('button',{name:'Read guide',exact:true}).click();
    await rendered(1);await expect(reader.locator('.source-toolbar small')).toContainText('Guest 1');
    await expect(reader.locator('.source-toolbar small')).toContainText('Your replacement');
    stage='replacement-closes-retired-reader';
    // A file-input change exercises the ordinary replacement handler while the
    // older reader is mounted; no server response or authorization is invented.
    const text='Fictional private preparation guide\nPets stay with a trusted neighbour outside the home during cleaning. Keep the front entrance clear for the cleaner.\n';
    await preparation.locator('input[type="file"]').setInputFiles({name:'preparation.txt',mimeType:'text/plain',buffer:Buffer.from(text)});
    await expect(preparation).toContainText('Guest 2');await expect(reader).toHaveCount(0);
    await preparation.getByRole('button',{name:'Read guide',exact:true}).click();
    await expect(reader.locator('.text-source')).toContainText('trusted neighbour outside the home');
    await expect(reader.locator('canvas')).toHaveCount(0);
    evidence.checks.retiredReplacementReaderCloses=true;evidence.checks.newTextSourceOpens=true;
    const sample=await context.request.get(`${origin}/samples/preparation-guide-v2.pdf`);expect(sample.status()).toBe(200);
    await preparation.locator('input[type="file"]').setInputFiles({name:'preparation.pdf',mimeType:'application/pdf',buffer:await sample.body()});
    await expect(preparation).toContainText('Guest 3');await expect(reader).toHaveCount(0);
    await preparation.getByRole('button',{name:'Read guide',exact:true}).click();
    await rendered(1);await expect(reader.locator('.source-toolbar small')).toContainText('Guest 3');
    await expect(reader.locator('.source-toolbar small')).toContainText('Your replacement');
    const beforeReset=await (await context.request.get(`${origin}/api/demo/session`)).json();
    const privateVersion=beforeReset.documents.find(row=>row.slot==='preparation');expect(privateVersion.private).toBe(true);
    stage='reset-closes-private-reader';
    page.once('dialog',dialog=>dialog.accept());
    // Dispatch the real reset button's handler while the desktop reader remains
    // mounted; its overlay can cover the footer's pointer position.
    await page.getByRole('button',{name:'Reset demo',exact:true}).dispatchEvent('click');
    await expect(reader).toHaveCount(0);await expect(preparation).not.toContainText('Guest');
    const reset=await (await context.request.get(`${origin}/api/demo/session`)).json();
    expect(reset.workspace_id).not.toBe(beforeReset.workspace_id);expect(reset.profile).toBe('fake');
    expect(reset.timezone).toBe('Africa/Cairo');expect(reset.connection).toBeNull();
    expect(reset.documents.every(row=>!row.private)).toBe(true);
    const denied=await context.request.get(`${origin}/api/demo/documents/${privateVersion.id}/source`);
    expect(denied.status()).toBe(404);expect((await denied.json()).code).toBe('SOURCE_UNAVAILABLE');
    await preparation.getByRole('button',{name:'Read guide',exact:true}).click();
    await rendered(1);await expect(reader.locator('.source-toolbar small')).toContainText('Juniper sample');
    await expect(reader.locator('.source-toolbar small')).not.toContainText('Guest');
    await page.keyboard.press('Escape');await expect(reader).toHaveCount(0);
    evidence.guestWorkspaces=2;evidence.checks.resetUnmountsPrivateReader=true;
    evidence.checks.newWorkspaceReadsCurrentSample=true;evidence.checks.oldPrivateSourceDenied=true;
  }
  expect(pageErrors).toHaveLength(0);evidence.checks.pageErrors=0;
  evidence.checks.noCRMInstallation=true;evidence.counts=snapshot();evidence.passed=true;
  }
}catch(error){
  const line=Number(error?.stack?.match(/inspect-performance\.mjs:(\d+):\d+/)?.[1])||undefined;
  evidence.passed=false;evidence.failure={code:'PERFORMANCE_BROWSER_CHECK_FAILED',stage,line};process.exitCode=1;
}finally{
  await context?.close();await browser?.close();
  mkdirSync('.runtime',{recursive:true});writeFileSync(output,JSON.stringify(evidence,null,2)+'\n');
  console.log(JSON.stringify({passed:evidence.passed,profile:evidence.profile,mode:evidence.mode,
    checks:evidence.checks,failure:evidence.failure,output}));
}
