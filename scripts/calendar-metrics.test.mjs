import {test} from 'node:test';
import assert from 'node:assert/strict';
import {calendarWeek,appointmentsForDay} from '../apps/frontend/lib/calendar-metrics.ts';
const event=(starts_at,ends_at,state='confirmed')=>({id:'fixture',enquiry_id:null,staff_id:'ada',starts_at,ends_at,state,label:'Fictional fixture'});

test('calendar keeps cancelled history on the correct local day while hours exclude it',()=>{
 const cancelled=event('2026-10-19T22:00Z','2026-10-20T00:00Z','cancelled');
 const active=event('2026-10-19T23:00Z','2026-10-20T01:00Z');
 const rows=appointmentsForDay([cancelled,active],'2026-10-20','Africa/Cairo');
 assert.deepEqual(rows,[cancelled,active]);
 assert.deepEqual(appointmentsForDay([cancelled,active],'2026-10-19','Africa/Cairo'),[]);
 assert.equal(calendarWeek(rows,'2026-10-19','Africa/Cairo')[1].hours,2);
});
test('weekly chart uses stored intervals, includes blocks and excludes cancellations',()=>{
 const data=calendarWeek([event('2026-10-19T09:00Z','2026-10-19T11:00Z'),event('2026-10-19T12:00Z','2026-10-19T13:00Z','blocked'),event('2026-10-20T09:00Z','2026-10-20T14:00Z','cancelled')],'2026-10-19','UTC');
 assert.deepEqual(data.map(row=>row.hours),[3,0,0,0,0,0,0]);
 assert.equal(calendarWeek([],'2026-10-19','UTC').length,7);
});
test('cross-midnight intervals split across the real local days, not UTC dates',()=>{
 const rows=[event('2026-10-19T22:00Z','2026-10-20T02:00Z')];
 assert.deepEqual(calendarWeek(rows,'2026-10-19','UTC').map(row=>row.hours),[2,2,0,0,0,0,0]);
 assert.deepEqual(calendarWeek(rows,'2026-10-19','Africa/Cairo').map(row=>row.hours),[0,4,0,0,0,0,0]);
});
test('DST day length and week boundaries retain actual elapsed staff hours',()=>{
 const rows=[event('2026-11-01T04:00Z','2026-11-02T05:00Z')];
 assert.equal(calendarWeek(rows,'2026-10-26','America/New_York')[6].hours,25);
 assert.equal(calendarWeek(rows,'2026-11-02','America/New_York')[0].hours,0);
 assert.deepEqual(calendarWeek([event('invalid','invalid')],'2026-10-19','UTC').map(row=>row.hours),[0,0,0,0,0,0,0]);
});
