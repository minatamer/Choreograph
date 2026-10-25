'use client';
import {useEffect,useRef,useState} from 'react';
import {appointment,duration,money,type Mutation,type RequestRecord,type SessionState} from '@/lib/api';
import {utcOffset} from '@/lib/timezone';
import {ExpandingDialog} from './expanding-dialog';
import {Button} from './ui';

export function BookingActionDialog({record,zone,action,pending,opener,fallbackFocus,onClose,onConfirm}:{record:RequestRecord;zone:string;action:'cancel'|'complete';pending:boolean;opener:HTMLElement|null;fallbackFocus:HTMLElement|null;onClose:()=>void;onConfirm:()=>Promise<Mutation|SessionState|null>}){
 const [submitting,setSubmitting]=useState(false),[failed,setFailed]=useState(false);
 const lock=useRef(false),sequence=useRef(0);
 useEffect(()=>()=>{sequence.current++;},[]);
 const completing=action==='complete',declining=record.status==='awaiting_review';
 const title=completing?'Mark this clean completed?':declining?'Decline this request?':'Cancel this booking?';
 const confirmLabel=completing?'Mark completed':declining?'Decline request':'Confirm cancellation';
 const busy=pending||submitting;
 function close(){if(!lock.current&&!pending)onClose();}
 async function confirm(){
  if(busy||failed||lock.current)return;
  const id=++sequence.current;lock.current=true;setSubmitting(true);let succeeded=false;
  try{
   const result=await onConfirm();if(id!==sequence.current)return;
   if(result){onClose();succeeded=true;}else setFailed(true);
  }catch{if(id===sequence.current)setFailed(true);}
  finally{if(id===sequence.current&&!succeeded){lock.current=false;setSubmitting(false);}}
 }
 return <ExpandingDialog layoutId={`booking-action-${record.id}`} className="booking-management-dialog booking-action-dialog" label={title} opener={opener} fallbackFocus={fallbackFocus} onClose={close}>
  <header><div><span className="eyebrow blue-text">{completing?'Update booking':'Review cancellation'}</span><h2>{title}</h2></div><Button kind="quiet" disabled={busy} onClick={close}>Close</Button></header>
  <div className="management-current"><strong>{record.quote.items.map(item=>item.name).join(' + ')}</strong><span>{appointment(record.preferred_at,zone)}</span><small>Timezone: {utcOffset(zone,record.preferred_at)} · {duration(record.quote.minutes)} · {money(record.quote.cents)}</small></div>
  <p>{completing?'This clean will be marked completed.':declining?'This request hasn’t reserved a time. Confirm below to decline it.':'Cancelling releases this appointment. It stays booked until you confirm below.'}</p>
  {failed&&<p className="booking-action-error" role="alert">We couldn’t confirm this change. Close this dialog and refresh to check the latest status.</p>}
  <footer><Button kind="secondary" disabled={busy} onClick={close}>{declining?'Keep request':'Keep booking'}</Button><Button busy={submitting} disabled={busy||failed} onClick={()=>void confirm()}>{confirmLabel}</Button></footer>
 </ExpandingDialog>;
}
