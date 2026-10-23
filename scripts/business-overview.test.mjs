import {test} from 'node:test';
import assert from 'node:assert/strict';
import {overviewAgenda,overviewDay,overviewWeek,weekOf} from '../apps/frontend/lib/business-overview-data.ts';
const event=(id,starts_at,ends_at,fields={})=>({id,enquiry_id:null,staff_id:'ada',starts_at,ends_at,state:'confirmed',label:'Home clean',...fields});

test('agenda follows the saved local day, includes overnight work and excludes released time',()=>{
 const overnight=event('overnight','2026-10-22T20:00Z','2026-10-22T23:30Z');
 const midnightEnd=event('ended','2026-10-22T19:00Z','2026-10-22T21:00Z');
 const complete=event('complete','2026-10-23T06:00Z','2026-10-23T08:00Z',{state:'completed'});
 const cancelled=event('cancel','2026-10-23T08:00Z','2026-10-23T09:00Z',{state:'cancelled'});
 const result=overviewAgenda([cancelled,complete,midnightEnd,overnight],'Africa/Cairo',Date.parse('2026-10-22T22:00Z'));
 assert.equal(result.today,'2026-10-23');assert.deepEqual(result.agenda.map(row=>row.id),['overnight','complete']);
 assert.deepEqual(result.upcoming.map(row=>row.id),['overnight']);
});
test('upcoming uses actual state, includes legacy samples and never silently completes elapsed bookings',()=>{
 const rows=[event('past','2026-10-23T07:00Z','2026-10-23T08:00Z'),event('ongoing','2026-10-23T09:00Z','2026-10-23T11:00Z'),event('legacy','2026-10-24T09:00Z','2026-10-24T11:00Z',{state:'blocked',label:'Existing appointment'}),event('break','2026-10-24T12:00Z','2026-10-24T13:00Z',{state:'blocked',label:'Staff break'}),event('complete','2026-10-25T09:00Z','2026-10-25T11:00Z',{state:'completed'})];
 assert.deepEqual(overviewAgenda(rows,'UTC',Date.parse('2026-10-23T10:00Z')).upcoming.map(row=>row.id),['ongoing','legacy']);
 assert.equal(rows[0].state,'confirmed');
});
test('service counts use local starts once, normalize legacy jobs and exclude genuine blocks/cancellations',()=>{
 const result=overviewWeek([
  event('local-monday','2026-10-18T22:00Z','2026-10-19T00:00Z'),
  event('completed','2026-10-20T07:00Z','2026-10-20T09:00Z',{state:'completed'}),
  event('seed','2026-10-21T07:00Z','2026-10-21T09:00Z',{state:'blocked',label:'Existing appointment'}),
  event('block','2026-10-22T07:00Z','2026-10-22T08:00Z',{state:'blocked',label:'Staff break'}),
  event('cancel','2026-10-23T07:00Z','2026-10-23T10:00Z',{state:'cancelled'}),
  event('next-week','2026-10-25T22:00Z','2026-10-26T00:00Z'),
 ],'2026-10-19','Africa/Cairo');
 assert.deepEqual(result.services,[{name:'Home clean',count:2},{name:'Cleaning appointment',count:1}]);
 assert.equal(result.staff[0].hours,7);assert.equal(result.days.reduce((sum,row)=>sum+row.hours,0),7);
});
test('workload conserves staff hours across midnight and DST while services stay in their starting week',()=>{
 const rows=[event('overnight','2026-10-31T22:00Z','2026-11-01T08:00Z'),event('noah','2026-11-01T08:00Z','2026-11-01T10:00Z',{staff_id:'noah'}),event('cancel','2026-11-01T10:00Z','2026-11-01T15:00Z',{state:'cancelled'})];
 const result=overviewWeek(rows,'2026-10-26','America/New_York');
 assert.deepEqual(result.staff,[{id:'ada',hours:10},{id:'noah',hours:2}]);assert.equal(result.days[5].hours,6);assert.equal(result.days[6].hours,6);
 assert.deepEqual(result.services,[{name:'Home clean',count:2}]);
 const following=overviewWeek([event('cross','2026-11-02T04:00Z','2026-11-02T07:00Z')],'2026-11-02','America/New_York');
 assert.deepEqual(following.services,[]);assert.equal(following.staff[0].hours,2);
});
test('empty and invalid records are safe, and Monday week navigation spans months and years',()=>{
 const invalid=[event('invalid','bad','bad'),event('backwards','2026-10-23T12:00Z','2026-10-23T10:00Z')];
 assert.deepEqual(overviewAgenda(invalid,'UTC',Date.parse('2026-10-23T10:00Z')).agenda,[]);
 const result=overviewWeek(invalid,'2026-10-19','UTC');assert.deepEqual(result.staff,[]);assert.deepEqual(result.services,[]);assert.equal(result.days.length,7);
 assert.equal(weekOf('2027-01-01'),'2026-12-28');assert.equal(weekOf('2026-10-19'),'2026-10-19');assert.equal(weekOf('2026-10-25'),'2026-10-19');
});

test('chart day details clip overnight intervals and preserve counts, cancellation and legacy presentation',()=>{
 const rows=[event('overnight','2026-10-18T20:00Z','2026-10-18T23:00Z'),event('midnight-end','2026-10-18T18:00Z','2026-10-18T21:00Z'),event('seed','2026-10-19T06:00Z','2026-10-19T08:00Z',{state:'blocked',label:'Existing appointment'}),event('break','2026-10-19T08:00Z','2026-10-19T09:00Z',{state:'blocked',label:'Staff break'}),event('complete','2026-10-19T10:00Z','2026-10-19T11:00Z',{state:'completed'}),event('cancel','2026-10-19T12:00Z','2026-10-19T15:00Z',{state:'cancelled'})];
 const day=overviewDay(rows,'2026-10-19','Africa/Cairo');
 assert.deepEqual(day.entries.map(row=>row.event.id),['overnight','seed','break','complete','cancel']);
 assert.equal(day.appointments,3);assert.equal(day.blocked,1);assert.equal(day.cancelled,1);
 assert.equal(day.entries[0].start,Date.parse('2026-10-18T21:00Z'));assert.equal(day.entries[0].continuesBefore,true);
 const occupied=day.entries.filter(row=>row.event.state!=='cancelled').reduce((sum,row)=>sum+(row.end-row.start)/3600000,0);
 assert.equal(occupied,6);assert.equal(overviewWeek(rows,'2026-10-19','Africa/Cairo').days[0].hours,occupied);
});

test('chart day details conserve real DST hours and indicate continuation past local midnight',()=>{
 const rows=[event('whole-day','2026-11-01T03:00Z','2026-11-02T06:00Z')];
 const day=overviewDay(rows,'2026-11-01','America/New_York');
 assert.equal((day.end-day.start)/3600000,25);assert.equal(day.entries[0].continuesBefore,true);assert.equal(day.entries[0].continuesAfter,true);
 assert.equal((day.entries[0].end-day.entries[0].start)/3600000,25);
 assert.equal(overviewWeek(rows,'2026-10-26','America/New_York').days[6].hours,25);
 const empty=overviewDay([event('bad','invalid','invalid')],'2026-10-19','UTC');
 assert.deepEqual(empty.entries,[]);assert.equal(empty.appointments+empty.blocked+empty.cancelled,0);
});
