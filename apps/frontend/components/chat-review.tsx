'use client';
import {utcOffset} from '@/lib/timezone';
import {useState,type RefObject} from 'react';
import {appointment,duration,money,type RequestRecord,type SessionState} from '@/lib/api';
import {Badge,Button,Spinner} from './ui';
export type TimeSelection={start:string;status:'saving'|'error'};
export function ChatReview({state,pending,onSubmit,selection,anchor}:{state:SessionState;pending:boolean;onSubmit:(request?:RequestRecord)=>void;selection?:TimeSelection|null;anchor?:RefObject<HTMLElement|null>}){
 const [acceptedRevision,setAcceptedRevision]=useState<number|null>(null);
 const accepted=acceptedRevision===state.revision;
 if(!state.quote||(!state.draft.preferred_at&&!selection))return null;
 const latest=state.requests.at(-1);
 const matchesLatest=latest&&latest.preferred_at===state.draft.preferred_at&&latest.fields.service===state.draft.service&&latest.fields.bedrooms===state.draft.bedrooms&&latest.fields.oven===state.draft.oven&&latest.quote.cents===state.quote.cents&&latest.quote.minutes===state.quote.minutes;
 if(!selection&&matchesLatest&&['confirmed','completed'].includes(latest.status))return null;
 const existing=matchesLatest&&latest.status==='awaiting_review'?latest:undefined;
 const start=selection?.start??state.draft.preferred_at!;
 const saving=selection?.status==='saving';
 return <section ref={anchor} tabIndex={-1} className="chat-review" aria-label="Review your booking" aria-busy={saving||undefined}><div className="card-heading"><div><span className="eyebrow blue-text">{saving?'Preparing your review':selection?'Choose a time again':'Ready when you are'}</span><h3>A clean that fits.</h3></div><Badge tone="blue">{saving?'Saving time':selection?'Not confirmed':'Review'}</Badge></div><div className="chat-review-facts"><div><strong>{state.quote.items.map(item=>item.name).join(' + ')}</strong><span>{appointment(start,state.timezone)}</span><small>Timezone: {utcOffset(state.timezone,start)} · {duration(state.quote.minutes)}</small></div><strong className="chat-review-price">{money(state.quote.cents)}</strong></div>{selection?<div className="review-selection-status" role={saving?'status':'alert'}>{saving&&<Spinner/>}<p>{saving?'Saving your preferred time…':'We couldn’t confirm this time. Choose another time or refresh the demo.'}</p></div>:<><label className="checkbox-label"><input type="checkbox" checked={accepted} disabled={pending} onChange={event=>setAcceptedRevision(event.target.checked?state.revision:null)}/>I’ve reviewed this quote and preferred time.</label><div className="chat-review-send"><Button disabled={pending||!accepted} onClick={()=>onSubmit(existing)}>Book this clean</Button><small>We’ll reserve this time for your clean.</small></div></>}</section>;
}
