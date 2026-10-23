import {test} from 'node:test';
import assert from 'node:assert/strict';
import {utcOffset,weekUtcOffset} from '../apps/frontend/lib/timezone.ts';

test('offsets use UTC labels including zero, negative and partial hours',()=>{
 const at='2026-01-15T12:00:00Z';
 for(const [zone,label] of [['UTC','UTC'],['Etc/GMT+5','UTC-05:00'],['Asia/Kolkata','UTC+05:30'],['Asia/Kathmandu','UTC+05:45']])assert.equal(utcOffset(zone,at),label);
});
test('appointment labels reflect the saved zone at the appointment date',()=>{
 assert.equal(utcOffset('Africa/Cairo','2026-10-24T12:00:00Z'),'UTC+03:00');
 assert.equal(utcOffset('Africa/Cairo','2026-11-04T12:00:00Z'),'UTC+02:00');
 assert.equal(utcOffset('America/New_York','2026-07-15T12:00:00Z'),'UTC-04:00');
 assert.equal(utcOffset('America/New_York','2026-01-15T12:00:00Z'),'UTC-05:00');
});
test('week labels include both offsets across daylight-saving changes',()=>{
 assert.equal(weekUtcOffset('Africa/Cairo','2026-10-26'),'UTC+03:00 / UTC+02:00');
 assert.equal(weekUtcOffset('Asia/Kathmandu','2026-10-26'),'UTC+05:45');
});
