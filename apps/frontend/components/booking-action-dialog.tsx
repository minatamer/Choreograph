'use client';
import {appointment,duration,money,type Mutation,type RequestRecord,type SessionState} from '@/lib/api';
import {utcOffset} from '@/lib/timezone';
import {ConfirmationDialog} from './confirmation-dialog';

export function BookingActionDialog({record,zone,action,pending,opener,fallbackFocus,onClose,onConfirm}:{record:RequestRecord;zone:string;action:'cancel'|'complete';pending:boolean;opener:HTMLElement|null;fallbackFocus:HTMLElement|null;onClose:()=>void;onConfirm:()=>Promise<Mutation|SessionState|null>}){
 const completing=action==='complete',declining=record.status==='awaiting_review';
 const title=completing?'Mark this clean completed?':declining?'Decline this request?':'Cancel this booking?';
 const confirmLabel=completing?'Mark completed':declining?'Decline request':'Confirm cancellation';
 return <ConfirmationDialog layoutId={`booking-action-${record.id}`} title={title} eyebrow={completing?'Update booking':'Review cancellation'} confirmLabel={confirmLabel} cancelLabel={declining?'Keep request':'Keep booking'} pending={pending} opener={opener} fallbackFocus={fallbackFocus} onClose={onClose} onConfirm={async()=>Boolean(await onConfirm())}>
  <div className="management-current"><strong>{record.quote.items.map(item=>item.name).join(' + ')}</strong><span>{appointment(record.preferred_at,zone)}</span><small>Timezone: {utcOffset(zone,record.preferred_at)} · {duration(record.quote.minutes)} · {money(record.quote.cents)}</small></div>
  <p>{completing?'This clean will be marked completed.':declining?'This request hasn’t reserved a time. Confirm below to decline it.':'Cancelling releases this appointment. It stays booked until you confirm below.'}</p>
 </ConfirmationDialog>;
}
