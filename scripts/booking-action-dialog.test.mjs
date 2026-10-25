import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import ts from 'typescript';
import * as timezone from '../apps/frontend/lib/timezone.ts';
import {requestTone} from '../apps/frontend/lib/appointment-status.ts';

const require=createRequire(import.meta.url),jsx=require('react/jsx-runtime'),noop=()=>null;
const compile=file=>ts.transpileModule(readFileSync(new URL(file,import.meta.url),'utf8'),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},
}).outputText;
const api={};new Function('require','exports',compile('../apps/frontend/lib/api.ts'))(name=>{assert.equal(name,'./timezone');return timezone;},api);
function find(node,predicate){
 if(!node||typeof node!=='object')return;
 if(predicate(node))return node;
 for(const child of [node.props?.children].flat(Infinity)){const match=find(child,predicate);if(match)return match;}
}
function hooks(){
 let index=0,sets=0;const slots=[],effects=[];
 return {react:{useState:initial=>{const n=index++;slots[n]??={value:initial};return [slots[n].value,update=>{sets++;slots[n].value=typeof update==='function'?update(slots[n].value):update;}];},
  useRef:initial=>{const n=index++;slots[n]??={current:initial};return slots[n];},
  useEffect:(callback,next)=>{const n=index++;if(!slots[n]||next.some((value,j)=>!Object.is(value,slots[n].deps[j]))){const previous=slots[n];slots[n]={deps:next};effects.push(()=>{previous?.cleanup?.();slots[n].cleanup=callback();});}}},
  begin:()=>{index=0;},flush:()=>{for(const effect of effects.splice(0))effect();},sets:()=>sets,cleanup:()=>slots.forEach(slot=>slot?.cleanup?.())};
}
const record={id:'booking',revision:3,status:'confirmed',preferred_at:'2026-10-27T07:00:00Z',fields:{service:'deep',bedrooms:2},
 quote:{cents:12000,minutes:180,items:[{name:'Deep cleaning · 2 bedrooms'}]},booking:{staff_id:'ada'},crm_state:'not_connected'};
const dialogCode=compile('../apps/frontend/components/booking-action-dialog.tsx');
function dialog({action='complete',status='confirmed',pending=false}={}){
 const h=hooks();let tree,resolve,reject,calls=0,closed=0;
 const response=new Promise((yes,no)=>{resolve=yes;reject=no;});
 const opener={isConnected:true},fallbackFocus={isConnected:true};
 const deps={react:h.react,'react/jsx-runtime':jsx,'@/lib/api':api,'@/lib/timezone':timezone,
  './expanding-dialog':{ExpandingDialog:function Dialog(){}},'./ui':{Button:function Button(){}}};
 const Component=new Function('require','exports',dialogCode+'\nreturn BookingActionDialog;')(name=>{assert.ok(name in deps);return deps[name];},{});
 function render(){h.begin();tree=Component({record:{...record,status},zone:'Africa/Cairo',action,pending,opener,fallbackFocus,
  onClose:()=>closed++,onConfirm:()=>{calls++;return response;}});h.flush();}
 render();
 return {render,tree:()=>tree,button:text=>find(tree,node=>node.props?.children===text),calls:()=>calls,closed:()=>closed,opener,fallbackFocus,
  settle:async(success=true)=>{resolve(success?{state:{}}:null);for(let n=0;n<5;n++)await Promise.resolve();render();},
  reject:async()=>{reject(Error('Network'));for(let n=0;n<5;n++)await Promise.resolve();render();},cleanup:h.cleanup,sets:h.sets};
}

