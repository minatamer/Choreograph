export type AppointmentPeriod='all'|'morning'|'afternoon';
export function periodSlots<T extends {start:string}>(slots:T[],zone:string,period:AppointmentPeriod):T[]{
 if(period==='all')return slots;
 const formatter=new Intl.DateTimeFormat('en-GB',{timeZone:zone,hour:'2-digit',hourCycle:'h23'});
 return slots.filter(slot=>{const hour=Number(formatter.format(new Date(slot.start)));return period==='morning'?hour<12:hour>=12;});
}
