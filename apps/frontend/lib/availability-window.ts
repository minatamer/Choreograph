import type {Week} from './api';

/** Appointment pickers start with upcoming dates, including restored chat cards. */
export function calendarWindowStart(today:string,requested?:string,rolling=true){
 const last=new Date(today+'T12:00:00Z');last.setUTCDate(last.getUTCDate()+29);
 const valid=requested&&/^\d{4}-\d{2}-\d{2}$/.test(requested)&&Number.isFinite(Date.parse(requested+'T12:00:00Z'))&&
  new Date(requested+'T12:00:00Z').toISOString().slice(0,10)===requested;
 const start=valid&&requested>=today&&requested<=last.toISOString().slice(0,10)?requested:today;
 if(rolling)return start;
 const monday=new Date(start+'T12:00:00Z');monday.setUTCDate(monday.getUTCDate()-(monday.getUTCDay()+6)%7);
 return monday.toISOString().slice(0,10);
}

export function calendarSelectedDay(value:Week,today:string,previous:string,matches:(day:Week['days'][number])=>boolean){
 const upcoming=value.days.filter(day=>day.date>=today&&day.status!=='past'&&day.status!=='outside');
 if(upcoming.some(day=>day.date===previous))return previous;
 return (upcoming.find(matches)??upcoming.find(day=>day.slots.length)??upcoming[0])?.date??'';
}
