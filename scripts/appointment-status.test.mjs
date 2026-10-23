import {test} from 'node:test';
import assert from 'node:assert/strict';
import {appointmentPresentation,requestTone,appointmentVisible} from '../apps/frontend/lib/appointment-status.ts';
const event=(fields={})=>({id:'appointment',enquiry_id:'request',staff_id:'ada',starts_at:'2026-10-24T09:00Z',ends_at:'2026-10-24T11:00Z',state:'confirmed',label:'Regular clean',...fields});

test('legacy sample appointments and confirmed bookings share one presentation',()=>{
 const sample=appointmentPresentation(event({enquiry_id:null,state:'blocked',label:'Existing appointment'}));
 const booked=appointmentPresentation(event({label:'Cleaning appointment'}));
 assert.deepEqual(sample,booked);
 assert.equal(sample.status,'confirmed');assert.equal(sample.tone,'blue');assert.equal(sample.label,'Scheduled');
});
test('only the known unlinked sample blocker is presented as an appointment',()=>{
 assert.equal(appointmentPresentation(event({enquiry_id:null,state:'blocked',label:'Staff break'})).status,'blocked');
 assert.equal(appointmentPresentation(event({state:'blocked',label:'Existing appointment'})).status,'blocked');
});
test('completed and cancelled history retains its real status and title',()=>{
 const completed=appointmentPresentation(event({state:'completed'})),cancelled=appointmentPresentation(event({state:'cancelled'}));
 assert.equal(completed.tone,'green');assert.equal(completed.label,'Completed');
 assert.equal(cancelled.tone,'red');assert.equal(cancelled.label,'Cancelled');
 assert.equal(cancelled.title,'Regular clean');
});
test('elapsed time cannot silently complete a visitor booking',()=>{
 const display=appointmentPresentation(event({starts_at:'2020-01-01T09:00Z',ends_at:'2020-01-01T11:00Z'}));
 assert.equal(display.status,'confirmed');assert.equal(display.label,'Scheduled');
});

test('calendar filters include legacy appointments and preserve genuine staff blocks',()=>{
 const upcoming=new Set(['confirmed']);
 assert.equal(appointmentVisible(event(),upcoming),true);
 assert.equal(appointmentVisible(event({enquiry_id:null,state:'blocked',label:'Existing appointment'}),upcoming),true);
 for(const state of ['completed','cancelled']){
  assert.equal(appointmentVisible(event({state}),upcoming),false);
  assert.equal(appointmentVisible(event({state}),new Set([state])),true);
 }
 assert.equal(appointmentVisible(event(),new Set()),false);
 assert.equal(appointmentVisible(event({state:'blocked',label:'Staff break'}),new Set()),true);
});
test('review and outcome colors agree with calendar status',()=>{
 for(const status of ['confirmed','completed','cancelled'])assert.equal(requestTone(status),appointmentPresentation(event({state:status})).tone);
 assert.equal(requestTone('awaiting_review'),'amber');
});