test('completion opens the shared branded dialog with the actual appointment and requires explicit confirmation',async()=>{
 const h=dialog();assert.equal(h.tree().props.label,'Mark this clean completed?');
 assert.equal(h.tree().props.opener,h.opener);assert.equal(h.tree().props.fallbackFocus,h.fallbackFocus);
 assert.ok(find(h.tree(),node=>node.props?.children==='Deep cleaning · 2 bedrooms'));
 assert.equal(h.calls(),0);h.button('Keep booking').props.onClick();assert.equal(h.closed(),1);assert.equal(h.calls(),0);
 h.cleanup();
 const confirmed=dialog();confirmed.button('Mark completed').props.onClick();confirmed.button('Mark completed').props.onClick();
 assert.equal(confirmed.calls(),1);confirmed.render();assert.equal(confirmed.button('Mark completed').props.busy,true);
 confirmed.tree().props.onClose();assert.equal(confirmed.closed(),0);
 await confirmed.settle();assert.equal(confirmed.closed(),1);
 confirmed.button('Mark completed').props.onClick();assert.equal(confirmed.calls(),1); // exiting dialogs cannot repeat the mutation
 confirmed.cleanup();
});

test('cancel and decline use distinct honest wording and never act on opening or dismissing',()=>{
 for(const [status,label,title,keep] of [['confirmed','Confirm cancellation','Cancel this booking?','Keep booking'],
  ['awaiting_review','Decline request','Decline this request?','Keep request']]){
  const h=dialog({action:'cancel',status});assert.equal(h.tree().props.label,title);assert.ok(h.button(label));
  h.button(keep).props.onClick();assert.equal(h.calls(),0);assert.equal(h.closed(),1);h.cleanup();
 }
});

test('failed/unknown responses stay in the dialog and cannot repeat an uncertain mutation',async()=>{
 for(const failure of ['null','throw']){
  const h=dialog();h.button('Mark completed').props.onClick();h.render();
  if(failure==='null')await h.settle(false);else await h.reject();
  assert.equal(h.closed(),0);assert.ok(find(h.tree(),node=>node.props?.role==='alert'));
  assert.equal(h.button('Mark completed').props.disabled,true);h.button('Mark completed').props.onClick();assert.equal(h.calls(),1);
  h.tree().props.onClose();assert.equal(h.closed(),1);h.cleanup();
 }
});

test('pending actions and late responses after unmount cannot dispatch or update the retired dialog',async()=>{
 const busy=dialog({pending:true});busy.button('Mark completed').props.onClick();assert.equal(busy.calls(),0);busy.cleanup();
 const h=dialog();h.button('Mark completed').props.onClick();h.render();h.cleanup();const sets=h.sets();
 await h.settle();assert.equal(h.closed(),0);assert.equal(h.sets(),sets);
});

const businessCode=compile('../apps/frontend/components/business-review.tsx');
function request(){
 const h=hooks(),calls=[];let current=record,tree;
 function Dialog(){}
 const deps={react:h.react,'react/jsx-runtime':jsx,'motion/react':{AnimatePresence:noop},'@/lib/api':api,'@/lib/timezone':timezone,
  './ui':{Badge:noop,Button:noop},'./week-calendar':{WeekCalendar:noop},'@/lib/appointment-status':{requestTone},
  './booking-action-dialog':{BookingActionDialog:Dialog}};
 const Component=new Function('require','exports','window',businessCode+'\nreturn RequestReview;')(
  name=>{assert.ok(name in deps);return deps[name];},{},{confirm:()=>assert.fail('Native confirmation is forbidden for booking actions')});
 function render(flush=true){h.begin();tree=Component({record:current,state:{timezone:'Africa/Cairo'},pending:false,
  onAction:async(...args)=>{calls.push(args);return {state:{}};}});tree.props.ref.current={isConnected:true};if(flush)h.flush();}
 render();return {calls,render,button:text=>find(tree,node=>node.props?.children===text),dialog:()=>find(tree,node=>node.type===Dialog),
  update:value=>{current=value;render(false);},flush:h.flush,cleanup:h.cleanup};
}

test('Business action buttons open an app dialog, and only its confirmation invokes the exact scoped command',async()=>{
 for(const [label,action] of [['Mark completed','complete'],['Cancel booking','cancel']]){
  const h=request(),opener={isConnected:true};h.button(label).props.onClick({currentTarget:opener});h.render();
  assert.equal(h.calls.length,0);assert.equal(h.dialog().props.opener,opener);
  h.dialog().props.onClose();h.render();assert.equal(h.dialog(),undefined);assert.equal(h.calls.length,0);
  h.button(label).props.onClick({currentTarget:opener});h.render();await h.dialog().props.onConfirm();
  assert.deepEqual(h.calls,[[record,action]]);h.cleanup();
 }
});

