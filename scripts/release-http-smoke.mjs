// Pipe into the isolated frontend container with: node --input-type=module.
// All requests use this one configured origin; no provider credentials are read.
import {randomUUID} from 'node:crypto';

let stage='configuration';
let requests=0;
let assertions=0;
const checks={};
const assert=(condition)=>{assertions++;if(!condition)throw new Error('SMOKE_ASSERTION');};
const checked=(name,condition)=>{assert(condition);checks[name]=true;};
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

try {
  const origin=new URL(process.env.SMOKE_ORIGIN??'http://frontend:8080');
  assert(['http:','https:'].includes(origin.protocol)&&!origin.username&&!origin.password&&
    origin.pathname==='/'&&!origin.search&&!origin.hash);

  async function boundedBytes(response,max){
    const length=Number(response.headers.get('content-length'));
    assert(!Number.isFinite(length)||length<=max);
    const reader=response.body?.getReader();
    assert(reader);
    const chunks=[];let count=0;
    try {
      while(true){
        const {done,value}=await reader.read();
        if(done)break;
        count+=value.byteLength;
        if(count>max){await reader.cancel();assert(false);}
        chunks.push(value);
      }
    }finally{reader.releaseLock();}
    return Buffer.concat(chunks,count);
  }

  function guest(){return {cookies:new Map(),state:null};}
  async function request(client,path,{method='GET',body,status=200,max=262_144,command=false}={}){
    const url=new URL(path,origin);
    assert(path.startsWith('/')&&url.origin===origin.origin);
    const headers=new Headers({'origin':origin.origin});
    if(client?.cookies.size)headers.set('cookie',[...client.cookies].map(([key,value])=>`${key}=${value}`).join('; '));
    if(body!==undefined)headers.set('content-type','application/json');
    if(command){
      assert(client?.state?.csrf);
      headers.set('x-csrf-token',client.state.csrf);
      headers.set('idempotency-key',randomUUID());
    }
    requests++;
    const response=await fetch(url,{method,headers,body:body===undefined?undefined:JSON.stringify(body),
      redirect:'error',cache:'no-store',signal:AbortSignal.timeout(25_000)});
    for(const cookie of response.headers.getSetCookie()){
      const first=cookie.split(';',1)[0];const split=first.indexOf('=');
      if(client&&split>0&&first.slice(0,split)==='choreograph_guest'){
        assert(/;\s*HttpOnly\b/i.test(cookie)&&/;\s*SameSite=Lax\b/i.test(cookie));
        client.cookies.set(first.slice(0,split),first.slice(split+1));
      }
    }
    const bytes=await boundedBytes(response,max);
    assert(response.status===status);
    return {response,bytes};
  }
  async function json(client,path,options){
    const result=await request(client,path,options);
    assert(result.response.headers.get('content-type')?.includes('application/json'));
    return JSON.parse(result.bytes.toString('utf8'));
  }
  function state(client,value){
    assert(value&&uuid.test(value.workspace_id)&&value.profile==='fake'&&value.timezone==='Africa/Cairo'&&
      Number.isInteger(value.generation)&&value.generation>0&&Number.isInteger(value.revision)&&value.revision>0&&
      typeof value.csrf==='string'&&value.csrf.length>=32);
    if(client.state)assert(client.state.workspace_id===value.workspace_id&&client.state.generation===value.generation);
    client.state=value;return value;
  }
  async function command(client,path,fields={},method='POST'){
    const result=await json(client,`/api/demo/${path}`,{method,command:true,
      body:{generation:client.state.generation,revision:client.state.revision,...fields}});
    assert(result.replayed===false);
    state(client,result.state);return result;
  }
  const calendarFingerprint=(rows)=>rows.map(row=>JSON.stringify([
    row.id,row.enquiry_id,row.staff_id,row.starts_at,row.ends_at,row.state,row.label,
  ])).sort().join('\n');
  const instant=(value)=>new Date(value).getTime();
  function monday(date){
    assert(/^\d{4}-\d{2}-\d{2}$/.test(date));
    const day=new Date(`${date}T12:00:00Z`);
    day.setUTCDate(day.getUTCDate()-((day.getUTCDay()+6)%7));
    return day.toISOString().slice(0,10);
  }

  stage='health';
  const health=await json(null,'/healthz');
  checked('contentFreeHealth',health.status==='ok'&&Object.keys(health).length===1);

  stage='session';
  const first=guest();
  state(first,await json(first,'/api/demo/session',{method:'POST',body:{timezone:'Africa/Cairo'}}));
  const initial=first.state;
  const seeded=calendarFingerprint(initial.calendar);
  checked('isolatedFakeSession',first.cookies.has('choreograph_guest')&&initial.requests.length===0&&
    initial.connection===null&&initial.documents.length===6&&initial.calendar.length>0&&
    initial.calendar.every(row=>row.state==='blocked'));
  stage='crm-skip';
  await command(first,'crm/skip');
  checked('explicitCRMSkip',first.state.crm_mode==='skipped'&&first.state.connection===null);

  stage='grounded-answer';
  const petQuestion='What do I do with my cats?';
  await command(first,'chat',{text:petQuestion});
  const originalPreparation=first.state.documents.find(document=>document.slot==='preparation');
  assert(originalPreparation&&uuid.test(originalPreparation.id));
  const petClaim=first.state.messages.at(-1).claims.find(claim=>claim.version_id===originalPreparation.id&&
    claim.page===1&&claim.excerpt.includes('separate safe room'));
  assert(petClaim&&uuid.test(petClaim.passage_id));
  const detail=await json(first,`/api/demo/documents/${petClaim.version_id}`);
  const passage=detail.passages.find(item=>item.id===petClaim.passage_id);
  checked('groundedPetPassage',passage?.page===petClaim.page&&passage.content.includes(petClaim.excerpt)&&
    detail.document.id===petClaim.version_id&&detail.document.pages>=petClaim.page);
  stage='source-pdf';
  const source=await request(first,`/api/demo/documents/${petClaim.version_id}/source`,{max:2_097_152});
  const sourcePages=(source.bytes.toString('latin1').match(/\/Type\s*\/Page\b/g)??[]).length;
  checked('actualPDFPage',source.response.headers.get('content-type')?.includes('application/pdf')&&
    source.bytes.subarray(0,5).toString()==='%PDF-'&&sourcePages===detail.document.pages&&sourcePages>=petClaim.page);

  stage='busy-quote';
  const busyDate=first.state.scenario.busy_date;
  assert(/^\d{4}-\d{2}-\d{2}$/.test(busyDate));
  await command(first,'chat',{text:`I am moving out of my two-bedroom apartment on ${busyDate} at 09:00. Can you do the oven too?`});
  checked('exactSharedQuote',first.state.quote?.currency==='USD'&&first.state.quote.cents===18500&&
    first.state.quote.minutes===270&&first.state.draft.service==='move-out'&&first.state.draft.bedrooms===2&&
    first.state.draft.oven===true&&first.state.draft.preferred_at===null&&
    first.state.messages.at(-1).text.includes('occupied')&&first.state.messages.at(-1).cards.includes('week')&&
    first.state.requests.length===0&&calendarFingerprint(first.state.calendar)===seeded);
  stage='availability';
  const busyWeek=await json(first,`/api/demo/availability?week=${first.state.scenario.week_start}`);
  const busyDay=busyWeek.days.find(day=>day.date===busyDate);
  checked('persistentOccupiedDate',busyWeek.days.length===7&&busyWeek.timezone==='Africa/Cairo'&&busyWeek.minutes===270&&
    busyDay?.status==='busy'&&busyDay.slots.length===0&&busyDay.occupied.length===2);
  const alternativeDate=first.state.scenario.alternative_date;
  const alternativeWeek=monday(alternativeDate)===busyWeek.week_start?busyWeek:
    await json(first,`/api/demo/availability?week=${monday(alternativeDate)}`);
  const slot=alternativeWeek.days.find(day=>day.date===alternativeDate)?.slots[0];
  assert(slot&&instant(slot.end)-instant(slot.start)===270*60_000&&slot.staff_ids.length>0);
  await command(first,'draft',{preferred_at:slot.start},'PUT');
  checked('selectionDoesNotReserve',instant(first.state.draft.preferred_at)===instant(slot.start)&&
    first.state.requests.length===0&&calendarFingerprint(first.state.calendar)===seeded);

  stage='submit';
  const submitted=await command(first,'requests',{accept_quote:true});
  assert(uuid.test(submitted.request_id));
  const pending=first.state.requests.find(row=>row.id===submitted.request_id);
  checked('explicitSubmission',pending?.status==='awaiting_review'&&pending.booking===null&&
    pending.quote.cents===18500&&pending.quote.minutes===270&&instant(pending.preferred_at)===instant(slot.start)&&
    first.state.requests.length===1&&calendarFingerprint(first.state.calendar)===seeded);
  stage='approve';
  const approved=await command(first,`requests/${pending.id}/approve`,{
    request_revision:pending.revision,confirm:true,staff_id:slot.staff_ids[0],
  });
  const booked=first.state.requests.find(row=>row.id===pending.id);
  const booking=booked?.booking;
  checked('approvalAndCalendarAgree',approved.receipt?.action==='confirmed'&&approved.receipt.status==='accepted'&&
    booked.status==='confirmed'&&booking?.state==='confirmed'&&booking.id===approved.receipt.booking_id&&
    booking.enquiry_id===pending.id&&instant(booking.starts_at)===instant(slot.start)&&
    instant(booking.ends_at)-instant(booking.starts_at)===270*60_000&&booking.staff_id===slot.staff_ids[0]&&
    first.state.calendar.some(row=>row.id===booking.id&&row.enquiry_id===pending.id&&row.state==='confirmed')&&
    calendarFingerprint(first.state.calendar.filter(row=>row.id!==booking.id))===seeded&&
    first.state.summary.confirmed_count===1&&first.state.summary.booked_cents===18500);
  checked('noCRMOutcome',first.state.crm_mode==='skipped'&&first.state.connection===null&&
    booked.crm_state==='not_connected'&&approved.receipt.crm_state==='not_connected'&&
    Object.keys(booked.crm_links).length===0&&booked.crm_receipt===null);
  stage='refresh';
  const confirmedCalendar=calendarFingerprint(first.state.calendar);
  state(first,await json(first,'/api/demo/session'));
  checked('durableRefresh',calendarFingerprint(first.state.calendar)===confirmedCalendar&&
    first.state.requests.find(row=>row.id===pending.id)?.booking?.id===booking.id);

  stage='replacement';
  const replacement=Buffer.from('Pet preparation — fictional Juniper Cleaning guide\nBefore the clean, all pets must stay with a trusted neighbour outside the home. Keep every pet outside the home until the cleaning is complete.\n','utf8');
  const replaced=await command(first,'documents/preparation/replace',{kind:'text',data:replacement.toString('base64')});
  const privateDocument=first.state.documents.find(document=>document.slot==='preparation');
  checked('privateReplacementReady',replaced.document_notice?.ready===true&&privateDocument?.private===true&&
    privateDocument.media_type==='text/plain'&&uuid.test(privateDocument.id)&&privateDocument.id!==originalPreparation.id&&
    first.state.replacements_left===initial.replacements_left-1);
  const privateSource=await request(first,`/api/demo/documents/${privateDocument.id}/source`,{max:32_000});
  checked('actualPrivateText',privateSource.response.headers.get('content-type')?.includes('text/plain')&&
    privateSource.bytes.equals(replacement));
  stage='replacement-answer';
  await command(first,'chat',{text:petQuestion});
  const changedClaim=first.state.messages.at(-1).claims.find(claim=>claim.version_id===privateDocument.id&&
    claim.page===1&&claim.excerpt.includes('trusted neighbour outside the home'));
  const privateDetail=await json(first,`/api/demo/documents/${privateDocument.id}`);
  checked('replacementChangesGroundedAnswer',changedClaim&&privateDetail.passages.some(item=>
    item.id===changedClaim.passage_id&&item.page===changedClaim.page&&item.content.includes(changedClaim.excerpt))&&
    !first.state.messages.at(-1).claims.some(claim=>claim.version_id===originalPreparation.id)&&
    first.state.requests.find(row=>row.id===pending.id)?.booking?.id===booking.id&&
    calendarFingerprint(first.state.calendar)===confirmedCalendar);
  stage='source-isolation';
  const retired=await json(first,`/api/demo/documents/${originalPreparation.id}/source`,{status:404});
  const other=guest();
  state(other,await json(other,'/api/demo/session',{method:'POST',body:{timezone:'Africa/Cairo'}}));
  assert(other.state.workspace_id!==first.state.workspace_id&&other.cookies.get('choreograph_guest')!==first.cookies.get('choreograph_guest'));
  const denied=await json(other,`/api/demo/documents/${privateDocument.id}/source`,{status:404});
  const deniedDetail=await json(other,`/api/demo/documents/${privateDocument.id}`,{status:404});
  checked('manifestAndGuestIsolation',retired.code==='SOURCE_UNAVAILABLE'&&denied.code==='SOURCE_UNAVAILABLE'&&
    deniedDetail.code==='SOURCE_UNAVAILABLE'&&!other.state.documents.some(document=>document.id===privateDocument.id));

  stage='static-assets';
  const worker=await request(null,'/vendor/pdfjs/pdf.worker.min.mjs',{max:3_145_728});
  const sample=await request(null,'/samples/preparation-guide-v2.pdf',{max:2_097_152});
  checked('selfHostedPDFAssets',/javascript/.test(worker.response.headers.get('content-type')??'')&&worker.bytes.length>1000&&
    /pdfjs|PDF\.js/.test(worker.bytes.subarray(0,131_072).toString())&&
    sample.response.headers.get('content-type')?.includes('application/pdf')&&sample.bytes.subarray(0,5).toString()==='%PDF-');
  stage='bridge-allowlist';
  const arbitrary=await json(first,'/api/demo/not-an-approved-command',{status:404});
  const internal=await json(first,'/api/demo/internal/maintenance',{method:'POST',body:{},status:404});
  checked('privateBridgeRoutesRejected',arbitrary.code==='ROUTE_UNAVAILABLE'&&internal.code==='ROUTE_UNAVAILABLE');

  console.log(JSON.stringify({ok:true,checks,requests,assertions,documents:initial.documents.length,sourcePages}));
}catch{
  console.error(JSON.stringify({ok:false,code:'LINUX_HTTP_SMOKE_FAILED',stage,requests,assertions}));
  process.exitCode=1;
}
