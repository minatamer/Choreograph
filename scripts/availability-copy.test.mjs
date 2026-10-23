import {test} from 'node:test';
import assert from 'node:assert/strict';
import {availabilityLabel,unavailableReason} from '../apps/frontend/lib/availability-copy.ts';
const day=(status,date='2026-10-24')=>({status,date,weekday:'Sat',slots:[],occupied:[]});

test('elapsed dates and a day too late to fit a service have distinct explanations',()=>{
 assert.equal(availabilityLabel(day('past','2026-10-22'),'2026-10-23'),'Past date');
 assert.equal(availabilityLabel(day('past','2026-10-23'),'2026-10-23'),'Too late today');
 assert.match(unavailableReason(day('past','2026-10-22'),'2026-10-23','4h'),/has passed/);
 assert.match(unavailableReason(day('past','2026-10-23'),'2026-10-23','4h'),/enough time left today/);
});
test('unavailable service-length slots do not claim both staff are fully booked',()=>{
 assert.equal(availabilityLabel(day('busy'),'2026-10-23'),'No times');
 assert.equal(unavailableReason(day('busy'),'2026-10-23','4h 30m'),'No 4h 30m appointment fits on this day. Try another date.');
});
test('closed and not-yet-open dates retain their actual reasons',()=>{
 assert.equal(availabilityLabel(day('closed'),'2026-10-23'),'Closed');
 assert.equal(availabilityLabel(day('outside'),'2026-10-23'),'Not open yet');
 assert.match(unavailableReason(day('outside'),'2026-10-23','4h'),/30 days ahead/);
});
