import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import ts from 'typescript';
import {approvedRoute,boundedBody} from '../apps/frontend/lib/bridge.ts';

function compile(file){
 return ts.transpileModule(readFileSync(new URL(file,import.meta.url),'utf8'),{
  compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022},
 }).outputText;
}
class ApiError extends Error{
 constructor(code,status=403){super(code);this.code=code;this.status=status;}
}
const state={workspace_id:'fixture',generation:1,revision:3,csrf:'synthetic-csrf',requests:[]};
function guest(fetcher,verifier=async()=> 'fresh-proof'){
 let index=0;const states=[state,false,null,false],calls=[],checks=[];
 const dependencies={react:{useState:initial=>{const slot=index++;return [states[slot]??initial,value=>{states[slot]=value;}];},
  useRef:initial=>({current:initial}),useCallback:value=>value,useEffect:()=>{}},
  '@/lib/api':{ApiError,api:async(path,options)=>{calls.push({path,options});return fetcher(path,options,calls.length);}}};
 const useGuest=new Function('require','exports',compile('../apps/frontend/components/use-guest.ts')+'\nreturn useGuest;')(
  name=>{assert.ok(name in dependencies);return dependencies[name];},{});
 const hook=useGuest(false,async(...args)=>{checks.push(args);return verifier(...args);});
 return {hook,calls,checks,states};
}

test('chat with a server-accepted receipt never opens a fresh widget',async()=>{
 const h=guest(async()=>({state}));
 assert.deepEqual(await h.hook.mutate('chat',{text:'Hello'}),{state});
 assert.equal(h.calls.length,1);assert.equal(h.calls[0].options.proof,undefined);assert.equal(h.checks.length,0);
 assert.equal(h.calls[0].options.csrf,state.csrf);
});

test('missing receipt asks once in background and retries the unchanged command',async()=>{
 const h=guest(async(path,options,n)=>{if(n===1)throw new ApiError('VERIFICATION_REQUIRED');return {state};});
 await h.hook.mutate('chat',{text:'My question'});
 assert.equal(h.calls.length,2);assert.equal(h.checks.length,1);
 const [first,second]=h.calls.map(value=>value.options);
 assert.equal(second.key,first.key);assert.deepEqual(second.body,first.body);
 assert.equal(second.proof,'fresh-proof');assert.equal(h.checks[0][0],'assistant');
 assert.equal(h.checks[0][1],first.key);assert.equal(h.checks[0][3],false);
});

test('cancelling verification sends no second command and preserves the submitted text',async()=>{
 const h=guest(async()=>{throw new ApiError('VERIFICATION_REQUIRED');},async()=>{throw new ApiError('VERIFICATION_CANCELLED');});
 assert.equal(await h.hook.mutate('chat',{text:'Keep my question'}),null);
 assert.equal(h.calls.length,1);assert.equal(h.calls[0].options.body.text,'Keep my question');
 assert.equal(h.states[2].code,'VERIFICATION_CANCELLED');
});

test('fresh proof rejection has no automatic retry loop and ordinary failures do not invoke verification',async()=>{
 const h=guest(async()=>{throw new ApiError('VERIFICATION_REQUIRED');});
 assert.equal(await h.hook.mutate('chat',{text:'Hello'}),null);
 assert.equal(h.calls.length,2);assert.equal(h.checks.length,1);assert.equal(h.states[2].code,'VERIFICATION_REQUIRED');
 for(const code of ['CSRF_REQUIRED','AI_PROVIDER_FAILED']){
  const denied=guest(async()=>{throw new ApiError(code);});
  await denied.hook.mutate('chat',{text:'Hello'});
  assert.equal(denied.calls.length,1);assert.equal(denied.checks.length,0);
 }
});

test('document replacement retains a fresh check and explicit rejected-proof recovery',async()=>{
 const h=guest(async(path,options,n)=>{if(n===1)throw new ApiError('VERIFICATION_REQUIRED');return {state};});
 await h.hook.mutate('documents/preparation/replace',{kind:'text',data:'synthetic'});
 assert.equal(h.calls[0].options.proof,'fresh-proof');assert.equal(h.checks.length,2);
 assert.equal(h.checks[0][0],'documents');assert.equal(h.checks[1][3],true);
});

const bridgeDependencies={'@/lib/bridge':{approvedRoute,boundedBody},'@/lib/private-api':{
 configuredAPI:()=>new URL('http://api:8080'),authorizeAPI:async()=>{}}};
const bridgeFactory=new Function('require','exports','fetch','process',
 compile('../apps/frontend/app/api/demo/[...path]/route.ts')+'\nreturn bridge;');
const stamp='v1.1792920000.1792921800.'+'a'.repeat(64),origin='http://localhost:45860';
test('bridge forwards only the scoped guest and well-formed human cookies and preserves the receipt response',async()=>{
 for(const value of [stamp,'invalid; unrelated=1','a'.repeat(2048)]){
  const bridge=bridgeFactory(name=>bridgeDependencies[name],{},async(url,options)=>{
   assert.equal(options.headers.get('cookie'),'choreograph_guest='+'s'.repeat(48)+(value===stamp?'; choreograph_human='+stamp:''));
   return Response.json({state},{headers:{'set-cookie':`choreograph_human=${stamp}; HttpOnly; SameSite=Lax; Path=/`}});
  },{env:{CHOREOGRAPH_ORIGIN:origin,CHOREOGRAPH_BRIDGE_SECRET:'synthetic'}});
  const response=await bridge({method:'POST',nextUrl:new URL(origin+'/api/demo/chat'),
   headers:new Headers({origin,'content-type':'application/json'}),
   cookies:{get:name=>({value:name==='choreograph_guest'?'s'.repeat(48):name==='choreograph_human'?value:'unrelated'})},
   body:new ReadableStream({start(controller){controller.close();}})},
  {params:Promise.resolve({path:['chat']})});
  assert.equal(response.status,200);assert.match(response.headers.get('set-cookie'),/HttpOnly/);
 }
});