test('an open confirmation stays bound to the reviewed revision and closes on record changes',()=>{
 const h=request();h.button('Mark completed').props.onClick({currentTarget:{isConnected:true}});h.render();
 h.update({...record,revision:4,preferred_at:'2026-10-28T07:00:00Z'});
 assert.equal(h.dialog().props.record.revision,3);assert.equal(h.dialog().props.record.preferred_at,record.preferred_at);
 h.flush();h.render();assert.equal(h.dialog(),undefined);assert.equal(h.calls.length,0);h.cleanup();
});

test('the shared portal restores focus to the booking when the action button no longer exists',()=>{
 const effects=[],focus=[];const workspace={inert:false},main={inert:false};
 const fallback={isConnected:true,focus:options=>{assert.equal(workspace.inert,false);assert.deepEqual(options,{preventScroll:true});focus.push('record');}};
 const document={documentElement:{style:{overflow:'auto'},clientWidth:1000},body:{style:{overflow:'auto',paddingRight:''}},
  querySelectorAll:()=>[workspace,main],querySelector:()=>{throw Error('The record fallback should be used');}};
 const deps={react:{useRef:()=>({current:null}),useState:()=>[0,noop],useLayoutEffect:noop,useEffect:callback=>effects.push(callback)},
  'react/jsx-runtime':jsx,'react-dom':{createPortal:value=>value},'motion/react':{motion:{div:'div',section:'section'}},
  './use-dialog-focus':{useDialogFocus:noop}};
 const Component=new Function('require','exports','document','innerWidth','getComputedStyle',
  compile('../apps/frontend/components/expanding-dialog.tsx')+'\nreturn ExpandingDialog;')(
  name=>deps[name],{},document,1000,()=>({paddingRight:'0'}));
 Component({layoutId:'fixture',className:'booking-action-dialog',opener:{isConnected:false},fallbackFocus:fallback,onClose:noop});
 const cleanup=effects[0]();assert.equal(workspace.inert,true);cleanup();assert.deepEqual(focus,['record']);
 assert.equal(main.inert,false);assert.equal(document.body.style.overflow,'auto');
});

test('keyboard focus stays in a saving dialog when every action is disabled',()=>{
 const effects=[],listeners=new Map();let nodes=[],closed=0,prevented=0;
 const document={activeElement:null,addEventListener:(name,fn)=>listeners.set(name,fn),removeEventListener:name=>listeners.delete(name)};
 const panel={isConnected:true,closest:()=>null,querySelector:()=>nodes[0],querySelectorAll:()=>nodes,
  focus:options=>{assert.deepEqual(options,{preventScroll:true});document.activeElement=panel;}};
 const deps={react:{useRef:value=>({current:value}),useEffect:fn=>effects.push(fn)}};
 const hook=new Function('require','exports','document',compile('../apps/frontend/components/use-dialog-focus.ts')+'\nreturn useDialogFocus;')(
  name=>deps[name],{},document);
 hook({current:panel},()=>closed++);effects[0]();const cleanup=effects[1]();assert.equal(document.activeElement,panel);
 const key=(value,shiftKey=false)=>listeners.get('keydown')({key:value,shiftKey,defaultPrevented:false,preventDefault(){prevented++;},stopPropagation(){}});
 key('Tab');assert.equal(prevented,1);assert.equal(document.activeElement,panel);
 const first={focus(){document.activeElement=first;}},last={focus(){document.activeElement=last;}};nodes=[first,last];
 document.activeElement=last;key('Tab');assert.equal(document.activeElement,first);
 key('Tab',true);assert.equal(document.activeElement,last);
 key('Escape');assert.equal(closed,1);cleanup();assert.equal(listeners.size,0);
});
