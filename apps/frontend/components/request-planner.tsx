'use client';
import {useEffect,useState} from 'react';
import {money,duration,appointment,type SessionState} from '@/lib/api';
import {Button,Badge} from './ui';
export function RequestPlanner({state,pending,onEdit,onSubmit}:{state:SessionState;pending:boolean;onEdit:(fields:Record<string,unknown>)=>void;onSubmit:()=>void}){
  const [accepted,setAccepted]=useState(false);
  useEffect(()=>setAccepted(false),[state.revision]);
  return <aside className="request-planner"><div className="panel-heading"><h2>Cleaning request</h2><Badge tone="neutral">Draft</Badge></div>
    <label>Cleaning<select aria-label="Cleaning" value={state.draft.service??''} disabled={pending} onChange={event=>onEdit({service:event.target.value||null})}><option value="">Choose a cleaning</option><option value="regular">Regular cleaning</option><option value="deep">Deep cleaning</option><option value="move-out">Move-out cleaning</option></select></label>
    <label>Home size<select aria-label="Home size" value={state.draft.bedrooms??''} disabled={pending} onChange={event=>onEdit({bedrooms:event.target.value?Number(event.target.value):null})}><option value="">Choose bedrooms</option>{[1,2,3].map(n=><option key={n} value={n}>{n} bedroom{n>1?'s':''}</option>)}</select></label>
    <label className="checkbox-label"><input type="checkbox" checked={state.draft.oven} disabled={pending} onChange={event=>onEdit({oven:event.target.checked})}/>Add inside oven</label>
    {state.quote&&<section className="quote-summary"><h3>Quote summary</h3>{state.quote.items.map(item=><div key={item.name}><span>{item.name}</span><span>{money(item.cents)}</span></div>)}<div className="quote-total"><output aria-label="Quote total">{money(state.quote.cents)}</output><span>{duration(state.quote.minutes)}</span></div>
      <p>{state.draft.preferred_at?appointment(state.draft.preferred_at,state.timezone):'Choose a time from the calendar.'}</p><small>{state.timezone}</small>
      {state.draft.preferred_at&&<><label className="checkbox-label"><input type="checkbox" checked={accepted} disabled={pending} onChange={event=>setAccepted(event.target.checked)}/>I’ve reviewed this quote.</label><Button disabled={pending||!accepted} onClick={onSubmit}>Send request</Button><small>Time is reserved after business approval.</small></>}
    </section>}
  </aside>;
}
