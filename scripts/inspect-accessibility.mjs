import {chromium,expect} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
import {preparedRequest} from './browser-fixtures.mjs';

// Local fake-provider interaction checks. A shortened viewport approximates the
// space left by a phone keyboard; it does not prove native mobile IME behavior.
const origin='http://127.0.0.1:45860';
const retryOnly=process.argv.includes('--retry-only');
const pendingOnly=process.argv.includes('--pending-only');
const timezoneOnly=process.argv.includes('--timezone-only');
const focused=retryOnly||pendingOnly||timezoneOnly;
const output=timezoneOnly?'.runtime/accessibility-timezone-check.json':pendingOnly?'.runtime/accessibility-pending-check.json':retryOnly?'.runtime/accessibility-retry-check.json':'.runtime/accessibility-browser-check.json';
mkdirSync('.runtime/screens',{recursive:true});
const browser=await chromium.launch({headless:true});
const results=[];
const focus=page=>page.evaluate(()=>({
  tag:document.activeElement?.tagName,
  label:document.activeElement?.getAttribute('aria-label')??'',
  text:document.activeElement?.tagName==='BODY'?'':document.activeElement?.textContent?.trim().slice(0,80),
}));
async function withinViewport(locator){
  await locator.scrollIntoViewIfNeeded();
  await expect.poll(()=>locator.evaluate(node=>{
    const r=node.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1&&r.top>=0&&r.bottom<=innerHeight+1;
  })).toBe(true);
}
async function session(context){return (await context.request.get(origin+'/api/demo/session')).json();}
async function check(row,name,action){
  try{await action();row.checks.push({name,passed:true});}
  catch(error){row.checks.push({name,passed:false,error:error.message.split('\n').slice(0,4).join(' ').slice(0,500)});}
}
async function retryCheck(row,context,page,edited=false){
  await check(row,edited?'retry keeps a newer unsent composer edit':'network error preserves text; keyboard retry sends once and clears accepted text',async()=>{
    const composer=page.getByRole('textbox',{name:'Ask Juniper'});const failedText='How do you clean a kitchen?';
    const newerText='Do I need to provide equipment?';const previous=(await session(context)).messages.length;
    await composer.fill(failedText);await page.route('**/api/demo/chat',route=>route.abort('failed'),{times:1});
    await composer.press('Enter');const alert=page.locator('.error-banner[role="alert"]');await expect(alert).toContainText('Couldn’t reach the front desk. Try again.');
    await expect(composer).toHaveValue(failedText);
    if((await session(context)).messages.length!==previous)throw Error('Aborted chat changed accepted state');
    if(edited)await composer.fill(newerText);
    const retry=alert.getByRole('button',{name:'Try again',exact:true});await retry.focus();await withinViewport(retry);
    await page.screenshot({path:`.runtime/screens/accessibility-error-${row.label}.png`});
    await page.keyboard.press('Enter');await expect(alert).toHaveCount(0);
    await expect(page.getByRole('article',{name:'Juniper reply'})).toHaveCount(previous/2+1);
    const accepted=await session(context);if(accepted.messages.length!==previous+2)throw Error('Retry duplicated or lost exchange');
    await expect(page.getByRole('article',{name:'Your message'}).last()).toContainText(failedText);
    await expect(composer).toHaveValue(edited?newerText:'');
    row.observations.composerAfterRetry=await composer.inputValue();
  });
}
try{
  for(const [label,width,height] of focused?[]:[['desktop',1440,900],['short',1280,720],['tablet',768,1024],['phone',390,844],['small-phone',320,740]]){
    const context=await browser.newContext({viewport:{width,height},timezoneId:'Africa/Cairo',locale:'en-US'});
    const page=await context.newPage();const row={label,width,height,checks:[],errors:[],observations:{}};results.push(row);
    page.on('pageerror',()=>row.errors.push('PAGE_ERROR'));
    await page.goto(origin+'/demo/workspace');
    const composer=page.getByRole('textbox',{name:'Ask Juniper'});await expect(composer).toBeVisible();
    await check(row,'three editable starters require explicit Send',async()=>{
      await expect(page.locator('.chat-starters button')).toHaveCount(3);
      const starter=page.getByRole('button',{name:'Moving out, with pets',exact:false});
      await starter.focus();await page.keyboard.press('Enter');await expect(composer).toBeFocused();
      await expect(composer).toHaveValue(/two-bedroom/);
      if((await session(context)).messages.length)throw Error('Starter dispatched without Send');
    });
    await check(row,'question bank is discoverable and keyboard navigable',async()=>{
      const toggle=page.getByRole('button',{name:'Questions to try'});await toggle.focus();await page.keyboard.press('Enter');
      await expect(toggle).toHaveAttribute('aria-expanded','true');
      const choices=page.locator('.question-bank section>button');const count=await choices.count();
      row.observations.questionCount=count;if(count<18)throw Error('Fewer than eighteen questions');
      for(let i=0;i<count;i++){await page.keyboard.press('Tab');await expect(choices.nth(i)).toBeFocused();}
      await choices.filter({hasText:'What cleaning supplies do you use?'}).focus();await page.keyboard.press('Enter');
      await expect(composer).toBeFocused();await expect(composer).toHaveValue('What cleaning supplies do you use?');
      await expect(page.locator('.question-bank')).toHaveCount(0);
    });
    await check(row,'IME Enter does not send; Shift+Enter adds a line; Enter sends once',async()=>{
      await composer.dispatchEvent('compositionstart');await page.keyboard.press('Enter');
      if((await session(context)).messages.length)throw Error('Composition Enter dispatched');
      await composer.dispatchEvent('compositionend');
      await composer.dispatchEvent('keydown',{key:'Enter',code:'Enter',isComposing:true});
      if((await session(context)).messages.length)throw Error('Native composing key dispatched');
      await composer.press('Shift+Enter');await expect(composer).toHaveValue(/\n$/);
      await composer.press('Enter');await expect(page.getByRole('article',{name:'Juniper reply'})).toHaveCount(1);
      if((await session(context)).messages.length!==2)throw Error('Enter did not produce exactly one exchange');
      await expect(composer).toHaveValue('');
    });
    const reader=page.getByRole('complementary',{name:'Document reader'});
    await expect(reader).toBeVisible();await expect(reader.locator('canvas')).toHaveAttribute('data-rendered-page',/^[1-9]$/,{timeout:20000});
    await check(row,'source overlay cycles keyboard focus on narrow screens',async()=>{
      if(width>900)return;
      const close=reader.getByRole('button',{name:'Close document reader'});await expect(close).toBeFocused();
      await page.keyboard.press('Shift+Tab');await expect(reader.locator('select')).toBeFocused();
      await page.keyboard.press('Tab');await expect(close).toBeFocused();
    });
    await page.screenshot({path:`.runtime/screens/accessibility-source-${label}.png`});
    await check(row,'closing automatically opened source returns to composer',async()=>{
      await page.keyboard.press('Escape');await expect(reader).toHaveCount(0);row.observations.autoReaderReturn=await focus(page);
      await expect(composer).toBeFocused({timeout:1500});
    });
    await check(row,'citation source returns keyboard focus to the citation',async()=>{
      const citation=page.locator('.answer-passages button').first();await citation.focus();await page.keyboard.press('Enter');
      await expect(reader).toBeVisible();if(width<=900)await expect(reader.getByRole('button',{name:'Close document reader'})).toBeFocused();
      await page.keyboard.press('Escape');await expect(reader).toHaveCount(0);row.observations.citationReturn=await focus(page);
      await expect(citation).toBeFocused({timeout:1500});
    });
    await check(row,'composer and Send remain reachable in the available viewport',async()=>{
      if(width<=390)await page.setViewportSize({width,height:420});
      await composer.fill('How do you clean a kitchen?');await composer.focus();await withinViewport(composer);
      await page.keyboard.press('Tab');const send=page.getByRole('button',{name:'Send message'});await expect(send).toBeFocused();await withinViewport(send);
      row.observations.sendViewport=await send.boundingBox();
      await page.screenshot({path:`.runtime/screens/accessibility-composer-${label}.png`});
      if(width<=390)await page.setViewportSize({width,height});
    });
    await retryCheck(row,context,page);
    await check(row,'no horizontal document overflow or uncaught browser errors',async()=>{
      if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('Horizontal document overflow');
      if(row.errors.length)throw Error('Uncaught browser error');
    });
    await context.close();
  }
  if(!focused){
  const context=await browser.newContext({viewport:{width:320,height:740},timezoneId:'Africa/Cairo'});const page=await context.newPage();
  const fallback={label:'small-phone-source-fallback',checks:[],errors:[]};results.push(fallback);
  await page.goto(origin+'/demo/workspace');const composer=page.getByRole('textbox',{name:'Ask Juniper'});await expect(composer).toBeVisible();
  await page.route('**/api/demo/documents/*/source',route=>route.abort('failed'));
  await composer.fill('What cleaning supplies do you use?');await composer.press('Enter');
  await check(fallback,'unavailable PDF keeps the actual supported excerpt and a reachable return',async()=>{
    const reader=page.getByRole('complementary',{name:'Document reader'});await expect(reader).toContainText('The page could not be displayed. The supported passage is available below.');
    await expect(reader.locator('.supported-excerpt mark')).not.toBeEmpty();
    const close=reader.getByRole('button',{name:'Close document reader'});await withinViewport(close);
    await page.screenshot({path:'.runtime/screens/accessibility-source-fallback-small-phone.png'});
    await close.press('Enter');await expect(reader).toHaveCount(0);await expect(composer).toHaveValue('');
  });
  await context.close();
  const business=await browser.newContext({viewport:{width:320,height:740},timezoneId:'Africa/Cairo'});const businessPage=await business.newPage();
  const documentReturn={label:'business-document-return',checks:[],errors:[]};results.push(documentReturn);
  await businessPage.goto(origin+'/demo/workspace?view=business');
  await check(documentReturn,'Business guide and text FAQ preserve the initiating control and narrow focus loop',async()=>{
    const cards=businessPage.locator('.document-card');await expect(cards.first()).toBeVisible();
    const selections=[cards.filter({has:businessPage.getByRole('heading',{name:'Service Guide',exact:true})}),cards.filter({hasText:'Text'})];
    for(const card of selections){
      const button=card.getByRole('button',{name:'Read guide'});await button.focus();await businessPage.keyboard.press('Enter');
      const reader=businessPage.getByRole('complementary',{name:'Document reader'});const close=reader.getByRole('button',{name:'Close document reader'});
      await expect(close).toBeFocused();await expect(reader.locator('.source-controls')).toBeVisible();
      await businessPage.keyboard.press('Shift+Tab');
      const last=reader.locator('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),[tabindex="0"]').last();await expect(last).toBeFocused();
      await businessPage.keyboard.press('Tab');await expect(close).toBeFocused();
      await businessPage.keyboard.press('Escape');await expect(reader).toHaveCount(0);await expect(button).toBeFocused();
    }
  });
  await business.close();
  }
  for(const [label,width,height,edited] of pendingOnly||timezoneOnly?[]:retryOnly?[['retry-short',1280,720,false],['retry-small-phone',320,740,false],['retry-edited-small-phone',320,740,true]]:[['retry-edited-small-phone',320,740,true]]){
    const context=await browser.newContext({viewport:{width,height},timezoneId:'Africa/Cairo'});const page=await context.newPage();
    const row={label,width,height,checks:[],errors:[],observations:{}};results.push(row);page.on('pageerror',()=>row.errors.push('PAGE_ERROR'));
    await page.goto(origin+'/demo/workspace');await expect(page.getByRole('textbox',{name:'Ask Juniper'})).toBeVisible();
    await retryCheck(row,context,page,edited);await context.close();
  }
  if(!retryOnly&&!timezoneOnly){
    const context=await browser.newContext({viewport:{width:1280,height:720},timezoneId:'Africa/Cairo'});const page=await context.newPage();
    const row={label:'pending-new-question',width:1280,height:720,checks:[],errors:[],observations:{}};results.push(row);
    page.on('pageerror',()=>row.errors.push('PAGE_ERROR'));
    await page.goto(origin+'/demo/workspace');const composer=page.getByRole('textbox',{name:'Ask Juniper'});await expect(composer).toBeVisible();
    await check(row,'a question chosen while Send is pending survives the accepted response without dispatch',async()=>{
      const sentText='How do you clean a kitchen?';const newerText='Do I need to provide equipment?';
      let release;let processed=false;const held=new Promise(resolve=>{release=resolve;});
      await page.route('**/api/demo/chat',async route=>{const response=await route.fetch();processed=true;await held;await route.fulfill({response});},{times:1});
      try{
        await composer.fill(sentText);await page.getByRole('button',{name:'Questions to try'}).press('Enter');
        await expect(page.locator('.question-bank')).toBeVisible();await composer.press('Enter');
        await expect.poll(()=>processed,{timeout:10000}).toBe(true);await expect(composer).toBeDisabled();
        if((await session(context)).messages.length!==2)throw Error('Server did not process exactly one held exchange');
        await page.locator('.question-bank section>button').filter({hasText:newerText}).press('Enter');
        await expect(composer).toHaveValue(newerText);row.observations.newQuestionPreparedWhilePending=true;
      }finally{release();}
      await expect(composer).toBeEnabled();await expect(composer).toHaveValue(newerText);
      const accepted=await session(context);const sent=accepted.messages.filter(message=>message.role==='user');
      if(accepted.messages.length!==2||sent.length!==1||sent[0].text!==sentText)throw Error('Held Send lost, duplicated or dispatched the newer question');
      row.observations.acceptedExchanges=1;row.observations.composerAfterSend=await composer.inputValue();
      await page.keyboard.press('Escape');await composer.focus();await withinViewport(composer);
      await page.screenshot({path:'.runtime/screens/accessibility-pending-new-question.png'});
    });
    await context.close();
  }
  if(!retryOnly&&!pendingOnly){
    const context=await browser.newContext({viewport:{width:390,height:844},timezoneId:'Africa/Cairo'});const page=await context.newPage();
    const row={label:'synthetic-timezone-detection-refresh',width:390,height:844,checks:[],errors:[],observations:{syntheticTimezoneDetectionUnavailable:true}};results.push(row);
    page.on('pageerror',()=>row.errors.push('PAGE_ERROR'));
    await check(row,'saved guest loads without timezone detection; lost session clears old UI before manual timezone restart',async()=>{
      const prepared=await preparedRequest(context,'Africa/Cairo');const request=prepared.state.requests.find(record=>record.id===prepared.requestId);
      const approval=await context.request.post(origin+`/api/demo/requests/${prepared.requestId}/approve`,{
        headers:{origin,'x-csrf-token':prepared.state.csrf,'idempotency-key':crypto.randomUUID()},
        data:{generation:prepared.state.generation,revision:prepared.state.revision,request_revision:request.revision,confirm:true,staff_id:null},
      });
      if(approval.status()!==200)throw Error('Isolated fake booking setup failed');
      const old=await session(context);if(!old.requests[0]?.booking)throw Error('Expected an actual old booking');
      await context.addInitScript(()=>{
        const original=Intl.DateTimeFormat.prototype.resolvedOptions;
        Intl.DateTimeFormat.prototype.resolvedOptions=function(){return {...original.call(this),timeZone:undefined};};
      });
      await page.goto(origin+'/demo/workspace');const composer=page.getByRole('textbox',{name:'Ask Juniper'});
      await expect(composer).toBeVisible();await expect(page.getByText('Booking confirmed',{exact:true})).toBeVisible();
      if(await page.evaluate(()=>Intl.DateTimeFormat().resolvedOptions().timeZone)!==undefined)throw Error('Synthetic detection override was not applied');
      await composer.fill('How do you clean a kitchen?');await composer.press('Enter');
      await expect(page.getByRole('article',{name:'Juniper reply'})).toHaveCount(1);await page.keyboard.press('Escape');
      await page.route('**/api/demo/chat',route=>route.abort('failed'),{times:1});
      await composer.fill('Do I need to provide equipment?');await composer.press('Enter');
      const alert=page.locator('.error-banner[role="alert"]');await expect(alert).toContainText('Couldn’t reach the front desk. Try again.');
      await context.clearCookies();await alert.getByRole('button',{name:'Refresh',exact:true}).click();
      await expect(page.getByRole('heading',{name:'Choose your timezone',exact:true})).toBeVisible();
      await expect(page.locator('.booking-outcome')).toHaveCount(0);await expect(page.locator('.chat-message')).toHaveCount(0);
      await expect(composer).toHaveCount(0);await expect(page.getByRole('button',{name:'Business view',exact:true})).toHaveCount(0);
      await expect(alert).toHaveCount(0);await page.screenshot({path:'.runtime/screens/accessibility-timezone-required-phone.png'});
      await page.getByLabel('IANA timezone').fill('Pacific/Auckland');await page.getByRole('button',{name:'Continue',exact:true}).click();
      await expect(composer).toBeVisible();await expect(composer).toHaveValue('');
      const fresh=await session(context);
      if(fresh.workspace_id===old.workspace_id||fresh.timezone!=='Pacific/Auckland'||fresh.messages.length||fresh.requests.length)throw Error('Manual timezone did not start an empty isolated workspace');
      row.observations.savedGuestLoaded=true;row.observations.oldBookingAndChatCleared=true;row.observations.manualTimezoneFreshWorkspace=true;
    });
    await context.close();
  }
}finally{await browser.close();writeFileSync(output,JSON.stringify(results,null,2));}
console.log(JSON.stringify(results.map(({label,checks,errors})=>({label,checks,errors}))));
if(results.some(row=>row.checks.some(check=>!check.passed)||row.errors.length))process.exitCode=1;
