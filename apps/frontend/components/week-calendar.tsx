'use client';
import {useEffect,useState} from 'react';
import {api,clockReader,duration,type SessionState,type Week,type RequestRecord} from '@/lib/api';
import {Badge} from './ui';
import {weekUtcOffset} from '@/lib/timezone';
import {localDay} from '@/lib/calendar-metrics';
import {availabilityLabel,unavailableReason} from '@/lib/availability-copy';
import {periodSlots,type AppointmentPeriod} from '@/lib/availability-period';
import {calendarWindowStart,calendarSelectedDay} from '@/lib/availability-window';

export function WeekCalendar({state,pending,onSelect,request,selectedTime,initialDate,initialPeriod='all',rolling=true}:{state:SessionState;pending:boolean;onSelect:(start:string)=>void;request?:RequestRecord;selectedTime?:string|null;initialDate?:string;initialPeriod?:AppointmentPeriod;rolling?:boolean}){
  const today=localDay(Date.now(),state.timezone);
  const [week,setWeek]=useState(()=>calendarWindowStart(today,initialDate,rolling));const [data,setData]=useState<Week|null>(null);const [selected,setSelected]=useState('');const [error,setError]=useState('');
  const windowStart=calendarWindowStart(today,week,rolling);
  const quote=request?.quote??state.quote;
  const [period,setPeriod]=useState<AppointmentPeriod>(initialPeriod);
  const minutes=quote?.minutes;
  const preferred=selectedTime??request?.preferred_at??state.draft.preferred_at;
  const [loading,setLoading]=useState(true),[attempt,setAttempt]=useState(0);
  useEffect(()=>{
    if(!minutes&&!rolling){setData(null);setLoading(false);return;}
    const controller=new AbortController();setError('');setLoading(true);
    const endpoint=request?`requests/${request.id}/availability`:'availability';
    void api<Week>(endpoint+'?'+(rolling?'start':'week')+'='+windowStart,{signal:controller.signal}).then(value=>{
      if(controller.signal.aborted)return;setData(value);
      setSelected(previous=>calendarSelectedDay(value,today,previous,day=>value.preview?day.status==='available':periodSlots(day.slots,state.timezone,initialPeriod).length>0));
    }).catch(()=>{if(!controller.signal.aborted)setError('Couldn’t load this week. Please try again.');}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return()=>controller.abort();
  },[state.workspace_id,state.generation,state.revision,state.timezone,minutes,request?.id,request?.revision,windowStart,today,attempt,initialPeriod,rolling]);
  if(!quote&&!rolling)return <div className="calendar-empty"><h3>Find a time</h3><p>Choose your cleaning and home size to see the week.</p></div>;
  function move(offset:number){if(!data||loading)return;const day=new Date(data.week_start+'T12:00:00Z');day.setUTCDate(day.getUTCDate()+offset);setWeek(day.toISOString().slice(0,10));}
  const active=data?.days.find(day=>day.date===selected);
  const slots=periodSlots(active?.slots??[],state.timezone,period);
  const readClock=clockReader(state.timezone);
  const updating=loading||pending,displayWeek=data?.week_start||windowStart;
  const preview=!quote||data?.preview===true;
  const label=(day:Week['days'][number])=>preview&&day.status==='available'?'Openings':availabilityLabel(day,today);
  const readDate=new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',timeZone:'UTC'});
  const rangeStart=new Date(displayWeek+'T12:00:00Z'),rangeEnd=new Date(rangeStart);rangeEnd.setUTCDate(rangeEnd.getUTCDate()+6);
  return <section className={`calendar-card${rolling?' rolling-calendar':''}`} aria-label="Available appointments" aria-busy={loading}><div className="card-heading availability-heading"><h3>{preview?'Find an appointment':'Choose a time'}</h3><div className="week-navigation"><button aria-label={rolling?'Previous seven days':'Previous week'} disabled={!data?.can_previous||updating} onClick={()=>move(-7)}>←</button><button aria-label={rolling?'Next seven days':'Next week'} disabled={!data?.can_next||updating} onClick={()=>move(7)}>→</button></div><small>{weekUtcOffset(state.timezone,displayWeek)} · {preview?'Choose your clean and home size for exact times.':duration(quote?.minutes??0)}</small></div>
    <div className="calendar-week-heading"><p className="week-label">{rolling?`${readDate.format(rangeStart)} – ${readDate.format(rangeEnd)}`:`Week of ${readDate.format(rangeStart)}`}</p><span className="calendar-load-status" role={error?'alert':'status'}>{error?<>Couldn’t update. <button type="button" onClick={()=>setAttempt(value=>value+1)}>Retry</button></>:loading?'Updating…':''}</span></div>
    {data?<div className="calendar-days" key={data.week_start} role="group" aria-label={rolling?'Seven days of appointments':'Week of appointments'}>{data.days.map(day=><button key={day.date} data-date={day.date} disabled={loading} aria-label={`${day.weekday} ${day.date}: ${label(day)}`} className={`calendar-day ${day.status} ${selected===day.date?'chosen':''}`} aria-pressed={selected===day.date} onClick={()=>setSelected(day.date)}><span>{day.weekday}</span><strong>{Number(day.date.slice(-2))}</strong><small>{label(day)}</small></button>)}</div>:<div className="calendar-days calendar-placeholder" aria-hidden="true">{Array.from({length:7},(_,index)=><div className="calendar-day" key={index}/>)}</div>}
    {!preview&&<label className="availability-period">Appointment time<select value={period} onChange={event=>setPeriod(event.target.value as AppointmentPeriod)}><option value="all">All times</option><option value="morning">Morning</option><option value="afternoon">Afternoon</option></select></label>}
    <div className="day-options">{active?<><div><strong>{active.weekday} {Number(active.date.slice(-2))}</strong><Badge tone={active.status==='busy'?'red':active.status==='available'?'green':'neutral'}>{label(active)}</Badge></div>
      {preview?<p key={active.date}>{active.status==='available'?'This day has potential openings. Tell me your cleaning and home size to check exact times.':active.status==='closed'?'Juniper is open Monday to Saturday.':'Choose a day with openings, then tell me your cleaning and home size.'}</p>:slots.length?<div className="time-options" key={active.date} aria-label="Appointment times">{slots.map(slot=><button key={slot.start} disabled={updating||!!error} className={preferred===slot.start?'selected-time':''} onClick={()=>onSelect(slot.start)}>{readClock(slot.start)}<span>–{readClock(slot.end)}</span></button>)}</div>:<p key={active.date}>{active.slots.length?`No ${period} appointments fit this clean on this day. Choose another day or show all times.`:unavailableReason(active,today,duration(quote?.minutes??0))}</p>}
    </>:<p>{error?'Try loading the calendar again.':'Checking available appointments…'}</p>}</div>
  </section>;
}
