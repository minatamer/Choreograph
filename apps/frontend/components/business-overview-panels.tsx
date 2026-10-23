'use client';
import {motion} from 'motion/react';
import type {ReactNode} from 'react';
import {appointment,clockTime,money,type SessionState} from '@/lib/api';
import {appointmentPresentation} from '@/lib/appointment-status';
import {utcOffset} from '@/lib/timezone';
import type {overviewWeek} from '@/lib/business-overview-data';
import type {BusinessPage} from '@/lib/workspace-navigation';
import {Badge} from './ui';
import {calendarSpring,cleanerName,type CalendarEvent} from './calendar-event-dialog';

type Navigate=(page:BusinessPage,week?:string)=>void;
type WeekData=ReturnType<typeof overviewWeek>;
function OverviewLink({children,onClick}:{children:ReactNode;onClick:()=>void}){
 return <button type="button" className="overview-link" onClick={onClick}>{children}<span aria-hidden="true">↗</span></button>;
}

export function OverviewAppointments({title,subtitle,events,zone,origin,selected,onOpen,onCalendar}:{title:string;subtitle:string;events:CalendarEvent[];zone:string;origin:string;selected:string|undefined;onOpen:(event:CalendarEvent,origin:string,opener:HTMLElement)=>void;onCalendar:()=>void}){
 return <section className="overview-panel overview-appointments" aria-label={title}>
  <header className="overview-panel-heading"><div><h2>{title}</h2><p>{subtitle}</p></div><OverviewLink onClick={onCalendar}>Calendar</OverviewLink></header>
  {events.length?<div className="overview-appointment-list">{events.slice(0,3).map(event=>{
   const display=appointmentPresentation(event),layoutId=origin+'-'+event.id;
   return <motion.button key={event.id} type="button" className={`overview-appointment ${display.status}`} layoutId={layoutId} style={{borderRadius:16}} transition={calendarSpring} aria-haspopup="dialog" aria-expanded={selected===layoutId} aria-label={`View ${display.title}, ${display.label}, ${cleanerName(event.staff_id)}, ${appointment(event.starts_at,zone)}`} onClick={click=>onOpen(event,layoutId,click.currentTarget)}>
    <span className="overview-appointment-date"><strong>{new Intl.DateTimeFormat(undefined,{day:'numeric',timeZone:zone}).format(new Date(event.starts_at))}</strong><small>{new Intl.DateTimeFormat(undefined,{month:'short',timeZone:zone}).format(new Date(event.starts_at))}</small></span>
    <span className="overview-appointment-copy"><strong>{display.title}</strong><span>{clockTime(event.starts_at,zone)}–{clockTime(event.ends_at,zone)} · {cleanerName(event.staff_id)}</span><small>{utcOffset(zone,event.starts_at)}</small></span>
    <span className="overview-appointment-state"><Badge tone={display.tone}>{display.label}</Badge><span aria-hidden="true">↗</span></span>
   </motion.button>;
  })}</div>:<div className="overview-empty"><span aria-hidden="true">✓</span><strong>{origin==='today'?'A little breathing room.':'A clear calendar ahead.'}</strong><p>{origin==='today'?'No appointments today. Take a look at the week.':'New bookings will appear here.'}</p></div>}
  {events.length>3&&<OverviewLink onClick={onCalendar}>View all {events.length} appointments</OverviewLink>}
 </section>;
}

