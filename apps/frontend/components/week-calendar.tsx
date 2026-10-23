'use client';
import {useEffect,useState} from 'react';
import {api,clockTime,duration,type SessionState,type Week,type RequestRecord} from '@/lib/api';
import {Badge} from './ui';
import {weekUtcOffset} from '@/lib/timezone';
import {localDay} from '@/lib/calendar-metrics';
import {availabilityLabel,unavailableReason} from '@/lib/availability-copy';

export function WeekCalendar({state,pending,onSelect,request,selectedTime,initialDate}:{state:SessionState;pending:boolean;onSelect:(start:string)=>void;request?:RequestRecord;selectedTime?:string|null;initialDate?:string}){
  const [week,setWeek]=useState(()=>{if(!initialDate)return '';const day=new Date(initialDate+'T12:00:00Z');day.setUTCDate(day.getUTCDate()-(day.getUTCDay()+6)%7);const value=day.toISOString().slice(0,10);return value>=(state.calendar_week_start??value)&&value<=(state.calendar_last_week_start??value)?value:'';});const [data,setData]=useState<Week|null>(null);const [selected,setSelected]=useState(initialDate??'');const [error,setError]=useState('');
  const quote=request?.quote??state.quote;
  const minutes=quote?.minutes;
  const preferred=selectedTime??request?.preferred_at??state.draft.preferred_at;
  const [loading,setLoading]=useState(true),[attempt,setAttempt]=useState(0);
  useEffect(()=>{
    if(!minutes){setData(null);setLoading(false);return;}
    const controller=new AbortController();setError('');setLoading(true);
    const endpoint=request?`requests/${request.id}/availability`:'availability';
    void api<Week>(endpoint+(week?'?week='+week:''),{signal:controller.signal}).then(value=>{
      if(controller.signal.aborted)return;setData(value);
      setSelected(previous=>value.days.some(day=>day.date===previous)?previous:value.days.find(day=>day.slots.length)?.date??value.days[0].date);
    }).catch(()=>{if(!controller.signal.aborted)setError('Couldn’t load this week. Please try again.');}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return()=>controller.abort();
  },[state.workspace_id,state.generation,state.revision,minutes,request?.id,request?.revision,week,attempt]);
  if(!quote)return <div className="calendar-empty"><h3>Find a time</h3><p>Choose your cleaning and home size to see the week.</p></div>;
  function move(offset:number){if(!data||loading)return;const day=new Date(data.week_start+'T12:00:00Z');day.setUTCDate(day.getUTCDate()+offset);setWeek(day.toISOString().slice(0,10));}
  const active=data?.days.find(day=>day.date===selected);
  const today=localDay(Date.now(),state.timezone);
  const updating=loading||pending,displayWeek=data?.week_start||week||state.calendar_week_start||state.scenario.week_start||today;
  return <section className="calendar-card" aria-label="Available appointments" aria-busy={loading}><div className="card-heading availability-heading"><h3>Choose a time</h3><div className="week-navigation"><button aria-label="Previous week" disabled={!data?.can_previous||updating} onClick={()=>move(-7)}>←</button><button aria-label="Next week" disabled={!data?.can_next||updating} onClick={()=>move(7)}>→</button></div><small>Timezone: {weekUtcOffset(state.timezone,displayWeek)} · {duration(quote.minutes)}</small></div>
    <div className="calendar-week-heading"><p className="week-label">Week of {new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',timeZone:'UTC'}).format(new Date(displayWeek+'T12:00:00Z'))}</p><span className="calendar-load-status" role={error?'alert':'status'}>{error?<>Couldn’t update. <button type="button" onClick={()=>setAttempt(value=>value+1)}>Retry</button></>:loading?'Updating…':''}</span></div>
    {data?<div className="calendar-days" key={data.week_start}>{data.days.map(day=><button key={day.date} data-date={day.date} disabled={loading} aria-label={`${day.weekday} ${day.date}: ${availabilityLabel(day,today)}`} className={`calendar-day ${day.status} ${selected===day.date?'chosen':''}`} aria-pressed={selected===day.date} onClick={()=>setSelected(day.date)}><span>{day.weekday}</span><strong>{Number(day.date.slice(-2))}</strong><small>{availabilityLabel(day,today)}</small></button>)}</div>:<div className="calendar-days calendar-placeholder" aria-hidden="true">{Array.from({length:7},(_,index)=><div className="calendar-day" key={index}/>)}</div>}
    <div className="day-options">{active?<><div><strong>{active.weekday} {Number(active.date.slice(-2))}</strong><Badge tone={active.status==='busy'?'red':active.status==='available'?'green':'neutral'}>{availabilityLabel(active,today)}</Badge></div>
      {active.slots.length?<div className="time-options" key={active.date} aria-label="Appointment times">{active.slots.map(slot=><button key={slot.start} disabled={updating||!!error} className={preferred===slot.start?'selected-time':''} onClick={()=>onSelect(slot.start)}>{clockTime(slot.start,state.timezone)}<span>–{clockTime(slot.end,state.timezone)}</span></button>)}</div>:<p key={active.date}>{unavailableReason(active,today,duration(quote.minutes))}</p>}
    </>:<p>{error?'Try loading the calendar again.':'Checking available appointments…'}</p>}</div>
  </section>;
}
