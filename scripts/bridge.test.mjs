import {test} from 'node:test';
import assert from 'node:assert/strict';
import {approvedRoute,boundedBody} from '../apps/frontend/lib/bridge.ts';
test('bridge permits the guest vocabulary and rejects arbitrary/internal destinations',()=>{
  assert.equal(approvedRoute('POST',['session']),true);
  assert.equal(approvedRoute('POST',['bookings']),true);
  assert.equal(approvedRoute('GET',['bookings']),false);
  assert.equal(approvedRoute('POST',['bookings','extra']),false);
  assert.equal(approvedRoute('GET',['documents','12345678-1234-1234-1234-123456789abc','source']),true);
  for(const segments of [['internal','tick'],['https:','example.com'],['..','health'],['documents','../x','source'],['crm','admin'],['session','extra']])
    assert.equal(approvedRoute('GET',segments),false);
  assert.equal(approvedRoute('DELETE',['session']),false);
  const id='12345678-1234-1234-1234-123456789abc';
  assert.equal(approvedRoute('POST',['calendar',id,'clear']),true);
  for(const action of ['cancel','delete','approve','clear/extra'])assert.equal(approvedRoute('POST',['calendar',id,action]),false);
  assert.equal(approvedRoute('GET',['calendar',id,'clear']),false);
});
test('body admission cancels oversized and stalled streams',async()=>{
  let cancelled=false;
  const large=new ReadableStream({start(c){c.enqueue(new Uint8Array(20));},cancel(){cancelled=true;}});
  await assert.rejects(boundedBody(large,10),/BODY_TOO_LARGE/);assert.equal(cancelled,true);
  let retired=false;
  const slow=new ReadableStream({cancel(){retired=true;}});
  await assert.rejects(boundedBody(slow,10,10),/BODY_TIMEOUT/);assert.equal(retired,true);
});
