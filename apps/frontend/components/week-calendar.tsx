'use client';
import {useEffect,useState} from 'react';
import {api,clockTime,duration,type SessionState,type Week,type RequestRecord} from '@/lib/api';
import {Badge,Button} from './ui';

export function WeekCalendar({state,pending,onSelect,request,selectedTime,initialDate}:{state:SessionState;pending:boolean;onSelect:(start:string)=>void;request?:RequestRecord;selectedTime?:string|null;initialDate?:string}){
  const [week,setWeek]=useState(()=>{if(!initialDate)return '';const day=new Date(initialDate+'T12:00:00Z');day.setUTCDate(day.getUTCDate()-(day.getUTCDay()+6)%7);const value=day.toISOString().slice(0,10);return value>=(state.calendar_week_start??value)&&value<=(state.calendar_last_week_start??value)?value:'';});const [data,setData]=useState<Week|null>(null);const [selected,setSelected]=useState(initialDate??'');const [error,setError]=useState('');
  const quote=request?.quote??state.quote;
  const minutes=quote?.minutes;
  const preferred=selectedTime??request?.preferred_at??state.draft.preferred_at;
  useEffect(()=>{
    if(!minutes){setData(null);return;}
    const controller=new AbortController();setError('');setData(null);
    const endpoint=request?`requests/${request.id}/availability`:'availability';
    void api<Week>(endpoint+(week?'?week='+week:''),{signal:controller.signal}).then(value=>{
      if(controller.signal.aborted)return;setData(value);
      setSelected(previous=>value.days.some(day=>day.date===previous)?previous:value.days.find(day=>day.slots.length)?.date??value.days[0].date);
    }).catch(()=>{if(!controller.signal.aborted)setError('Couldn’t load this week. Please try again.');});
    return()=>controller.abort();
  },[state.workspace_id,state.generation,state.revision,minutes,request?.id,request?.revision,week]);
  if(!quote)return <div className="calendar-empty"><h3>Find a time</h3><p>Choose your cleaning and home size to see the week.</p></div>;
  function move(offset:number){if(!data)return;const day=new Date(data.week_start+'T12:00:00Z');day.setUTCDate(day.getUTCDate()+offset);setWeek(day.toISOString().slice(0,10));}
  const active=data?.days.find(day=>day.date===selected);
  const labels={past:'No times left',outside:'Outside the window',closed:'Closed',available:'Available',busy:'Fully booked'};
  return <section className="calendar-card" aria-label="Available appointments"><div className="card-heading"><div><h3>Choose a time</h3><small>{state.timezone} · {duration(quote.minutes)}</small></div><div className="week-navigation"><button aria-label="Previous week" disabled={!data?.can_previous||pending} onClick={()=>move(-7)}>←</button><button aria-label="Next week" disabled={!data?.can_next||pending} onClick={()=>move(7)}>→</button></div></div>
    {error?<p role="alert">{error}</p>:!data?<p role="status">Checking the calendar…</p>:<>
      <p className="week-label">Week of {new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',timeZone:'UTC'}).format(new Date(data.week_start+'T12:00:00Z'))}</p>
      <div className="calendar-days">{data.days.map(day=><button key={day.date} data-date={day.date} aria-label={`${day.weekday} ${day.date}: ${labels[day.status]}`} className={`calendar-day ${day.status} ${selected===day.date?'chosen':''}`} aria-pressed={selected===day.date} onClick={()=>setSelected(day.date)}><span>{day.weekday}</span><strong>{Number(day.date.slice(-2))}</strong><small>{labels[day.status]}</small>{day.occupied.length>0&&<span className="occupancy-mark" aria-label="Existing appointments"/>}</button>)}</div>
      {active&&<div className="day-options"><div><strong>{active.weekday} {Number(active.date.slice(-2))}</strong><Badge tone={active.status==='busy'?'red':active.status==='available'?'green':'neutral'}>{labels[active.status]}</Badge></div>
        {active.slots.length?<div className="time-options">{active.slots.map(slot=><button key={slot.start} disabled={pending} className={preferred===slot.start?'selected-time':''} onClick={()=>onSelect(slot.start)}>{clockTime(slot.start,state.timezone)}<span>–{clockTime(slot.end,state.timezone)}</span></button>)}</div>:<p>{active.status==='busy'?'Both cleaners are booked. Choose another day.':active.status==='closed'?'Juniper is open Monday to Saturday.':'Choose another day or check the next week.'}</p>}
      </div>}
    </>}
  </section>;
}
