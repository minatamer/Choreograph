import {test} from 'node:test';
import assert from 'node:assert/strict';
import {configuredAPI,createAPIAuthorizer} from '../apps/frontend/lib/private-api.ts';

const values={CHOREOGRAPH_API_AUTH:'google'};
const target=new URL('https://api.example.run.app');
const jwt=(aud,exp)=>['test',Buffer.from(JSON.stringify({aud,exp})).toString('base64url'),'signature'].join('.');
test('private API auth is opt-in and never inherits a browser-selected destination',async()=>{
  let calls=0;
  const auth=createAPIAuthorizer(async()=>{calls++;throw Error('must not call');});
  await auth(new Headers(),target,{});assert.equal(calls,0);
  for(const url of ['https://user:password@example.com','http://example.com/path','http://remote.example.invalid','ftp://example.com'])assert.throws(()=>configuredAPI({CHOREOGRAPH_API_URL:url}));
  for(const url of ['http://127.0.0.1:45861','http://api:8080','https://api.example.run.app'])assert.equal(configuredAPI({CHOREOGRAPH_API_URL:url}).origin,url);
  await assert.rejects(auth(new Headers(),new URL('http://127.0.0.1'),values),/CONFIGURATION_INVALID/);
  await assert.rejects(auth(new Headers(),target,{CHOREOGRAPH_API_AUTH:'invalid'}),/CONFIGURATION_INVALID/);
  assert.equal(calls,0);
});
test('metadata identity is bounded, cached and shared across concurrent requests',async()=>{
  let calls=0;let now=1_000_000;
  const auth=createAPIAuthorizer(async(url,options)=>{
    calls++;assert.equal(url.hostname,'metadata.google.internal');assert.equal(url.searchParams.get('audience'),target.origin);
    assert.equal(options.headers['Metadata-Flavor'],'Google');assert.equal(options.redirect,'error');
    return new Response(jwt(target.origin,now/1000+300),{headers:{'Metadata-Flavor':'Google'}});
  },()=>now);
  const first=new Headers(),second=new Headers();await Promise.all([auth(first,target,values),auth(second,target,values)]);
  assert.equal(calls,1);assert.equal(first.get('authorization'),second.get('authorization'));
  now+=250_000;await auth(new Headers(),target,values);assert.equal(calls,2);
});
test('metadata failure never falls back to an unauthenticated upstream request',async()=>{
  for(const response of [new Response('bad',{status:503}),new Response('not a token',{headers:{'Metadata-Flavor':'Google'}}),
    new Response(jwt('https://wrong.example',Date.now()/1000+300),{headers:{'Metadata-Flavor':'Google'}})]){
    const headers=new Headers();const auth=createAPIAuthorizer(async()=>response);
    await assert.rejects(auth(headers,target,values));assert.equal(headers.has('authorization'),false);
  }
});
