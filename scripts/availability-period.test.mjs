import {test} from 'node:test';
import assert from 'node:assert/strict';
import {periodSlots} from '../apps/frontend/lib/availability-period.ts';

test('morning and afternoon use the workspace offset rather than UTC or device time',()=>{
 const slots=[{start:'2026-10-24T05:45:00Z',id:'morning'},{start:'2026-10-24T06:15:00Z',id:'noon'}];
 assert.deepEqual(periodSlots(slots,'Asia/Kathmandu','morning').map(slot=>slot.id),['morning']);
 assert.deepEqual(periodSlots(slots,'Asia/Kathmandu','afternoon').map(slot=>slot.id),['noon']);
 assert.equal(periodSlots(slots,'Asia/Kathmandu','all'),slots);
});
test('daylight-saving transitions change filtering with the actual appointment date',()=>{
 const slots=[{start:'2026-10-30T16:30:00Z'},{start:'2026-11-02T16:30:00Z'}];
 assert.deepEqual(periodSlots(slots,'America/New_York','morning'),[slots[1]]);
 assert.deepEqual(periodSlots(slots,'America/New_York','afternoon'),[slots[0]]);
});
