import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import ts from 'typescript';
import * as questions from '../apps/frontend/lib/chat-questions.ts';
import * as windowing from '../apps/frontend/lib/availability-window.ts';

const require=createRequire(import.meta.url),jsx=require('react/jsx-runtime');
const noop=()=>null;
const compiled=ts.transpileModule(readFileSync(new URL('../apps/frontend/components/chat-workspace.tsx',import.meta.url),'utf8'),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},
}).outputText;
const deps={react:{Fragment:Symbol.for('react.fragment'),useState:value=>[value,noop],useRef:value=>({current:value}),useLayoutEffect:noop},
 'react/jsx-runtime':jsx,'@/lib/api':{money:noop,duration:noop},'@/lib/chat-questions':questions,
 '@/lib/chat-messages':{acceptedMessage:noop,bookingMessageAnchors:()=>new Map(),conversationMessages:messages=>messages.map(message=>({key:message.id,message}))},
 './ui':{Button:noop,Badge:noop,Arrow:noop,Mark:noop,Spinner:noop},'./week-calendar':{WeekCalendar:noop},
 './booking-outcome':{BookingOutcome:noop},'./chat-sources':{ChatSources:noop},'@/lib/chat-sources':{reviewMessage:noop},
 './conversation-library':{ConversationLibrary:noop},'./use-chat-scroll':{useChatScroll:()=>({pane:{current:null},content:{current:null}})},
 './reply-text':{ReplyText:noop},'./chat-review':{ChatReview:noop},'./chat-booking-management':{ChatBookingManagement:noop}};
const ChatWorkspace=new Function('require','exports',compiled+'\nreturn ChatWorkspace;')(name=>{
 assert.ok(name in deps,'Unexpected component dependency');return deps[name];},{});
function find(node,predicate){
 if(!node||typeof node!=='object')return;
 if(predicate(node))return node;
 for(const child of [node.props?.children].flat(Infinity)){const match=find(child,predicate);if(match)return match;}
}
function render(fields={},pending=false){
 const sent=[],draftEdits=[];let text='My unfinished question';
 const state={draft:{service:null,bedrooms:null,preferred_at:null},quote:null,requests:[],documents:[],
  messages:[],scenario:{busy_date:'2030-01-03'},...fields};
 const tree=ChatWorkspace({state,pending,text,setText:update=>{text=typeof update==='function'?update(text):update;},
  onSend:async value=>{sent.push(value);return {state};},onEdit:async value=>{draftEdits.push(value);return {state:{...state,draft:{...state.draft,...value}}};},onSubmit:noop,onBookingAction:noop,onBusiness:noop,onTour:noop});
 return {tree,sent,draftEdits,getText:()=>text,button:find(tree,node=>node.type==='button'&&node.props.className==='reservation-shortcut')};
}

test('reservation remains a separate visible action across initial, guided and booked conversations',()=>{
 for(const fields of [{},{messages:[{id:'a',role:'assistant',text:'Guide answer',cards:[],claims:[],suggestions:[]}]},
  {draft:{service:'regular',bedrooms:2,preferred_at:null},quote:{}},
  {requests:[{status:'confirmed'}]},
  {messages:[{id:'u',role:'user',text:questions.RESERVATION_SHORTCUT.text,cards:[],claims:[]}]}]){
  const h=render(fields);assert.ok(h.button);assert.equal(h.button.props.disabled,false);
 }
});

test('reservation click uses the normal chat send and preserves an unrelated typed question',async()=>{
 const h=render();h.button.props.onClick();await Promise.resolve();await Promise.resolve();
 assert.deepEqual(h.sent,[questions.RESERVATION_SHORTCUT.text]);
 assert.equal(h.getText(),'My unfinished question');
});

test('pending reservation clicks cannot bypass the shared send guard',()=>{
 const h=render({},true);assert.equal(h.button.props.disabled,true);h.button.props.onClick();assert.deepEqual(h.sent,[]);
});

