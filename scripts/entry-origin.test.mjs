import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import ts from 'typescript';
import path from 'node:path';
import {unstable_getResponseFromNextConfig} from 'next/experimental/testing/server.js';
import {approvedRoute,boundedBody} from '../apps/frontend/lib/bridge.ts';

function compile(path){
 return ts.transpileModule(readFileSync(new URL(path,import.meta.url),'utf8'),{
  compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022},
 }).outputText.replace(/^import .*;\r?\n/gm,'').replace(/^export \{.*\};?\r?\n/gm,'').replace(/^export /gm,'');
}
const origin='http://localhost:45860';
const configSource=ts.transpileModule(readFileSync(new URL('../apps/frontend/next.config.ts',import.meta.url),'utf8'),{
 compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022},
}).outputText.replace(/^import .*;\r?\n/gm,'').replaceAll('import.meta.dirname','"/synthetic/frontend"')
 .replace(/^export default config;?/gm,'return config;');
const configFactory=new Function('path','process',configSource);
function config(env=origin){return configFactory(path,{env:{CHOREOGRAPH_ORIGIN:env}});}
function pageResponse(address,env=origin){return unstable_getResponseFromNextConfig({url:address,
 headers:{host:new URL(address).host},nextConfig:config(env)});}

test('Next host matching selects the local redirect and configuration retains its port',async()=>{
 assert.equal((await config().redirects())[0].destination,origin+'/demo/:path*');
 for(const suffix of ['/demo','/demo/workspace?view=business']){
  const result=await pageResponse('http://127.0.0.1:45860'+suffix);
  assert.equal(result.status,307);
  // This experimental Next helper builds its base from hostname and drops
  // destination ports. Check its matching/path behavior here; actual HTTP
  // acceptance separately verifies the complete :45860 Location header.
  const target=new URL(result.headers.get('location'));
  assert.equal(target.hostname,'localhost');
  assert.equal(target.pathname+target.search,suffix);
  assert.equal(result.headers.has('set-cookie'),false);
 }
});

test('canonical pages do not loop and protected API routes are never redirected',async()=>{
 for(const address of [origin+'/demo','http://127.0.0.1:45860/api/demo/crm/skip']){
  const result=await pageResponse(address);
  assert.equal(result.status,200);
  assert.equal(result.headers.has('location'),false);
 }
});

test('host redirects are limited to the configured local OAuth setup',async()=>{
 for(const [address,env] of [['http://127.0.0.1:45860/demo',''],
  ['http://127.0.0.1:45860/demo','https://production.example.invalid'],
  ['https://untrusted.example.invalid/demo',origin]]){
  assert.equal((await pageResponse(address,env)).headers.has('location'),false);
 }
});

const bridgeFactory=new Function('approvedRoute','boundedBody','configuredAPI','authorizeAPI','fetch','process',
 compile('../apps/frontend/app/api/demo/[...path]/route.ts')+'\nreturn bridge;');
function bridge(fetcher){
 return bridgeFactory(approvedRoute,boundedBody,()=>new URL('http://api:8080'),async()=>{},fetcher,
  {env:{CHOREOGRAPH_ORIGIN:origin,CHOREOGRAPH_BRIDGE_SECRET:'synthetic-bridge'}});
}
function request(address){
 return {method:'POST',nextUrl:new URL(address+'/api/demo/crm/skip'),
  headers:new Headers({origin:address,'content-type':'application/json','x-csrf-token':'synthetic-csrf',
   'idempotency-key':'12345678-1234-4234-8234-123456789abc'}),
  cookies:{get:()=>({value:'s'.repeat(48)})},
  body:new ReadableStream({start(c){c.enqueue(new TextEncoder().encode('{"generation":1,"revision":3}'));c.close();}})};
}

test('wrong-origin skip is rejected before transport with a useful public error',async()=>{
 let calls=0;
 const response=await bridge(async()=>{calls++;throw Error('Unexpected fetch');})(request('http://127.0.0.1:45860'),
  {params:Promise.resolve({path:['crm','skip']})});
 assert.equal(response.status,403);
 const result=await response.json();
 assert.equal(result.code,'ORIGIN_REQUIRED');assert.match(result.message,/Reload the demo/);
 assert.equal(calls,0);
});

test('canonical skip reaches the existing command once with session and CSRF intact',async()=>{
 let calls=0;
 const response=await bridge(async(url,options)=>{
  calls++;assert.equal(url.href,'http://api:8080/v1/crm/skip');
  assert.equal(options.method,'POST');assert.equal(options.headers.get('origin'),origin);
  assert.equal(options.headers.get('x-csrf-token'),'synthetic-csrf');
  assert.equal(options.headers.get('cookie'),'choreograph_guest='+'s'.repeat(48));
  assert.deepEqual(JSON.parse(new TextDecoder().decode(options.body)),{generation:1,revision:3});
  return Response.json({state:{crm_mode:'skipped'}});
 })(request(origin),{params:Promise.resolve({path:['crm','skip']})});
 assert.equal(response.status,200);assert.equal((await response.json()).state.crm_mode,'skipped');
 assert.equal(calls,1);
});
