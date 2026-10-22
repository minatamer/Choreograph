import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {approvedRoute,boundedBody} from '../apps/frontend/lib/bridge.ts';

// Execute the actual route body with injected server configuration and transport.
// No Next server, provider, host environment values or network access is needed.
const require=createRequire(import.meta.url);
const app=fileURLToPath(new URL('../apps/frontend/',import.meta.url));
const ts=require(require.resolve('typescript',{paths:[app]}));
const source=readFileSync(new URL('../apps/frontend/app/api/demo/[...path]/route.ts',import.meta.url),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText
  .replace(/^import .*;\r?\n/gm,'').replace(/^export \{[^}]+\};?\s*$/m,'');
const factory=new Function('approvedRoute','boundedBody','configuredAPI','authorizeAPI','fetch','process',`${compiled}\nreturn bridge;`);
const origin='https://frontend.example.invalid';
const id='12345678-1234-1234-1234-123456789abc';
const cookie='f'.repeat(64);
const policy="sandbox; default-src 'none'";
function route(fetcher){
  return factory(approvedRoute,boundedBody,()=>new URL('http://api:8080'),
    async headers=>headers.set('authorization','Bearer server-identity-fixture'),fetcher,
    {env:{CHOREOGRAPH_ORIGIN:origin,CHOREOGRAPH_BRIDGE_SECRET:'bridge-fixture-not-a-real-secret'}});
}
function request(method='GET',path=['documents',id,'source'],headers={}){
  return [{method,headers:new Headers({authorization:'Bearer browser-value-must-not-pass',...headers}),
    cookies:{get:name=>name==='choreograph_guest'?{value:cookie}:undefined},
    nextUrl:new URL(`${origin}/api/demo/${path.join('/')}?page=2&version=fixture&unexpected=discard`)},
    {params:Promise.resolve({path})}];
}

for(const [label,type,body,filename] of [
  ['PDF','application/pdf','%PDF-1.7\nSynthetic source fixture.','juniper-guide.pdf'],
  ['text','text/plain; charset=utf-8','Fictional source with ordinary <b>markup</b>.','juniper-guide.txt'],
])test(`authorized ${label} source retains isolation headers without exposing upstream secrets`,async()=>{
  let calls=0;
  const bridge=route(async(url,options)=>{
    calls++;
    assert.equal(url.origin,'http://api:8080');assert.equal(url.pathname,`/v1/documents/${id}/source`);
    assert.equal(url.searchParams.get('page'),'2');assert.equal(url.searchParams.get('version'),'fixture');assert.equal(url.searchParams.has('unexpected'),false);
    assert.equal(options.headers.get('cookie'),`choreograph_guest=${cookie}`);
    assert.equal(options.headers.get('authorization'),'Bearer server-identity-fixture');
    assert.equal(options.headers.get('origin'),origin);assert.equal(options.redirect,'error');assert.equal(options.cache,'no-store');
    return new Response(body,{headers:{'content-type':type,'content-disposition':`inline; filename="${filename}"`,
      'content-security-policy':policy,'x-content-type-options':'nosniff','x-source-page':'2','cache-control':'public, max-age=3600',
      authorization:'Bearer upstream-fixture-must-not-pass','x-private-debug':'synthetic-private-fixture',
      'x-choreograph-bridge':'synthetic-upstream-fixture','access-control-allow-origin':'*'}});
  });
  const response=await bridge(...request());
  assert.equal(calls,1);assert.equal(response.status,200);assert.equal(await response.text(),body);
  assert.equal(response.headers.get('content-type'),type);assert.equal(response.headers.get('cache-control'),'no-store');
  assert.equal(response.headers.get('content-security-policy'),policy);assert.equal(response.headers.get('x-content-type-options'),'nosniff');
  assert.equal(response.headers.get('content-disposition'),`inline; filename="${filename}"`);assert.equal(response.headers.get('x-source-page'),'2');
  for(const name of ['authorization','x-private-debug','x-choreograph-bridge','access-control-allow-origin'])assert.equal(response.headers.has(name),false);
});

test('source-header forwarding does not permit internal routes or cross-origin writes',async()=>{
  let calls=0;const bridge=route(async()=>{calls++;throw Error('unavailable fixture');});
  const internal=await bridge(...request('GET',['internal','maintenance']));
  assert.equal(internal.status,404);assert.equal((await internal.json()).code,'ROUTE_UNAVAILABLE');
  const crossOrigin=await bridge(...request('POST',['session'],{origin:'https://other.example.invalid'}));
  assert.equal(crossOrigin.status,403);assert.equal((await crossOrigin.json()).code,'ORIGIN_REQUIRED');
  assert.equal(calls,0);
});