test('reservation replies render the rolling calendar before a quote and slot selection only edits the draft',()=>{
 const h=render({messages:[{id:'a',role:'assistant',text:'Browse the next seven days.',cards:['reserve'],claims:[],requested_date:'2030-01-03'}]});
 const calendar=find(h.tree,node=>node.props?.rolling===true);
 assert.ok(calendar);assert.equal(calendar.props.initialDate,'2030-01-03');assert.equal(calendar.props.state.quote,null);
 calendar.props.onSelect('2030-01-04T10:00:00Z');
 assert.deepEqual(h.draftEdits,[{preferred_at:'2030-01-04T10:00:00Z'}]);
 assert.deepEqual(h.sent,[]);
});

test('ordinary schedule replies use the same forward-looking window as the reservation shortcut',()=>{
 const h=render({quote:{minutes:180},messages:[{id:'a',role:'assistant',text:'Choose a time.',cards:['week'],claims:[],requested_date:'2026-10-24'}]});
 const calendar=find(h.tree,node=>node.props?.rolling===true);
 assert.ok(calendar);assert.equal(calendar.props.initialDate,'2026-10-24');
});

const weekCode=ts.transpileModule(readFileSync(new URL('../apps/frontend/components/week-calendar.tsx',import.meta.url),'utf8'),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},
}).outputText;
function calendar(preview){
 const start='2030-01-03',requests=[],effects=[],selected=[];let index=0;
 const days=Array.from({length:7},(_,i)=>{const date=new Date(start+'T12:00:00Z');date.setUTCDate(date.getUTCDate()+i);
  const day=date.toISOString().slice(0,10);return {date:day,weekday:'Day '+i,status:'available',occupied:[],
   slots:preview?[]:[{start:day+'T09:00:00Z',end:day+'T10:30:00Z',staff_ids:['ada']}]};});
 const data={week_start:start,timezone:'UTC',minutes:90,days,preview,can_previous:false,can_next:true};
 const deps={react:{useState:initial=>{const n=index++;return [n===1?data:n===2?start:n===5?false:typeof initial==='function'?initial():initial,noop];},useEffect:callback=>effects.push(callback)},
  'react/jsx-runtime':jsx,'@/lib/api':{api:async endpoint=>{requests.push(endpoint);return data;},clockReader:()=>()=> '09:00',duration:value=>value+' minutes'},
  './ui':{Badge:noop},'@/lib/timezone':{weekUtcOffset:()=>'+00:00'},'@/lib/calendar-metrics':{localDay:()=>start},
  '@/lib/availability-copy':{availabilityLabel:()=> 'Available',unavailableReason:()=> 'No times'},
  '@/lib/availability-window':windowing,
  '@/lib/availability-period':{periodSlots:slots=>slots}};
 const WeekCalendar=new Function('require','exports',weekCode+'\nreturn WeekCalendar;')(name=>{assert.ok(name in deps);return deps[name];},{});
 const tree=WeekCalendar({state:{workspace_id:'fixture',generation:1,revision:1,timezone:'UTC',quote:preview?null:{minutes:90},draft:{},scenario:{}},
  pending:false,rolling:true,initialDate:start,onSelect:value=>selected.push(value)});
 return {tree,requests,selected,runEffect:()=>effects[0]()};
}

test('incomplete rolling calendars fetch a seven-day preview without exposing exact selectable times',()=>{
 const h=calendar(true);const cleanup=h.runEffect();
 assert.deepEqual(h.requests,['availability?start=2030-01-03']);
 const days=find(h.tree,node=>node.props?.['aria-label']==='Seven days of appointments');
 assert.equal(days.props.children.length,7);
 assert.equal(find(h.tree,node=>node.props?.className==='time-options'),undefined);
 assert.deepEqual(h.selected,[]);cleanup();
});

test('complete rolling calendars expose the returned time through the existing selection callback',()=>{
 const h=calendar(false);const times=find(h.tree,node=>node.props?.className==='time-options');
 assert.ok(times);times.props.children[0].props.onClick();
 assert.deepEqual(h.selected,['2030-01-03T09:00:00Z']);
});
