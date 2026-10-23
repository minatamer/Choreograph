'use client';
import {useEffect,useId,useMemo,useRef,useState} from 'react';
import {animate} from 'motion';
import {AnimatePresence,LayoutGroup,motion} from 'motion/react';
import {money,type SessionState} from '@/lib/api';
import {addDays,localDay} from '@/lib/calendar-metrics';
import {overviewAgenda,overviewWeek,weekOf} from '@/lib/business-overview-data';
import {utcOffset,weekUtcOffset} from '@/lib/timezone';
import type {BusinessPage} from '@/lib/workspace-navigation';
import {CalendarEventDialog,type CalendarEvent} from './calendar-event-dialog';
import {OverviewAppointments,OverviewAttention,OverviewServices,OverviewStaff} from './business-overview-panels';
import {CalendarActivityChart} from './calendar-activity-chart';

function MetricValue({value,format=String}:{value:number;format?:(value:number)=>string}){
 const node=useRef<HTMLSpanElement>(null);const previous=useRef(0);
 useEffect(()=>{const from=previous.current;previous.current=value;const animation=animate(from,value,{duration:.85,ease:[.16,1,.3,1],onUpdate:current=>{if(node.current)node.current.textContent=format(Math.round(current));}});return()=>animation.stop();},[value,format]);
 return <><span className="sr-only">{format(value)}</span><span ref={node} aria-hidden="true">{format(value)}</span></>;
}
export function BusinessOverview({state,week,onWeek,onNavigate,pending,onClear}:{state:SessionState;week:string;onWeek:(week:string)=>void;onNavigate:(page:BusinessPage,week?:string)=>void;pending:boolean;onClear:(id:string)=>Promise<boolean>}){
 const data=useMemo(()=>overviewWeek(state.calendar,week,state.timezone),[state.calendar,week,state.timezone]);
 const {days}=data;
 const [now,setNow]=useState(()=>Date.now());
 useEffect(()=>{const update=()=>setNow(Date.now());const timer=window.setInterval(update,60_000);document.addEventListener('visibilitychange',update);return()=>{window.clearInterval(timer);document.removeEventListener('visibilitychange',update);};},[]);
 const agenda=useMemo(()=>overviewAgenda(state.calendar,state.timezone,now),[state.calendar,state.timezone,now]);
 const group=useId(),titleId=useId();
 const [selection,setSelection]=useState<{id:string;origin:string}|null>(null);
 const opener=useRef<HTMLElement|null>(null);
 const selectedEvent=state.calendar.find(event=>event.id===selection?.id);
 const selectedRequest=selectedEvent?state.requests.find(record=>record.id===selectedEvent.enquiry_id&&record.booking?.id===selectedEvent.id):undefined;
 function open(event:CalendarEvent,origin:string,node:HTMLElement){opener.current=node;setSelection({id:event.id,origin});}
 const total=days.reduce((sum,day)=>sum+day.hours,0);
 const metrics=[{label:'Requests',value:state.summary.requests_count,icon:'↗',note:'Customer enquiries'},{label:'To review',value:state.summary.awaiting_count,icon:'◷',note:'Waiting for your approval'},{label:'Confirmed',value:state.summary.confirmed_count,icon:'✓',note:'Reserved appointments'},{label:'Booked value',value:state.summary.booked_cents,icon:'$',note:'Booking value, before any payment',format:money}];
 const first=state.calendar_first_week_start??state.calendar_week_start??week,last=state.calendar_last_week_start??first;
 const calendar=(target=week)=>onNavigate('calendar',target);
 const todayLabel=new Intl.DateTimeFormat(undefined,{weekday:'long',month:'short',day:'numeric',timeZone:state.timezone}).format(new Date(now));
 const weekLabel='Week of '+new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',timeZone:'UTC'}).format(new Date(week+'T12:00Z'));
 return <LayoutGroup id={group}><section className="business-overview" aria-label="Juniper business overview">
  <div className="business-metric-grid" data-tour="overview">{metrics.map((metric,index)=><motion.div key={metric.label} initial={{opacity:0,y:12}} animate={{opacity:1,y:0}} transition={{duration:.4,delay:index*.065}}><button type="button" onClick={()=>onNavigate('requests')} className="business-metric"><span className="metric-label"><span className="metric-icon" aria-hidden="true">{metric.icon}</span><span>{metric.label}</span></span><strong><MetricValue value={metric.value} format={metric.format}/></strong><small>{metric.note}</small></button></motion.div>)}</div>
  <div className="overview-priority-grid">
   <OverviewAppointments title="Today’s agenda" subtitle={`${todayLabel} · ${utcOffset(state.timezone,now)}`} events={agenda.agenda} zone={state.timezone} origin="today" selected={selection?.origin} onOpen={open} onCalendar={()=>calendar(weekOf(agenda.today))}/>
   <OverviewAttention state={state} onNavigate={onNavigate}/>
  </div>
  <div className="overview-analytics-grid">
   <section className="business-activity" aria-label="Weekly calendar hours"><header><div><span className="eyebrow blue-text">A little room to plan</span><h2>Time on the calendar.</h2><p>Calendar staff hours · {weekUtcOffset(state.timezone,week)}</p></div><div className="activity-total"><strong>{Number(total.toFixed(1))}<small> hrs</small></strong><span>{weekLabel}</span><div className="week-navigation"><button type="button" aria-label="Previous overview week" disabled={week<=first} onClick={()=>onWeek(addDays(week,-7))}>←</button><button type="button" aria-label="Next overview week" disabled={week>=last} onClick={()=>onWeek(addDays(week,7))}>→</button></div></div></header>
    <CalendarActivityChart key={state.workspace_id+week} days={days} events={state.calendar} requests={state.requests} zone={state.timezone} pending={pending} onClear={onClear} onCalendar={()=>calendar()}/>
   </section><OverviewServices services={data.services} weekLabel={weekLabel}/>
  </div>
  <div className="overview-priority-grid">
   <OverviewAppointments title="Next on the calendar" subtitle="Upcoming appointments" events={agenda.upcoming} zone={state.timezone} origin="next" selected={selection?.origin} onOpen={open} onCalendar={()=>calendar(agenda.upcoming[0]?weekOf(localDay(agenda.upcoming[0].starts_at,state.timezone)):week)}/>
   <OverviewStaff staff={data.staff} weekLabel={weekLabel} onCalendar={()=>calendar()}/>
  </div>
 </section><AnimatePresence>{selectedEvent&&selection&&<CalendarEventDialog key={state.workspace_id+selection.origin} layoutId={selection.origin} returnLabel="Back to overview" event={selectedEvent} request={selectedRequest} zone={state.timezone} opener={opener.current} titleId={titleId} onClose={()=>setSelection(null)} pending={pending} onClear={onClear}/>}</AnimatePresence></LayoutGroup>;
}
