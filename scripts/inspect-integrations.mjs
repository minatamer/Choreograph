// Actual components with an isolated-PG/MockTransport snapshot. UI evidence is
// explicitly injected; this script never authorizes real CRM or AI operations.
import {chromium,expect} from '@playwright/test';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
const origin='http://127.0.0.1:45860';
const fixture=JSON.parse(readFileSync(process.argv[2]??'.runtime/sbs013-ui.json','utf8'));
if(fixture.profile!=='injected-HTTP-isolated-PG-snapshot'||fixture.state.connection?.state!=='setup')throw Error('ISOLATED_SETUP_FIXTURE_REQUIRED');
mkdirSync('.runtime/screens',{recursive:true});
const evidence={profile:'actual-components-injected-HTTP-snapshot',liveCalls:0,viewports:[],resetDuringWait:false};
const browser=await chromium.launch({headless:true});
try{
 for(const [label,width,height] of [['desktop',1440,900],['short',1280,720],['phone',390,844]]){
  const context=await browser.newContext({viewport:{width,height},timezoneId:'UTC'});
  let state=structuredClone(fixture.state),chatWaiting,releaseChat;
  const waiting=new Promise(resolve=>chatWaiting=resolve);
  await context.route(`${origin}/api/demo/**`,async route=>{
   const path=new URL(route.request().url()).pathname.replace('/api/demo/','');
   if(path==='session')return route.fulfill({json:state});
   if(path==='crm/setup'){
    const body=route.request().postDataJSON();
    expect(body.pipeline_id).toBe('visitor-pipeline');expect(body.stage_id).toBe('queue');expect(body.allow_schema).toBe(true);
    state={...state,revision:state.revision+1,connection:{...state.connection,state:'ready',destinations:[],destination_label:'Visitor bookings'}};
    return route.fulfill({json:{state,replayed:false,request_id:null,crm_notice:'Destination verified.'}});
   }
   if(path==='chat'){
    chatWaiting();await new Promise(resolve=>releaseChat=resolve);
    try{await route.fulfill({json:{state,replayed:false}});}catch{}
    return;
   }
   if(path==='reset'){
    state={...state,workspace_id:crypto.randomUUID(),generation:1,revision:1,connection:null,crm_mode:'skipped',messages:[]};
    return route.fulfill({json:state});
   }
   return route.fulfill({status:503,json:{code:'INJECTED_ROUTE_UNAVAILABLE',message:'Synthetic UI fixture.'}});
  });
  const page=await context.newPage();const errors=[];page.on('pageerror',()=>errors.push('PAGE_ERROR'));page.on('dialog',dialog=>void dialog.accept());
  await page.goto(origin+'/demo');
  await expect(page.getByRole('heading',{name:'Choose a booking destination'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Verify destination'})).toBeDisabled();
  await page.getByRole('combobox',{name:/^Pipeline/}).selectOption('visitor-pipeline');
  await page.getByRole('combobox',{name:/^Stage/}).selectOption('queue');
  const schema=page.getByRole('checkbox',{name:'Create Choreograph demo ID fields in contacts and deals if needed.'});
  await expect(schema).not.toBeChecked();await schema.check();
  const verify=page.getByRole('button',{name:'Verify destination'});await verify.scrollIntoViewIfNeeded();
  const box=await verify.boundingBox();expect(box.y).toBeGreaterThanOrEqual(0);expect(box.y+box.height).toBeLessThanOrEqual(height+1);
  await page.evaluate(()=>document.fonts.ready);
  const file=`.runtime/screens/integration-setup-${label}.png`;
  await page.locator('.crm-controls').screenshot({path:file});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)).toBe(false);
  await verify.click();await expect(page.getByRole('heading',{name:'Your CRM connection'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Allow demo records'})).toBeDisabled();
  await expect(page.getByRole('checkbox',{name:'Allow these fictional contact and booking records in this account.'})).not.toBeChecked();
  await page.goto(origin+'/demo/workspace');
  await expect(page.getByText('Sample mode',{exact:true})).toBeVisible();
  const composer=page.getByRole('textbox',{name:'Ask Juniper'});await expect(composer).toBeEnabled();
  await composer.fill('Hello');await page.getByRole('button',{name:'Send message'}).click();await waiting;
  const reset=page.getByRole('button',{name:'Reset demo',exact:true});await expect(reset).toBeEnabled();await reset.click();
  await expect(composer).toBeEnabled();releaseChat();await expect(page.getByRole('article',{name:'Juniper reply'})).toHaveCount(0);
  expect(errors).toEqual([]);evidence.viewports.push({label,width,height,file,setupReachable:true,separateConsent:true,noHorizontalOverflow:true,pageErrors:0});
  evidence.resetDuringWait=true;await context.close();
 }
 writeFileSync('.runtime/integration-browser-review.json',JSON.stringify(evidence,null,2));
 console.log(JSON.stringify(evidence));
}finally{await browser.close();}
