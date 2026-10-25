import type {SessionState,Week} from './api';
type Day=Week['days'][number];

export function availabilityReply(draft:Pick<SessionState['draft'],'service'|'bedrooms'>){
 if(!draft.service)return {
  prompt:draft.bedrooms?'Which clean? Choose regular, deep or move-out.':'Choose a clean, then the bedrooms (1–3), to check exact times.',
  example:draft.bedrooms?'Deep clean. Show available times.':'Deep clean for 2 bedrooms. Show available times.',
  label:'Choose cleaning type',choices:[{label:'Regular',text:'A regular clean'},{label:'Deep',text:'A deep clean'},{label:'Move-out',text:'A move-out clean'}],
 };
 if(!draft.bedrooms)return {prompt:'How many bedrooms? Choose 1–3 to check exact times.',example:'2 bedrooms. Show available times.',
  label:'Choose bedroom count',choices:[1,2,3].map(count=>({label:String(count),text:`${count} bedroom${count>1?'s':''}`}))};
 return null;
}

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
