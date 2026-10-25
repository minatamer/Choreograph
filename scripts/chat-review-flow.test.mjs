import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import ts from 'typescript';
import * as questions from '../apps/frontend/lib/chat-questions.ts';
import * as timezone from '../apps/frontend/lib/timezone.ts';
import {reviewMessage} from '../apps/frontend/lib/chat-sources.ts';

const require=createRequire(import.meta.url),jsx=require('react/jsx-runtime'),noop=()=>null;
const compile=file=>ts.transpileModule(readFileSync(new URL(file,import.meta.url),'utf8'),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},
}).outputText;
const api={}, {utcOffset}=timezone;
new Function('require','exports',compile('../apps/frontend/lib/api.ts'))(name=>{assert.equal(name,'./timezone');return timezone;},api);
function find(node,predicate){
 if(!node||typeof node!=='object')return;
 if(predicate(node))return node;
 for(const child of [node.props?.children].flat(Infinity)){const match=find(child,predicate);if(match)return match;}
}
const time='2026-10-27T06:30:00Z';
const state={workspace_id:'fixture',revision:2,timezone:'Africa/Cairo',quote:{cents:12000,minutes:180,items:[{name:'Deep cleaning · 2 bedrooms'}]},
 draft:{service:'deep',bedrooms:2,oven:false,preferred_at:null},requests:[],documents:[],scenario:{},
 messages:[{id:'quote',role:'assistant',text:'Quote',cards:['quote'],claims:[]},{id:'times',role:'assistant',text:'Choose a time',cards:['reserve'],claims:[]}]};
const chatCode=compile('../apps/frontend/components/chat-workspace.tsx'),reviewCode=compile('../apps/frontend/components/chat-review.tsx');

function chat({pending=false}={}){
 const slots=[],effects=[],saved=[],revealed=[],submissions=[];let index=0,tree,current=state,resolve,reject,sets=0;
 const response=new Promise((yes,no)=>{resolve=yes;reject=no;});
 function Review(){}
 const target={isConnected:true},reveal={current:node=>revealed.push(node)};
 const deps={react:{Fragment:Symbol.for('react.fragment'),useState:initial=>{const n=index++;slots[n]??={value:initial};
  return [slots[n].value,update=>{sets++;slots[n].value=typeof update==='function'?update(slots[n].value):update;}];},
  useRef:initial=>{const n=index++;slots[n]??={current:initial};return slots[n];},
  useLayoutEffect:(callback,next)=>{const n=index++;if(!slots[n]||next.some((value,j)=>!Object.is(value,slots[n].deps[j]))){const old=slots[n];slots[n]={deps:next,cleanup:old?.cleanup};effects.push(()=>{old?.cleanup?.();slots[n].cleanup=callback();});}}},
  'react/jsx-runtime':jsx,'@/lib/api':api,'@/lib/chat-questions':questions,
  '@/lib/chat-messages':{acceptedMessage:noop,bookingMessageAnchors:()=>new Map(),conversationMessages:messages=>messages.map(message=>({key:message.id,message}))},
  './ui':{Button:noop,Badge:noop,Arrow:noop,Mark:noop,Spinner:noop},'./week-calendar':{WeekCalendar:function Calendar(){}},
  './booking-outcome':{BookingOutcome:noop},'./chat-sources':{ChatSources:noop},'@/lib/chat-sources':{reviewMessage},
  './conversation-library':{ConversationLibrary:noop},'./use-chat-scroll':{useChatScroll:()=>({pane:{current:null},content:{current:null},reveal})},
  './reply-text':{ReplyText:noop},'./chat-review':{ChatReview:Review},'./chat-booking-management':{ChatBookingManagement:noop}};
 const Component=new Function('require','exports',chatCode+'\nreturn ChatWorkspace;')(name=>{assert.ok(name in deps);return deps[name];},{});
 function render(){index=0;tree=Component({state:current,pending,text:'Unsent question',setText:noop,onSend:noop,
  onEdit:fields=>{saved.push(fields);return response;},onSubmit:value=>submissions.push(value),onBookingAction:noop,onBusiness:noop,onTour:noop});
  find(tree,node=>node.type===Review).props.anchor.current=target;for(const effect of effects.splice(0))effect();}
 render();
 return {saved,revealed,submissions,render,target,review:()=>find(tree,node=>node.type===Review),
  choose:start=>find(tree,node=>node.props?.rolling===true).props.onSelect(start),sets:()=>sets,
  settle:async(next={...state,revision:3,draft:{...state.draft,preferred_at:time}})=>{
   if(next){current=next;resolve({state:next});}else resolve(null);for(let n=0;n<5;n++)await Promise.resolve();render();},
  reject:async()=>{reject(Error('Network'));for(let n=0;n<5;n++)await Promise.resolve();render();},
  unmount:()=>slots.forEach(slot=>slot?.cleanup?.())};
}

