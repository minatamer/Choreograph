'use client';
import {utcOffset} from '@/lib/timezone';
import {useState} from 'react';
import {appointment,duration,money,type RequestRecord,type SessionState} from '@/lib/api';
import {Badge,Button} from './ui';
export function ChatReview({state,pending,onSubmit}:{state:SessionState;pending:boolean;onSubmit:(request?:RequestRecord)=>void}){
 const [acceptedRevision,setAcceptedRevision]=useState<number|null>(null);
 const accepted=acceptedRevision===state.revision;
 if(!state.quote||!state.draft.preferred_at)return null;
 const latest=state.requests.at(-1);
 const matchesLatest=latest&&latest.preferred_at===state.draft.preferred_at&&latest.fields.service===state.draft.service&&latest.fields.bedrooms===state.draft.bedrooms&&latest.fields.oven===state.draft.oven&&latest.quote.cents===state.quote.cents&&latest.quote.minutes===state.quote.minutes;
 if(matchesLatest&&['confirmed','completed'].includes(latest.status))return null;
 const existing=matchesLatest&&latest.status==='awaiting_review'?latest:undefined;
 return <section className="chat-review" aria-label="Review your booking"><div className="card-heading"><div><span className="eyebrow blue-text">Ready when you are</span><h3>A clean that fits.</h3></div><Badge tone="blue">Review</Badge></div><div className="chat-review-facts"><div><strong>{state.quote.items.map(item=>item.name).join(' + ')}</strong><span>{appointment(state.draft.preferred_at,state.timezone)}</span><small>Timezone: {utcOffset(state.timezone,state.draft.preferred_at)} · {duration(state.quote.minutes)}</small></div><strong className="chat-review-price">{money(state.quote.cents)}</strong></div><label className="checkbox-label"><input type="checkbox" checked={accepted} disabled={pending} onChange={event=>setAcceptedRevision(event.target.checked?state.revision:null)}/>I’ve reviewed this quote and preferred time.</label><div className="chat-review-send"><Button disabled={pending||!accepted} onClick={()=>onSubmit(existing)}>Book this clean</Button><small>We’ll reserve this time for your clean.</small></div></section>;
}
