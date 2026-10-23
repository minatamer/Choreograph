'use client';
import {useRef,useState} from 'react';
import {appointment,clockTime,duration,money,type RequestRecord} from '@/lib/api';
import {appointmentPresentation} from '@/lib/appointment-status';
import type {overviewDay} from '@/lib/business-overview-data';
import {utcOffset} from '@/lib/timezone';
import {ExpandingDialog} from './expanding-dialog';
import {cleanerName} from './calendar-event-dialog';
import {Badge,Button} from './ui';

type DayData=ReturnType<typeof overviewDay>;
function DayAppointment({row,request,zone,pending,onClear,onCleared}:{row:DayData['entries'][number];request?:RequestRecord;zone:string;pending:boolean;onClear:(id:string)=>Promise<boolean>;onCleared:()=>void}){
 const [clearing,setClearing]=useState(false),[failed,setFailed]=useState(false);
 const {event}=row,display=appointmentPresentation(event),offset=utcOffset(zone,event.starts_at),endOffset=utcOffset(zone,Date.parse(event.ends_at)-1);
 async function clear(){if(clearing||pending)return;setClearing(true);setFailed(false);try{if(await onClear(event.id))onCleared();else setFailed(true);}catch{setFailed(true);}finally{setClearing(false);}}
 return <details className={`activity-day-slot ${display.status}`}><summary><span className="activity-slot-copy"><strong>{display.title}</strong><span>{clockTime(new Date(row.start).toISOString(),zone)}–{clockTime(new Date(row.end).toISOString(),zone)} · {cleanerName(event.staff_id)}</span></span><Badge tone={display.tone}>{display.label}</Badge><span className="activity-slot-chevron" aria-hidden="true">⌄</span></summary>
  <div className="activity-slot-details"><p>{appointment(event.starts_at,zone)} – {appointment(event.ends_at,zone)}</p><small>{offset===endOffset?offset:offset+' / '+endOffset}</small>
   {(row.continuesBefore||row.continuesAfter)&&<p>{row.continuesBefore?'Continues from the previous day. ':''}{row.continuesAfter?'Continues into the next day.':''}</p>}
   <dl><div><dt>Cleaner</dt><dd>{cleanerName(event.staff_id)}</dd></div><div><dt>Full duration</dt><dd>{duration(Math.round((Date.parse(event.ends_at)-Date.parse(event.starts_at))/60_000))}</dd></div></dl>
   {request&&<div className="activity-slot-quote"><ul>{request.quote.items.map((item,index)=><li key={index}><span>{item.name}</span><strong>{money(item.cents)}</strong></li>)}</ul><div><span>Quoted total</span><strong>{money(request.quote.cents)}</strong></div></div>}
   {display.status==='cancelled'&&<><p>This time is released. Removing the card keeps the booking history.</p><Button kind="secondary" busy={clearing} disabled={pending} onClick={()=>void clear()}>Remove from calendar</Button></>}
   {display.status==='blocked'&&<p>This time is unavailable for bookings.</p>}
   {failed&&<p role="alert">Couldn’t remove it. Please try again.</p>}
  </div>
 </details>;
}

export function ActivityDayDialog({day,data,requests,zone,layoutId,titleId,opener,onClose,onCalendar,pending,onClear}:{day:{day:string;hours:number};data:DayData;requests:RequestRecord[];zone:string;layoutId:string;titleId:string;opener:HTMLElement|null;onClose:()=>void;onCalendar:()=>void;pending:boolean;onClear:(id:string)=>Promise<boolean>}){
 const close=useRef<HTMLButtonElement>(null),firstOffset=utcOffset(zone,data.start),lastOffset=utcOffset(zone,data.end-1);
 const label=new Intl.DateTimeFormat(undefined,{weekday:'long',month:'long',day:'numeric',timeZone:'UTC'}).format(new Date(day.day+'T12:00Z'));
 return <ExpandingDialog className="activity-day-dialog" layoutId={layoutId} titleId={titleId} opener={opener} onClose={onClose}>
  <header><div><span className="eyebrow blue-text">On the calendar</span><h2 id={titleId}>{label}</h2><p>{Number(day.hours.toFixed(1))} staff hours · {data.appointments} {data.appointments===1?'appointment':'appointments'}{data.blocked?` · ${data.blocked} unavailable ${data.blocked===1?'block':'blocks'}`:''}{data.cancelled?` · ${data.cancelled} cancelled`:''}</p><small>{firstOffset===lastOffset?firstOffset:firstOffset+' / '+lastOffset}</small></div><button ref={close} type="button" className="button quiet" aria-label="Close day details" onClick={onClose}>×</button></header>
  {data.entries.length?<div className="activity-day-list">{data.entries.map(row=><DayAppointment key={row.event.id} row={row} request={requests.find(record=>record.id===row.event.enquiry_id&&record.booking?.id===row.event.id)} zone={zone} pending={pending} onClear={onClear} onCleared={()=>close.current?.focus({preventScroll:true})}/>)}</div>:<div className="activity-day-empty"><span aria-hidden="true">✓</span><h3>Nothing on the calendar.</h3><p>No appointments or unavailable time for this day.</p></div>}
  <footer><Button kind="secondary" onClick={onCalendar}>Open calendar</Button></footer>
 </ExpandingDialog>;
}