test('selection reveals a loading review before the slow save completes and never books automatically',async()=>{
 const h=chat();h.choose(time);assert.deepEqual(h.saved,[{preferred_at:time}]);h.render();
 assert.deepEqual(h.review().props.selection,{start:time,status:'saving'});
 assert.deepEqual(h.revealed,[h.target]);assert.equal(h.review().props.pending,true);assert.deepEqual(h.submissions,[]);
 await h.settle();assert.equal(h.review().props.selection,null);assert.equal(h.review().props.state.draft.preferred_at,time);
 assert.equal(h.revealed.length,1);assert.deepEqual(h.submissions,[]);h.unmount();
});

test('failed and thrown saves replace the loading state with an honest inline error',async()=>{
 for(const failure of ['null','throw']){
  const h=chat();h.choose(time);h.render();if(failure==='null')await h.settle(null);else await h.reject();
  assert.equal(h.review().props.selection.status,'error');assert.equal(h.review().props.state.draft.preferred_at,null);
  assert.deepEqual(h.submissions,[]);h.unmount();
 }
});

test('selection guards duplicate/pending clicks and fences late completion after unmount',async()=>{
 const h=chat();h.choose(time);h.choose('2026-10-27T07:00:00Z');assert.equal(h.saved.length,1);
 h.render();h.unmount();const sets=h.sets();await h.settle();assert.equal(h.sets(),sets);
 const busy=chat({pending:true});busy.choose(time);assert.equal(busy.saved.length,0);busy.unmount();
});

test('reservation review anchors to its own calendar rather than an older quote',()=>{
 assert.equal(reviewMessage(state.messages),'times');
 assert.equal(reviewMessage([...state.messages,{id:'guide',role:'assistant',cards:['sources']}]),'times');
});

function review(selection,preferred=null){
 const deps={react:{useState:()=>[null,noop]},'react/jsx-runtime':jsx,'@/lib/api':api,'@/lib/timezone':{utcOffset},
  './ui':{Badge:noop,Button:function Button(){},Spinner:function Spinner(){}}};
 const Component=new Function('require','exports',reviewCode+'\nreturn ChatReview;')(name=>deps[name],{});
 return Component({state:{...state,draft:{...state.draft,preferred_at:preferred}},pending:false,selection,onSubmit:()=>assert.fail('No implicit booking')});
}

test('actual review card has an announced spinner while saving and no approval controls until ready',()=>{
 const loading=review({start:time,status:'saving'});
 assert.ok(loading);assert.equal(loading.props['aria-busy'],true);assert.equal(loading.props.tabIndex,-1);
 assert.ok(find(loading,node=>node.props?.role==='status'));
 assert.equal(find(loading,node=>node.type==='input'),undefined);assert.equal(find(loading,node=>node.props?.children==='Book this clean'),undefined);
 const error=review({start:time,status:'error'});assert.ok(find(error,node=>node.props?.role==='alert'));
 assert.equal(find(error,node=>node.type==='input'),undefined);
 const ready=review(null,time);assert.equal(ready.props['aria-busy'],undefined);
 assert.equal(find(ready,node=>node.type==='input').props.checked,false);
 assert.equal(find(ready,node=>node.props?.children==='Book this clean').props.disabled,true);
});
