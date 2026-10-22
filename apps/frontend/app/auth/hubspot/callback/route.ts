import {NextRequest,NextResponse} from 'next/server';
import {createHash} from 'node:crypto';
import type {SessionState,Mutation} from '@/lib/api';
import {configuredAPI,authorizeAPI} from '@/lib/private-api';
export async function GET(request:NextRequest){
 const origin=process.env.CHOREOGRAPH_ORIGIN??'http://127.0.0.1:45860';
 const result=(value:string)=>{const response=NextResponse.redirect(new URL('/demo?crm='+value,origin));response.headers.set('cache-control','no-store');response.headers.set('referrer-policy','no-referrer');return response;};
 const state=request.nextUrl.searchParams.get('state');const code=request.nextUrl.searchParams.get('code')??'';const denied=request.nextUrl.searchParams.has('error');
 const cookie=request.cookies.get('choreograph_guest')?.value;const secret=process.env.CHOREOGRAPH_BRIDGE_SECRET;
 if(request.nextUrl.origin!==origin||!state||state.length>100||state.length<32||code.length>600||(!denied&&!code)||!cookie||!/^[A-Za-z0-9_-]{32,128}$/.test(cookie)||!secret||['state','code','error'].some(name=>request.nextUrl.searchParams.getAll(name).length>1))return result('unavailable');
 try{
  const base=configuredAPI();
  const headers=new Headers({'x-choreograph-bridge':secret,'origin':origin,'cookie':`choreograph_guest=${cookie}`});
  await authorizeAPI(headers,base);
  const current=await fetch(new URL('/v1/session',base),{headers,cache:'no-store',redirect:'error',signal:AbortSignal.timeout(8_000)});
  if(!current.ok)return result('unavailable');const guest:SessionState=await current.json();
  headers.set('content-type','application/json');headers.set('x-csrf-token',guest.csrf);
  const hash=createHash('sha256').update(state+':'+code+':'+denied).digest('hex').slice(0,32);
  headers.set('idempotency-key',`${hash.slice(0,8)}-${hash.slice(8,12)}-${hash.slice(12,16)}-${hash.slice(16,20)}-${hash.slice(20)}`);
  const response=await fetch(new URL('/v1/crm/callback',base),{method:'POST',headers,
    body:JSON.stringify({generation:guest.generation,revision:guest.revision,state,code,denied}),redirect:'error',cache:'no-store',signal:AbortSignal.timeout(65_000)});
  if(!response.ok)return result('unavailable');const outcome:Mutation=await response.json();
  return result(outcome.state.crm_mode==='connected'?'connected':denied?'cancelled':'unavailable');
 }catch{return result('unavailable');}
}
