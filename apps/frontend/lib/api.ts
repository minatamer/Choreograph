import type {components} from './generated/api';
export type SessionState=components['schemas']['SessionView'];
export type Mutation=components['schemas']['MutationView'];
export type Week=components['schemas']['WeekView'];
export type Draft=components['schemas']['DraftView'];
export type Quote=components['schemas']['QuoteView'];
export type RequestRecord=components['schemas']['RequestView'];
export type KnowledgeDocument=components['schemas']['DocumentView'];
export type DocumentDetail=components['schemas']['DocumentDetail'];
export class ApiError extends Error {
  constructor(public code:string,message:string,public status:number){super(message);}
}
export async function api<T>(path:string,options:{method?:string;body?:unknown;csrf?:string;key?:string;signal?:AbortSignal}={}):Promise<T>{
  const headers:Record<string,string>={};
  if(options.body!==undefined)headers['content-type']='application/json';
  if(options.csrf)headers['x-csrf-token']=options.csrf;
  if(options.key)headers['idempotency-key']=options.key;
  const response=await fetch('/api/demo/'+path,{method:options.method??'GET',headers,
    body:options.body===undefined?undefined:JSON.stringify(options.body),credentials:'same-origin',cache:'no-store',signal:options.signal});
  const result=await response.json();
  if(!response.ok)throw new ApiError(typeof result.code==='string'?result.code:'REQUEST_FAILED',
    typeof result.message==='string'?result.message:'Please try again in a moment.',response.status);
  return result as T;
}
export function money(cents:number){return new Intl.NumberFormat(undefined,{style:'currency',currency:'USD',maximumFractionDigits:2}).format(cents/100);}
export function duration(minutes:number){return `${Math.floor(minutes/60)}h${minutes%60?' '+minutes%60+'m':''}`;}
export function clockTime(value:string,zone:string){return new Intl.DateTimeFormat(undefined,{hour:'2-digit',minute:'2-digit',timeZone:zone}).format(new Date(value));}
export function appointment(value:string,zone:string){return new Intl.DateTimeFormat(undefined,{weekday:'short',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',timeZone:zone}).format(new Date(value));}
