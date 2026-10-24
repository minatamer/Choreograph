import type {SessionState} from './api';
import {addDays,calendarDayBounds,calendarWeek,localDayReader} from './calendar-metrics.ts';
import {appointmentPresentation} from './appointment-status.ts';

type Event=SessionState['calendar'][number];
const validInterval=(event:Event)=>Number.isFinite(Date.parse(event.starts_at))&&Number.isFinite(Date.parse(event.ends_at))&&Date.parse(event.ends_at)>Date.parse(event.starts_at);
const chronological=(a:Event,b:Event)=>Date.parse(a.starts_at)-Date.parse(b.starts_at)||a.id.localeCompare(b.id);

export function weekOf(day:string){
 const weekday=new Date(day+'T12:00Z').getUTCDay();
 return addDays(day,-((weekday+6)%7));
}

/** Display-only clock; elapsed time never changes a stored booking status. */
export function overviewAgenda(events:Event[],zone:string,now:number){
 const readDay=localDayReader(zone),today=readDay(now),valid=events.filter(validInterval);
 return {
  today,
  agenda:valid.filter(event=>event.state!=='cancelled'&&readDay(event.starts_at)<=today&&readDay(Date.parse(event.ends_at)-1)>=today).sort(chronological),
  upcoming:valid.filter(event=>appointmentPresentation(event).status==='confirmed'&&Date.parse(event.ends_at)>now).sort(chronological),
 };
}

/** Service counts use start dates; staff hours split actual intervals at local midnight. */
export function overviewWeek(events:Event[],week:string,zone:string){
 const readDay=localDayReader(zone),valid=events.filter(validInterval),end=addDays(week,7),services=new Map<string,number>();
 for(const event of valid){
  const display=appointmentPresentation(event),day=readDay(event.starts_at);
  if(display.status==='blocked'||display.status==='cancelled'||day<week||day>=end)continue;
  services.set(display.title,(services.get(display.title)??0)+1);
 }
 const staff=[...new Set(valid.map(event=>event.staff_id))].sort().map(id=>({id,hours:calendarWeek(valid.filter(event=>event.staff_id===id),week,zone).reduce((sum,day)=>sum+day.hours,0)}));
 return {
  services:[...services].map(([name,count])=>({name,count})).sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name)),
  staff,
  days:calendarWeek(valid,week,zone),
 };
}

/** Drill into the exact local-day interval represented by a chart point. */
export function overviewDay(events:Event[],day:string,zone:string){
 const bounds=calendarDayBounds(day,zone);
 const entries=events.filter(validInterval).flatMap(event=>{
  const start=Math.max(Date.parse(event.starts_at),bounds.start),end=Math.min(Date.parse(event.ends_at),bounds.end);
  return end>start?[{event,start,end,continuesBefore:Date.parse(event.starts_at)<bounds.start,continuesAfter:Date.parse(event.ends_at)>bounds.end}]:[];
 }).sort((a,b)=>a.start-b.start||chronological(a.event,b.event));
 const count=(status:string)=>entries.filter(row=>appointmentPresentation(row.event).status===status).length;
 return {...bounds,entries,appointments:count('confirmed')+count('completed'),blocked:count('blocked'),cancelled:count('cancelled')};
}
