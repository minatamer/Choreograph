import type {SessionState} from './api';

type Appointment=SessionState['calendar'][number];
type Status=Appointment['state'];
export type CalendarStatus=Exclude<Status,'blocked'>;
export const APPOINTMENT_STATUS={
 confirmed:{label:'Scheduled',tone:'blue',symbol:'◷'},
 completed:{label:'Completed',tone:'green',symbol:'✓'},
 cancelled:{label:'Cancelled',tone:'red',symbol:'×'},
 blocked:{label:'Unavailable',tone:'neutral',symbol:'−'},
} as const;

/** The original unlinked sample appointments use blocked for overlap protection. */
export function appointmentPresentation(event:Appointment){
 const seed=event.state==='blocked'&&!event.enquiry_id&&event.label==='Existing appointment';
 const status:Status=seed?'confirmed':event.state;
 return {status,title:seed?'Cleaning appointment':event.label,...APPOINTMENT_STATUS[status]};
}

export function requestTone(status:SessionState['requests'][number]['status']){
 return status==='awaiting_review'?'amber':APPOINTMENT_STATUS[status].tone;
}

export function appointmentVisible(event:Appointment,visible:ReadonlySet<CalendarStatus>){
 const status=appointmentPresentation(event).status;
 return status==='blocked'||visible.has(status);
}
