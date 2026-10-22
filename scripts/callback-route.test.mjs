import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';

// Execute the actual callback route with server-only configuration and injected
// fetch. No provider, account, environment secret or listening server is used.
const require=createRequire(import.meta.url);
const app=fileURLToPath(new URL('../apps/frontend/',import.meta.url));
const ts=require(require.resolve('typescript',{paths:[app]}));
const source=readFileSync(new URL('../apps/frontend/app/auth/hubspot/callback/route.ts',import.meta.url),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText.replace(/^import .*;\r?\n/gm,'').replace(/^export /gm,'');
const factory=new Function('NextResponse','createHash','configuredAPI','authorizeAPI','fetch','process',`${compiled}\nreturn GET;`);
const origin='https://frontend.example.invalid';const state='s'.repeat(48);const cookie='c'.repeat(64);
const next={redirect:url=>new Response(null,{status:307,headers:{location:String(url)}})};
function route(fetcher){return factory(next,createHash,()=>new URL('http://api:8080'),async headers=>headers.set('authorization','Bearer synthetic-server-identity'),fetcher,{env:{CHOREOGRAPH_ORIGIN:origin,CHOREOGRAPH_BRIDGE_SECRET:'synthetic-bridge'}});}
function request(query=`state=${state}&code=synthetic-code`,base=origin){return {nextUrl:new URL(base+'/auth/hubspot/callback?'+query),cookies:{get:()=>({value:cookie})}};}
function isolated(response){assert.equal(response.headers.get('cache-control'),'no-store');assert.equal(response.headers.get('referrer-policy'),'no-referrer');assert.equal(response.headers.has('set-cookie'),false);assert.equal(response.headers.get('location').includes(state),false);assert.equal(response.headers.get('location').includes('synthetic-code'),false);}

test('callback uses server session/CSRF and a stable replay key; redirect drops the code',async()=>{
 const sent=[];const callback=route(async(url,options)=>{
  assert.equal(url.origin,'http://api:8080');assert.equal(options.cache,'no-store');assert.equal(options.redirect,'error');
  assert.equal(options.headers.get('cookie'),`choreograph_guest=${cookie}`);assert.equal(options.headers.get('authorization'),'Bearer synthetic-server-identity');
  if(url.pathname==='/v1/session')return Response.json({generation:7,revision:9,csrf:'synthetic-csrf'});
  assert.equal(url.pathname,'/v1/crm/callback');assert.equal(options.method,'POST');assert.equal(options.headers.get('origin'),origin);
  assert.equal(options.headers.get('x-csrf-token'),'synthetic-csrf');sent.push({key:options.headers.get('idempotency-key'),body:JSON.parse(options.body)});
  return Response.json({state:{crm_mode:'connected'}});
 });
 for(let i=0;i<2;i++){const response=await callback(request());isolated(response);assert.equal(response.headers.get('location'),origin+'/demo?crm=connected');}
 assert.equal(sent[0].key,sent[1].key);assert.match(sent[0].key,/^[a-f0-9-]{36}$/);
 assert.deepEqual(sent[0].body,{generation:7,revision:9,state,code:'synthetic-code',denied:false});
});

test('callback rejects cross-origin, duplicate and missing parameters before fetch',async()=>{
 let calls=0;const callback=route(async()=>{calls++;throw Error('unexpected transport');});
 for(const input of [request(`state=${state}&code=x&code=y`),request(`state=${state}`),request(`state=${state}&code=x`,'https://other.example.invalid'),request('state=short&code=x')]){
  const response=await callback(input);isolated(response);assert.equal(response.headers.get('location'),origin+'/demo?crm=unavailable');
 }
 assert.equal(calls,0);
});

test('denial is explicit and upstream errors never enter redirect or public output',async()=>{
 let body;const callback=route(async(url,options)=>url.pathname==='/v1/session'?Response.json({generation:1,revision:1,csrf:'synthetic-csrf'}):(body=JSON.parse(options.body),Response.json({state:{crm_mode:'skipped'}})));
 const denied=await callback(request(`state=${state}&error=access_denied`));isolated(denied);assert.equal(body.denied,true);assert.equal(body.code,'');assert.equal(denied.headers.get('location'),origin+'/demo?crm=cancelled');
 const failed=await route(async()=>{throw Error('synthetic-private-upstream-message');})(request());isolated(failed);assert.equal(failed.headers.get('location'),origin+'/demo?crm=unavailable');
});
