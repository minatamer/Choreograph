'use client';
import {weekUtcOffset} from '@/lib/timezone';
import {useEffect,useId,useRef,useState} from 'react';
import {AnimatePresence,LayoutGroup,motion} from 'motion/react';
import {appointment,clockTime,type SessionState} from '@/lib/api';
import {addDays,appointmentsForDay} from '@/lib/calendar-metrics';
import {appointmentPresentation,appointmentVisible,type CalendarStatus} from '@/lib/appointment-status';
import {CalendarEventDialog,calendarSpring,cleanerName} from './calendar-event-dialog';
import {CalendarFilters} from './calendar-filters';

export function StaffCalendar({state,week,onWeek,pending,onClear,visible,onVisibilityChange}:{state:SessionState;week:string;onWeek:(week:string)=>void;pending:boolean;onClear:(id:string)=>Promise<boolean>;visible:ReadonlySet<CalendarStatus>;onVisibilityChange:(value:Set<CalendarStatus>)=>void}){
  const group=useId(),titleId=useId();
  const [selectedId,setSelectedId]=useState<string|null>(null),[notice,setNotice]=useState('');
  const opener=useRef<HTMLElement|null>(null);
  useEffect(()=>{setSelectedId(null);setNotice('');},[week,state.workspace_id]);
  const selected=state.calendar.find(event=>event.id===selectedId&&appointmentVisible(event,visible));
  const request=selected?state.requests.find(record=>record.id===selected.enquiry_id&&record.booking?.id===selected.id):undefined;
  const first=state.calendar_first_week_start??state.calendar_week_start??state.scenario.week_start??'';
  async function clear(id:string){const accepted=await onClear(id);if(accepted){setSelectedId(null);setNotice('Removed from calendar.');}return accepted;}
  if(!week)return null;
  const days=Array.from({length:7},(_,index)=>addDays(week,index));
  return <LayoutGroup id={group}><section className="staff-calendar" data-tour="calendar">
    <div className="card-heading"><div><span className="eyebrow blue-text">The whole picture</span><h2>Staff calendar</h2><small>Timezone: {weekUtcOffset(state.timezone,week)}</small></div><div className="week-navigation"><button aria-label="Previous staff week" disabled={week<=first} onClick={()=>onWeek(addDays(week,-7))}>←</button><button aria-label="Next staff week" disabled={week>=(state.calendar_last_week_start??first)} onClick={()=>onWeek(addDays(week,7))}>→</button></div></div>
    <div className="staff-calendar-key"><p className="week-label">Week of {new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',timeZone:'UTC'}).format(new Date(week+'T12:00:00Z'))}</p><CalendarFilters visible={visible} onChange={onVisibilityChange}/></div>
    <div className="staff-week-scroll" role="region" aria-label="Staff week" tabIndex={0}><div className="staff-days">{days.map(day=>{
      const label=new Intl.DateTimeFormat(undefined,{weekday:'short',day:'numeric',month:'short',timeZone:'UTC'}).format(new Date(day+'T12:00:00Z'));
      const events=appointmentsForDay(state.calendar,day,state.timezone);
      return <article key={day}><h3>{label}</h3>{['ada','noah'].map(staff=>{
        const all=events.filter(event=>event.staff_id===staff),shown=all.filter(event=>appointmentVisible(event,visible));
        return <div key={staff} className="staff-lane"><strong>{cleanerName(staff)}</strong>{shown.length?shown.map(event=>{
          const display=appointmentPresentation(event);
          return <motion.button type="button" key={event.id} layoutId={event.id} className={`staff-event ${display.status}`} style={{borderRadius:10}} initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={calendarSpring} whileHover={{y:-2}} whileTap={{scale:.98}} aria-haspopup="dialog" aria-expanded={selected?.id===event.id} aria-label={`View ${display.title}, ${display.label}, ${cleanerName(staff)}, ${appointment(event.starts_at,state.timezone)}–${clockTime(event.ends_at,state.timezone)}`} onClick={click=>{opener.current=click.currentTarget;setSelectedId(event.id);}}><span>{clockTime(event.starts_at,state.timezone)}–{clockTime(event.ends_at,state.timezone)}</span><small>{display.title}</small><span className="staff-event-status"><span aria-hidden="true">{display.symbol}</span>{display.label}</span><span className="staff-event-open" aria-hidden="true">↗</span></motion.button>;
        }):<small className="staff-free">{all.length?'Hidden by filters':new Date(day+'T12:00:00Z').getUTCDay()===0?'Closed':'No appointments'}</small>}</div>;
      })}</article>;
    })}</div></div><p className="calendar-notice" role="status">{notice||(!visible.size?'Choose a status above to show appointments.':'')}</p>
  </section><AnimatePresence>{selected&&<CalendarEventDialog key={state.workspace_id+selected.id} event={selected} request={request} zone={state.timezone} opener={opener.current} titleId={titleId} onClose={()=>setSelectedId(null)} pending={pending} onClear={clear}/>}</AnimatePresence></LayoutGroup>;
}
