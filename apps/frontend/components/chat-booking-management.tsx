'use client';
import {useEffect,useRef,useState} from 'react';
import {AnimatePresence} from 'motion/react';
import {appointment,duration,money,type Mutation,type RequestRecord,type SessionState} from '@/lib/api';
import {utcOffset} from '@/lib/timezone';
import {ExpandingDialog} from './expanding-dialog';
import {WeekCalendar} from './week-calendar';
import {Button} from './ui';

export type BookingAction=(record:RequestRecord,action:'reschedule'|'cancel',fields?:Record<string,unknown>)=>Promise<Mutation|SessionState|null>;
export function ChatBookingManagement({state,record,pending,onAction,compact=false}:{state:SessionState;record:RequestRecord;pending:boolean;onAction:BookingAction;compact?:boolean}){
 const [mode,setMode]=useState<'reschedule'|'cancel'|null>(null),[candidate,setCandidate]=useState<string|null>(null),[reviewed,setReviewed]=useState(false);
 const [submitting,setSubmitting]=useState(false),[failure,setFailure]=useState(false);const lock=useRef(false),opener=useRef<HTMLElement|null>(null);
 const active=record.status==='confirmed'||record.status==='awaiting_review',busy=pending||submitting;
 useEffect(()=>{setMode(null);setCandidate(null);setReviewed(false);setFailure(false);},[record.revision]);
 function close(){if(!lock.current)setMode(null);}
 async function submit(){
  if(!mode||busy||lock.current||(mode==='reschedule'&&(!candidate||candidate===record.preferred_at||!reviewed)))return;
  lock.current=true;setSubmitting(true);setFailure(false);
  try{const result=await onAction(record,mode,mode==='reschedule'?{preferred_at:candidate}:undefined);if(result)setMode(null);else setFailure(true);}
  finally{lock.current=false;setSubmitting(false);}
 }
 if(!active)return null;
 return <section className={`chat-booking-management${compact?' compact':''}`} aria-label="Manage your booking">
  {!compact&&<div><h3>Your clean, your plans.</h3><p>{appointment(record.preferred_at,state.timezone)} · {duration(record.quote.minutes)} · {money(record.quote.cents)}</p><small>Timezone: {utcOffset(state.timezone,record.preferred_at)}</small></div>}
  <div className="chat-management-actions">{record.status==='confirmed'&&<Button kind="secondary" disabled={busy} onClick={event=>{opener.current=event.currentTarget;setMode('reschedule');setCandidate(null);setReviewed(false);setFailure(false);}}>Choose a new time</Button>}<Button kind="quiet" disabled={busy} onClick={event=>{opener.current=event.currentTarget;setMode('cancel');setFailure(false);}}>{record.status==='confirmed'?'Cancel booking':'Cancel request'}</Button></div>
  <AnimatePresence>{mode&&<ExpandingDialog layoutId={`manage-${record.id}`} className="booking-management-dialog" label={mode==='cancel'?'Cancel your booking':'Change your appointment'} opener={opener.current} onClose={close}>
   <header><div><span className="eyebrow blue-text">{mode==='cancel'?'Review cancellation':'Find a better time'}</span><h2>{mode==='cancel'?'Cancel this clean?':'Let’s move your clean.'}</h2></div><Button kind="quiet" disabled={busy} onClick={close}>Close</Button></header>
   <div className="management-current"><strong>{record.quote.items[0].name}</strong><span>{appointment(record.preferred_at,state.timezone)}</span><small>Timezone: {utcOffset(state.timezone,record.preferred_at)} · {duration(record.quote.minutes)} · {money(record.quote.cents)}</small></div>
   {mode==='cancel'?<p>{record.status==='confirmed'?'Cancelling releases this appointment. Your booking stays in place until you confirm below.':'This request has not reserved a time. Confirm below to cancel it.'}</p>:<><p>Your current appointment stays booked until your new time is confirmed.</p><WeekCalendar state={state} request={record} selectedTime={candidate} pending={busy} onSelect={value=>{setCandidate(value);setReviewed(false);}}/>{candidate&&<div className="management-proposal"><strong>Proposed appointment</strong><span>{appointment(candidate,state.timezone)}</span><small>Timezone: {utcOffset(state.timezone,candidate)} · {duration(record.quote.minutes)}</small><label className="checkbox-label"><input type="checkbox" checked={reviewed} disabled={busy} onChange={event=>setReviewed(event.target.checked)}/>I’ve reviewed this new time.</label></div>}</>}
   {failure&&<p role="alert">We couldn’t verify this change. Close this dialog and refresh to check your booking before trying again.</p>}
   <footer><Button kind="secondary" disabled={busy} onClick={close}>Keep my booking</Button><Button busy={submitting} disabled={busy||(mode==='reschedule'&&(!candidate||candidate===record.preferred_at||!reviewed))} onClick={()=>void submit()}>{mode==='cancel'?'Confirm cancellation':'Confirm new time'}</Button></footer>
  </ExpandingDialog>}</AnimatePresence>
 </section>;
}
