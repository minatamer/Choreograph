'use client';
import {useState} from 'react';
import {clockTime,type SessionState} from '@/lib/api';
export function addDays(day:string,offset:number){const date=new Date(day+'T12:00:00Z');date.setUTCDate(date.getUTCDate()+offset);return date.toISOString().slice(0,10);}
function localDay(instant:string,zone:string){const parts=new Intl.DateTimeFormat('en-CA',{year:'numeric',month:'2-digit',day:'2-digit',timeZone:zone}).formatToParts(new Date(instant));const get=(key:string)=>parts.find(part=>part.type===key)?.value;return `${get('year')}-${get('month')}-${get('day')}`;}
export function StaffCalendar({state}:{state:SessionState}){
  const first=state.calendar_week_start??state.scenario.week_start??'';const [selected,setSelected]=useState('');const week=selected||first;
  if(!week)return null;
  const days=Array.from({length:7},(_,index)=>addDays(week,index));
  return <section className="staff-calendar"><div className="card-heading"><div><h2>Staff calendar</h2><small>{state.timezone}</small></div><div className="week-navigation"><button aria-label="Previous staff week" disabled={week<=first} onClick={()=>setSelected(addDays(week,-7))}>←</button><button aria-label="Next staff week" disabled={week>=(state.calendar_last_week_start??first)} onClick={()=>setSelected(addDays(week,7))}>→</button></div></div><p className="week-label">Week of {new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',timeZone:'UTC'}).format(new Date(week+'T12:00:00Z'))}</p>
    <div className="staff-days">{days.map(day=>{const label=new Intl.DateTimeFormat(undefined,{weekday:'short',day:'numeric',month:'short',timeZone:'UTC'}).format(new Date(day+'T12:00:00Z'));const events=state.calendar.filter(event=>event.state!=='cancelled'&&localDay(event.starts_at,state.timezone)===day);return <article key={day}><h3>{label}</h3>{['ada','noah'].map(staff=><div key={staff} className="staff-lane"><strong>{staff==='ada'?'Ada':'Noah'}</strong>{events.filter(event=>event.staff_id===staff).length?events.filter(event=>event.staff_id===staff).map(event=><div key={event.id} className={`staff-event ${event.state}`}><span>{clockTime(event.starts_at,state.timezone)}–{clockTime(event.ends_at,state.timezone)}</span><small>{event.label}</small></div>):<small className="staff-free">{new Date(day+'T12:00:00Z').getUTCDay()===0?'Closed':'No appointments'}</small>}</div>)}</article>;})}</div>
  </section>;
}
