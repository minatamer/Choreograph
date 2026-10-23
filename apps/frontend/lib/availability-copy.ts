import type {Week} from './api';
type Day=Week['days'][number];

export function availabilityLabel(day:Day,today:string){
 if(day.status==='past')return day.date<today?'Past date':'Too late today';
 return {outside:'Not open yet',closed:'Closed',available:'Available',busy:'No times'}[day.status];
}

export function unavailableReason(day:Day,today:string,length:string){
 if(day.status==='past')return day.date<today?'This date has passed. Choose an upcoming day.':`There isn’t enough time left today for this ${length} clean.`;
 if(day.status==='busy')return `No ${length} appointment fits on this day. Try another date.`;
 if(day.status==='closed')return 'Juniper is open Monday to Saturday.';
 return 'Bookings open 30 days ahead. Choose an earlier date.';
}
