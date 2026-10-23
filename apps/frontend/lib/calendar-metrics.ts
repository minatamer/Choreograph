import type {SessionState} from './api';

export function addDays(day:string,offset:number){const date=new Date(day+'T12:00:00Z');date.setUTCDate(date.getUTCDate()+offset);return date.toISOString().slice(0,10);}
export function localDay(instant:string|number,zone:string){
 const formatter=new Intl.DateTimeFormat('en-CA',{year:'numeric',month:'2-digit',day:'2-digit',timeZone:zone});
 return dayWith(formatter,new Date(instant));
}
/** The Business calendar keeps cancelled history; only availability/hours exclude it. */
export function appointmentsForDay(events:SessionState['calendar'],day:string,zone:string){
 return events.filter(event=>localDay(event.starts_at,zone)===day);
}
function dayWith(formatter:Intl.DateTimeFormat,date:Date){const parts=formatter.formatToParts(date);const get=(key:string)=>parts.find(part=>part.type===key)?.value;return `${get('year')}-${get('month')}-${get('day')}`;}

/** Find the real local day boundary, including midnight DST changes. */
function dayStart(day:string,formatter:Intl.DateTimeFormat){
 const utc=Date.parse(day+'T00:00:00Z');let low=utc-36*3600000,high=utc+36*3600000;
 while(high-low>1){const middle=Math.floor((low+high)/2);if(dayWith(formatter,new Date(middle))<day)low=middle;else high=middle;}
 return high;
}
export function calendarDayBounds(day:string,zone:string){
 const formatter=new Intl.DateTimeFormat('en-CA',{year:'numeric',month:'2-digit',day:'2-digit',timeZone:zone});
 return {start:dayStart(day,formatter),end:dayStart(addDays(day,1),formatter)};
}
export function calendarWeek(events:SessionState['calendar'],week:string,zone:string){
 const formatter=new Intl.DateTimeFormat('en-CA',{year:'numeric',month:'2-digit',day:'2-digit',timeZone:zone});
 const boundaries=Array.from({length:8},(_,index)=>dayStart(addDays(week,index),formatter));
 return Array.from({length:7},(_,index)=>{
  const hours=events.reduce((total,event)=>{
   if(event.state==='cancelled')return total;
   const start=Date.parse(event.starts_at),end=Date.parse(event.ends_at);
   if(!Number.isFinite(start)||!Number.isFinite(end)||end<=start)return total;
   return total+Math.max(0,Math.min(end,boundaries[index+1])-Math.max(start,boundaries[index]))/3600000;
  },0);
  return {day:addDays(week,index),hours};
 });
}
