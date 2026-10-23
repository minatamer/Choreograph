'use client';
import {utcOffset} from '@/lib/timezone';
import {motion} from 'motion/react';
import {useState} from 'react';
import {clockTime,duration,money,type SessionState,type RequestRecord} from '@/lib/api';
import {ExpandingDialog} from './expanding-dialog';
export {cardSpring as calendarSpring} from './expanding-dialog';
import {Badge,Button} from './ui';
import {appointmentPresentation} from '@/lib/appointment-status';

export type CalendarEvent=SessionState['calendar'][number];
export const cleanerName=(id:string)=>id==='ada'?'Ada':id==='noah'?'Noah':id;

export function CalendarEventDialog({event,request,zone,onClose,opener,titleId,pending,onClear,layoutId=event.id,returnLabel='Back to calendar'}:{event:CalendarEvent;request?:RequestRecord;zone:string;onClose:()=>void;opener:HTMLElement|null;titleId:string;pending:boolean;onClear:(id:string)=>Promise<boolean>;layoutId?:string;returnLabel?:string}){
 const [clearing,setClearing]=useState(false),[failed,setFailed]=useState(false);
 async function clear(){setClearing(true);setFailed(false);try{if(!await onClear(event.id))setFailed(true);}catch{setFailed(true);}finally{setClearing(false);}}
 const minutes=Math.round((Date.parse(event.ends_at)-Date.parse(event.starts_at))/60_000);
 const day=new Intl.DateTimeFormat(undefined,{weekday:'long',month:'long',day:'numeric',year:'numeric',timeZone:zone}).format(new Date(event.starts_at));
 const display=appointmentPresentation(event);
 return <ExpandingDialog layoutId={layoutId} className={`calendar-event-dialog ${display.status}`} titleId={titleId} opener={opener} onClose={onClose}>
   <motion.div className="calendar-detail-content" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} transition={{duration:.18,delay:.12}}>
    <header><span className="calendar-detail-icon" aria-hidden="true"><svg width="24" height="24" viewBox="0 0 24 24" fill="none"><rect x="3" y="5" width="18" height="16" rx="4" stroke="currentColor" strokeWidth="1.5"/><path d="M7 3v5m10-5v5M3 11h18m-12 5h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg></span><Button kind="quiet" className="calendar-detail-close" aria-label="Close appointment details" onClick={onClose}>×</Button></header>
    <div className="calendar-detail-title"><Badge tone={display.tone}>{display.label}</Badge><h2 id={titleId}>{display.title}</h2><p>{day}</p></div>
    <div className="calendar-detail-time"><strong>{clockTime(event.starts_at,zone)} <span>– {clockTime(event.ends_at,zone)}</span></strong><small>Timezone: {utcOffset(zone,event.starts_at)}</small></div>
    <dl className="calendar-detail-facts"><div><dt>Cleaner</dt><dd>{cleanerName(event.staff_id)}</dd></div><div><dt>Duration</dt><dd>{duration(minutes)}</dd></div></dl>
    {request&&<div className="calendar-detail-service"><h3>Cleaning details</h3><ul>{request.quote.items.map((item,index)=><li key={index}><span>{item.name}</span><strong>{money(item.cents)}</strong></li>)}</ul><div><span>Quoted total</span><strong>{money(request.quote.cents)}</strong></div></div>}
    {display.status==='cancelled'&&<p className="calendar-detail-note">This time is released. Removing the card keeps the booking history.</p>}
    {display.status==='blocked'&&<p className="calendar-detail-note">This time is unavailable for bookings.</p>}
    {failed&&<p role="alert" className="calendar-clear-error">Couldn’t remove it. Please try again.</p>}
    <footer>{display.status==='cancelled'&&<Button kind="secondary" className="calendar-clear" busy={clearing} disabled={pending} onClick={()=>void clear()}>Remove from calendar</Button>}<Button kind="secondary" onClick={onClose}>{returnLabel}</Button></footer>
   </motion.div>
 </ExpandingDialog>;
}
