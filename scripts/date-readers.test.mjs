import {test} from 'node:test';
import assert from 'node:assert/strict';
import {appointmentReader,clockReader} from '../apps/frontend/lib/timezone.ts';
import {appointmentsForDay,localDayReader} from '../apps/frontend/lib/calendar-metrics.ts';
import {overviewAgenda,overviewWeek} from '../apps/frontend/lib/business-overview-data.ts';

test('operation readers preserve native locale, DST and fractional-offset labels',()=>{
 const values=['2026-10-31T22:30:00Z','2026-11-01T05:30:00Z','2026-11-01T06:30:00Z'];
 for(const zone of ['America/New_York','Africa/Cairo','Asia/Kathmandu']){
  const clock=clockReader(zone),appointment=appointmentReader(zone),day=localDayReader(zone);
  for(const value of values){
   assert.equal(clock(value),new Intl.DateTimeFormat(undefined,{timeZone:zone,hour:'2-digit',minute:'2-digit'}).format(new Date(value)));
   assert.equal(appointment(value),new Intl.DateTimeFormat(undefined,{timeZone:zone,weekday:'short',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}).format(new Date(value)));
  }
  assert.equal(day('2026-10-31T22:30:00Z'),zone==='America/New_York'?'2026-10-31':'2026-11-01');
 }
});

test('formatter construction stays bounded as appointment and label counts grow',()=>{
 const native=Intl.DateTimeFormat;let count=0;
 Intl.DateTimeFormat=new Proxy(native,{construct(target,args){count++;return Reflect.construct(target,args);}});
 try{
  for(const length of [4,40,100]){
   const rows=Array.from({length},(_,index)=>({id:String(index),staff_id:index%2?'ada':'noah',enquiry_id:null,
    starts_at:'2026-10-24T07:00:00Z',ends_at:'2026-10-24T09:00:00Z',state:'confirmed',label:'Home clean'}));
   count=0;assert.equal(appointmentsForDay(rows,'2026-10-24','Africa/Cairo').length,length);assert.equal(count,1);
   count=0;assert.equal(overviewAgenda(rows,'Africa/Cairo',Date.parse('2026-10-24T08:00Z')).agenda.length,length);assert.equal(count,1);
   count=0;assert.equal(overviewWeek(rows,'2026-10-19','Africa/Cairo').days.length,7);assert.ok(count<=4);
   count=0;const clock=clockReader('Asia/Kathmandu'),appointment=appointmentReader('Asia/Kathmandu');
   rows.forEach(row=>{assert.ok(clock(row.starts_at));assert.ok(appointment(row.ends_at));});assert.equal(count,2);
  }
 }finally{Intl.DateTimeFormat=native;}
});