export function OverviewAttention({state,onNavigate}:{state:SessionState;onNavigate:Navigate}){
 const waiting=state.requests.filter(record=>record.status==='awaiting_review').sort((a,b)=>a.preferred_at.localeCompare(b.preferred_at));
 const connection=state.crm_provider==='hubspot'&&state.connection?.provider==='hubspot'?state.connection:null;
 const connected=connection?.state==='ready'&&state.crm_mode==='connected';
 const connectionLabel=connected?'Connected':connection?.state==='setup'?'Finish setup':connection?.state==='needs_attention'?'Needs attention':connection?.state==='finishing'?'Finishing':connection&& !['finished','detached'].includes(connection.state)?'Check connection':'Not connected';
 return <section className="overview-panel overview-attention" aria-label="Needs your attention">
  <header className="overview-panel-heading"><div><h2>Needs your attention</h2><p>{waiting.length?`${waiting.length} ${waiting.length===1?'request is':'requests are'} ready to review.`:'You’re all caught up.'}</p></div><span className="overview-count">{waiting.length}</span></header>
  {waiting.length?<div className="overview-review-list">{waiting.slice(0,2).map(record=><button key={record.id} type="button" onClick={()=>onNavigate('requests')}><span className="overview-review-icon" aria-hidden="true">◷</span><span><strong>{record.quote.items[0]?.name??'Cleaning request'}</strong><small>{appointment(record.preferred_at,state.timezone)} · {utcOffset(state.timezone,record.preferred_at)}</small></span><span className="overview-review-price">{money(record.quote.cents)}<span aria-hidden="true"> ↗</span></span></button>)}</div>:<p className="overview-attention-note">New requests will wait here for your approval.</p>}
  <div className="overview-readiness">
   <button type="button" onClick={()=>onNavigate('guides')}><span className="overview-readiness-icon" aria-hidden="true">▤</span><span><strong>Juniper’s documents</strong><small>{state.documents.length} ready to answer</small></span><span aria-hidden="true">↗</span></button>
   <button type="button" onClick={()=>onNavigate('connections')}><span className="overview-readiness-icon" aria-hidden="true">↗</span><span><strong>HubSpot</strong><small>{connectionLabel}</small></span><span className={connected?'overview-connection-dot connected':'overview-connection-dot'} aria-hidden="true"/></button>
  </div>
 </section>;
}

export function OverviewServices({services,weekLabel}:{services:WeekData['services'];weekLabel:string}){
 const total=services.reduce((sum,row)=>sum+row.count,0),max=Math.max(1,...services.map(row=>row.count));
 const shown=services.slice(0,4),other=services.slice(4).reduce((sum,row)=>sum+row.count,0);
 const rows=other?[...shown,{name:'Other services',count:other}]:shown;
 return <section className="overview-panel overview-services" aria-label="Service mix"><header className="overview-panel-heading"><div><h2>Service mix</h2><p>{weekLabel} · appointments starting this week</p></div></header><div className="overview-service-total"><strong>{total}</strong><span>{total===1?'appointment':'appointments'}</span></div>
  {rows.length?<div className="overview-bars">{rows.map(row=><div key={row.name}><div><span>{row.name}</span><strong>{row.count}</strong></div><span className="overview-bar-track"><motion.span initial={{scaleX:0}} animate={{scaleX:Math.min(1,row.count/max)}} transition={{duration:.6,ease:[.16,1,.3,1]}}/></span></div>)}</div>:<p className="overview-attention-note">No appointments start in this week.</p>}
 </section>;
}

export function OverviewStaff({staff,weekLabel,onCalendar}:{staff:WeekData['staff'];weekLabel:string;onCalendar:()=>void}){
 const max=Math.max(1,...staff.map(row=>row.hours));
 return <section className="overview-panel overview-staff" aria-label="Staff workload"><header className="overview-panel-heading"><div><h2>On the team’s calendar</h2><p>{weekLabel} · includes unavailable time</p></div><OverviewLink onClick={onCalendar}>Calendar</OverviewLink></header>
  {staff.length?<div className="overview-staff-list">{staff.map(row=><div key={row.id}><span className="overview-staff-avatar" aria-hidden="true">{cleanerName(row.id).slice(0,1)}</span><div><div><strong>{cleanerName(row.id)}</strong><span>{Number(row.hours.toFixed(1))} h</span></div><span className="overview-bar-track"><motion.span initial={{scaleX:0}} animate={{scaleX:row.hours/max}} transition={{duration:.6,ease:[.16,1,.3,1]}}/></span></div></div>)}</div>:<p className="overview-attention-note">Staff hours appear with the first appointment.</p>}
 </section>;
}
