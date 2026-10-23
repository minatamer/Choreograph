'use client';
import {utcOffset} from '@/lib/timezone';
import {useEffect,useState} from 'react';
import {money,duration,appointment,type SessionState,type RequestRecord} from '@/lib/api';
import {Badge,Button} from './ui';
import {WeekCalendar} from './week-calendar';
import {BusinessOverview} from './business-overview';
import {requestTone} from '@/lib/appointment-status';
type Action=(record:RequestRecord,action:string,fields?:Record<string,unknown>)=>void;
function RequestReview({record,state,pending,onAction}:{record:RequestRecord;state:SessionState;pending:boolean;onAction:Action}){
  const [staff,setStaff]=useState('');const [reviewed,setReviewed]=useState(false);const [changing,setChanging]=useState(false);const [candidate,setCandidate]=useState<string|null>(null);
  useEffect(()=>{setReviewed(false);setChanging(false);setCandidate(null);},[record.revision]);
  const confirmed=record.status==='confirmed',awaiting=record.status==='awaiting_review';
  const labels={awaiting_review:'Awaiting review',confirmed:'Confirmed',cancelled:'Cancelled',completed:'Completed'};
  function act(action:string){onAction(record,action,{staff_id:staff||null,...(candidate?{preferred_at:candidate}:{})});}
  return <article className="request-record" aria-label={`${record.quote.items[0].name} request`}><div className="card-heading"><h2>{record.quote.items[0].name}</h2><Badge tone={requestTone(record.status)}>{labels[record.status]}</Badge></div>
    <div className="request-facts"><div><small>{candidate?'Proposed time':'Appointment'}</small><strong>{appointment(candidate??record.preferred_at,state.timezone)}</strong><small>Timezone: {utcOffset(state.timezone,candidate??record.preferred_at)} · {duration(record.quote.minutes)}</small></div><div><small>Quote</small><strong>{money(record.quote.cents)}</strong><small>{record.fields.oven?'Includes inside oven':'Cleaning service'}</small></div>{record.booking&&<div><small>Cleaner</small><strong>{record.booking.staff_id==='ada'?'Ada':'Noah'}</strong><small>{record.crm_state==='not_connected'?'CRM not connected':record.crm_state==='pending'?'CRM sync pending':record.crm_state.replaceAll('_',' ')}</small></div>}</div>
    {(awaiting||confirmed)&&<><div className="review-toolbar"><label>Cleaner<select aria-label="Assign cleaner" value={staff} disabled={pending} onChange={event=>{setStaff(event.target.value);setReviewed(false);}}><option value="">Any available cleaner</option><option value="ada">Ada</option><option value="noah">Noah</option></select></label><Button kind="secondary" disabled={pending} onClick={()=>{setChanging(value=>!value);setCandidate(null);setReviewed(false);}}>{changing?'Close calendar':confirmed?'Reschedule':'Choose another time'}</Button></div>
      {changing&&<WeekCalendar state={state} request={record} selectedTime={candidate} pending={pending} onSelect={value=>{setCandidate(value);setReviewed(false);}}/>}
      {(awaiting||candidate)&&<div className="approval-controls"><label className="checkbox-label"><input type="checkbox" checked={reviewed} disabled={pending} onChange={event=>setReviewed(event.target.checked)}/>I’ve reviewed this request.</label><Button disabled={pending||!reviewed||(confirmed&&!candidate)} onClick={()=>act(confirmed?'reschedule':'approve')}>{confirmed?'Confirm new time':'Approve and book'}</Button></div>}
      <div className="lifecycle-actions"><Button kind="quiet" disabled={pending} onClick={()=>{if(window.confirm(awaiting?'Decline this request?':'Cancel this booking and release its time?'))onAction(record,'cancel');}}>{awaiting?'Decline request':'Cancel booking'}</Button>{confirmed&&<Button kind="secondary" disabled={pending} onClick={()=>{if(window.confirm('Mark this booking completed?'))onAction(record,'complete');}}>Mark completed</Button>}</div>
    </>}
  </article>;
}
export function BusinessReview({state,pending,onAction,selectedWeek,onWeek,onClear}:{state:SessionState;pending:boolean;onAction:Action;selectedWeek:string;onWeek:(week:string)=>void;onClear:(id:string)=>Promise<boolean>}){
  const first=state.calendar_week_start??state.scenario.week_start??'';const week=selectedWeek||first;
  return <div className="business-content">{week&&<BusinessOverview state={state} week={week} onWeek={onWeek} pending={pending} onClear={onClear}/>}<section id="booking-requests" tabIndex={-1} className="business-queue" data-tour="review" aria-label="Booking requests"><div className="queue-title"><h2>A little review. Then it’s booked.</h2><span>{state.summary.awaiting_count} to review</span></div>{!state.requests.length?<div className="business-empty"><span aria-hidden="true">✓</span><div><h3>You’re all caught up.</h3><p>Try a clean in Customer view. Its request will arrive here for your approval.</p></div></div>:state.requests.map(record=><RequestReview key={record.id} record={record} state={state} pending={pending} onAction={onAction}/>)}</section></div>;
}
