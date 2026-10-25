import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import ts from 'typescript';
import * as navigation from '../apps/frontend/lib/workspace-navigation.ts';

const require=createRequire(import.meta.url),jsx=require('react/jsx-runtime'),noop=()=>null;
const compile=file=>ts.transpileModule(readFileSync(new URL('../apps/frontend/'+file,import.meta.url),'utf8'),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},
}).outputText;
function component(file,name,deps,globals={}){
 return new Function('require','exports',...Object.keys(globals),compile(file)+'\nreturn '+name+';')(
  name=>{assert.ok(name in deps,'Unexpected dependency '+name);return deps[name];},{},...Object.values(globals));
}
function find(node,predicate){
 if(!node||typeof node!=='object')return;
 if(predicate(node))return node;
 for(const child of [node.props?.children].flat(Infinity)){const match=find(child,predicate);if(match)return match;}
}
function hooks(){
 let index=0;const slots=[],effects=[];
 return {react:{useId:()=> 'confirmation-fixture',useTransition:()=>[false,fn=>fn()],useLayoutEffect:noop,
  useState:initial=>{const n=index++;slots[n]??={value:typeof initial==='function'?initial():initial};return [slots[n].value,value=>{slots[n].value=typeof value==='function'?value(slots[n].value):value;}];},
  useRef:initial=>{const n=index++;slots[n]??={current:initial};return slots[n];},
  useEffect:(callback,deps)=>{const n=index++;if(!slots[n]||deps.some((value,j)=>!Object.is(value,slots[n].deps[j]))){const previous=slots[n];slots[n]={deps};effects.push(()=>{previous?.cleanup?.();slots[n].cleanup=callback();});}}},
  begin:()=>{index=0;},flush:()=>{for(const effect of effects.splice(0))effect();},cleanup:()=>slots.forEach(slot=>slot?.cleanup?.())};
}
function resetControl({pending=false,mobile=false}={}){
 const h=hooks();let tree,modal,resolve,reject,calls=0,menuClosed=0;
 const response=new Promise((yes,no)=>{resolve=yes;reject=no;});
 const button={isConnected:true},menu={isConnected:true};
 const deps={react:h.react,'react/jsx-runtime':jsx,'motion/react':{AnimatePresence:noop},
  './ui':{Mark:noop,Button:noop},'./view-switch':{ViewSwitch:noop},'./expanding-dialog':{ExpandingDialog:noop}};
 const Confirmation=component('components/confirmation-dialog.tsx','ConfirmationDialog',deps);
 deps['./confirmation-dialog']={ConfirmationDialog:Confirmation};
 const Reset=component('components/workspace-controls.tsx','ResetDemo',deps,{window:{confirm:()=>assert.fail('Native confirmation is forbidden')}});
 function render(){h.begin();tree=Reset({disabled:pending,onReset:()=>{calls++;return response;},
  onDialogOpen:mobile?()=>{menuClosed++;return menu;}:undefined});
  const wrapper=find(tree,node=>node.type===Confirmation);modal=wrapper?Confirmation(wrapper.props):undefined;h.flush();}
 render();
 const open=()=>{find(tree,node=>node.props?.['aria-label']==='Reset demo').props.onClick({currentTarget:button});render();};
 return {open,render,modal:()=>modal,button:label=>find(modal,node=>node.props?.children===label),calls:()=>calls,
  menuClosed:()=>menuClosed,menu,opener:button,cleanup:h.cleanup,
  settle:async(ok=true)=>{resolve(ok);for(let n=0;n<6;n++)await Promise.resolve();render();},
  reject:async()=>{reject(Error('Unknown response'));for(let n=0;n<6;n++)await Promise.resolve();render();}};
}

test('Reset opens the shared app dialog; keep, close and backdrop/Escape dismissal never reset',()=>{
 for(const close of ['Keep this demo','Close','surface']){
  const h=resetControl();h.open();assert.equal(h.calls(),0);assert.equal(h.modal().props.label,'Start a fresh demo?');
  assert.equal(h.modal().props.opener,h.opener);
  if(close==='surface')h.modal().props.onClose();else h.button(close).props.onClick();
  h.render();assert.equal(h.modal(),undefined);assert.equal(h.calls(),0);h.cleanup();
 }
});

test('Reset waits for confirmation, blocks duplicate activation/dismissal and closes only after success',async()=>{
 const h=resetControl();h.open();h.button('Reset demo').props.onClick();h.button('Reset demo').props.onClick();
 assert.equal(h.calls(),1);h.render();assert.equal(h.button('Reset demo').props.busy,true);
 h.modal().props.onClose();h.render();assert.ok(h.modal());
 await h.settle();assert.equal(h.modal(),undefined);assert.equal(h.calls(),1);h.cleanup();
});

test('failed or unknown Reset stays in the app dialog without replaying the uncertain command',async()=>{
 for(const mode of ['null','throw']){
  const h=resetControl();h.open();h.button('Reset demo').props.onClick();h.render();
  if(mode==='null')await h.settle(false);else await h.reject();
  assert.ok(find(h.modal(),node=>node.props?.role==='alert'));assert.equal(h.button('Reset demo').props.disabled,true);
  h.button('Reset demo').props.onClick();assert.equal(h.calls(),1);
  h.button('Keep this demo').props.onClick();h.render();assert.equal(h.modal(),undefined);h.cleanup();
 }
});

test('Reset respects external pending state and can restore focus to the mobile menu opener',()=>{
 const pending=resetControl({pending:true});pending.open();pending.button('Reset demo').props.onClick();
 assert.equal(pending.calls(),0);pending.cleanup();
 const h=resetControl({mobile:true});h.open();assert.equal(h.menuClosed(),1);
 assert.equal(h.modal().props.opener,h.menu);assert.equal(h.calls(),0);h.cleanup();
});

function workspace({business=false,section='calendar'}={}){
 const h=hooks(),routes=[];let tree,resetCalls=0,resolve;
 const response=new Promise(yes=>{resolve=yes;});
 const guest={state:{workspace_id:'old-workspace',scenario:{week_start:'2026-10-26'},requests:[]},pending:false,error:null,
  initialize:async()=>null,retry:async()=>null,reset:()=>{resetCalls++;return response;}};
 function Footer(){}function Sidebar(){}function CRMControls(){}
 const router={replace:path=>routes.push(path)};
 const deps={react:h.react,'react/jsx-runtime':jsx,'motion/react':{motion:{div:'div'}},'next/navigation':{useRouter:()=>router},
  './demo-guest':{useDemoGuest:()=>guest},'@/lib/tour-preference':{tourWasSeen:()=>true},'@/lib/workspace-navigation':navigation,
  './workspace-controls':{CustomerFooter:Footer},'./business-sidebar':{BusinessSidebar:Sidebar},'./ui':{Button:noop,Spinner:noop}};
 for(const [file,name] of [['business-review','BusinessReview'],['business-overview','BusinessOverview'],['staff-calendar','StaffCalendar'],
  ['hero-collage','HeroCollage'],['documents','Documents'],['chat-workspace','ChatWorkspace'],['workspace-tour','WorkspaceTour']])deps['./'+file]={[name]:noop};
 deps['./crm-controls']={CRMControls};
 const window={location:{search:business?'?view=business&section='+section:''},addEventListener:noop,removeEventListener:noop};
 const Component=component('components/workspace-client.tsx','WorkspaceClient',deps,{window,document:{querySelector:()=>null}});
 function render(){h.begin();tree=Component();h.flush();}
 render();render();
 return {guest,routes,render,resetCalls:()=>resetCalls,control:()=>find(tree,node=>node.type===(business?Sidebar:Footer)),crm:()=>find(tree,node=>node.type===CRMControls),
  settle:async(ok=true)=>{if(ok)guest.state={...guest.state,workspace_id:'fresh-workspace'};resolve(ok?guest.state:null);for(let n=0;n<5;n++)await Promise.resolve();render();},cleanup:h.cleanup};
}

test('Business Connections enables the explicit uninstall control on the shared CRM panel',()=>{
 const h=workspace({business:true,section:'connections'});assert.equal(h.crm().props.manageConnection,true);assert.equal(h.crm().props.mutate,h.guest.mutate);h.cleanup();
});

test('Customer and Business Reset navigate to the choice step only after a confirmed fresh workspace',async()=>{
 for(const business of [false,true]){
  const h=workspace({business});const result=h.control().props.onReset();
  assert.equal(h.resetCalls(),1);assert.deepEqual(h.routes,[]);h.render();assert.deepEqual(h.routes,[]);
  await h.settle();assert.equal(await result,true);assert.deepEqual(h.routes,['/demo?step=connect']);
  h.render();assert.equal(h.routes.length,1);h.cleanup();
 }
});

test('failed reset stays in the workspace; verified recovery of an uncertain reset returns to choices',async()=>{
 const h=workspace();const result=h.control().props.onReset();await h.settle(false);
 assert.equal(await result,false);assert.deepEqual(h.routes,[]);
 h.guest.state={...h.guest.state,revision:2};h.render();assert.deepEqual(h.routes,[]);
 h.guest.state={...h.guest.state,workspace_id:'verified-after-retry'};h.render();
 assert.deepEqual(h.routes,['/demo?step=connect']);h.render();assert.equal(h.routes.length,1);h.cleanup();
 const ordinary=workspace();ordinary.guest.state={...ordinary.guest.state,workspace_id:'other-workspace'};ordinary.render();
 assert.deepEqual(ordinary.routes,[]);ordinary.cleanup();
});

test('workspace Reset controls are unavailable during another in-flight command',()=>{
 for(const business of [false,true]){
  const h=workspace({business});h.guest.pending=true;h.render();assert.equal(h.control().props.ready,false);
  assert.equal(h.resetCalls(),0);h.cleanup();
 }
});

test('the Reset destination mounts the existing animated connection setup, retaining ordinary welcome and OAuth entry',async()=>{
 function EntryClient(){}
 const Page=component('app/demo/page.tsx','Entry',{'react/jsx-runtime':jsx,'./welcome.css':{},'@/components/entry-client':{EntryClient}});
 const reset=await Page({searchParams:Promise.resolve({step:'connect'})});assert.equal(reset.props.resumeSetup,true);
 assert.equal((await Page({searchParams:Promise.resolve({})})).props.resumeSetup,false);
 assert.equal((await Page({searchParams:Promise.resolve({step:['connect']})})).props.resumeSetup,false);
 for(const crm of ['connected','unavailable','cancelled'])assert.equal((await Page({searchParams:Promise.resolve({crm})})).props.resumeSetup,true);
 const h=hooks();const deps={react:{...h.react,useCallback:value=>value},'react/jsx-runtime':jsx,'next/navigation':{useRouter:()=>({})},
  'motion/react':{AnimatePresence:noop,motion:{div:'div',main:'main'}},'./demo-guest':{useDemoGuest:()=>({state:{workspace_id:'fresh'},initialize:noop})},
  './ui':{AppHeader:noop,Badge:noop,Button:noop,Arrow:noop},'./crm-controls':{CRMControls:noop},'./guide-papers':{SampleGuideIntro:noop}};
 const Entry=component('components/entry-client.tsx','EntryClient',deps);h.begin();const tree=Entry(reset.props);
 assert.equal(find(tree,node=>node.key==='welcome'),undefined);
 const setup=find(tree,node=>node.key==='setup');assert.ok(setup);assert.equal(setup.type,'div');
 assert.deepEqual(setup.props.initial,{opacity:0,y:12});assert.deepEqual(setup.props.animate,{opacity:1,y:0});
 assert.equal(typeof setup.props.children.type,'function');h.cleanup();
});

test('mobile Business navigation closes before the app confirmation opens',()=>{
 const h=hooks();let tree,resets=0,opened=0,closed=0;
 function Reset(){}const menu={focus:noop};
 const dialog={open:false,showModal(){this.open=true;opened++;},close(){this.open=false;closed++;}};
 const deps={react:h.react,'react/jsx-runtime':jsx,'@/lib/workspace-navigation':navigation,
  './workspace-controls':{ResetDemo:Reset,PoweredBy:noop},'./view-switch':{ViewSwitch:noop}};
 const Component=component('components/business-sidebar.tsx','BusinessSidebar',deps,{window:{matchMedia:()=>({matches:true,addEventListener:noop,removeEventListener:noop})},requestAnimationFrame:noop,cancelAnimationFrame:noop});
 function render(){h.begin();tree=Component({businessName:'Juniper',page:'overview',collapsed:false,ready:true,onReset:async()=>{resets++;return true;},onNavigate:noop,onCollapse:noop,onPerspective:noop});
  const node=find(tree,value=>value.type==='dialog');if(node)node.props.ref.current=dialog;
  const button=find(tree,value=>value.props?.['aria-label']==='Open business navigation');if(button)button.props.ref.current=menu;h.flush();}
 render();render();find(tree,node=>node.props?.['aria-label']==='Open business navigation').props.onClick();render();
 assert.equal(opened,1);assert.equal(dialog.open,true);
 const reset=find(tree,node=>node.type===Reset);assert.equal(reset.props.onDialogOpen(),menu);render();
 assert.equal(dialog.open,false);assert.equal(closed,1);assert.equal(resets,0);h.cleanup();
});

function entrySetup({consented=false,status='ready',provider='hubspot',mode='connected',pending=false,routeThrows=false,reloadThrows=false}={}){
 const h=hooks(),routes=[],calls=[],reloads=[],timers=new Map();let tree,resolve,replacements=0,historyChanges=0,now=0,timerId=0;
 const response=new Promise(yes=>{resolve=yes;});
 const guest={state:{workspace_id:'workspace',crm_provider:provider,crm_mode:mode,connection:{id:'connection',provider,state:status,consented}},pending,error:null,
  mutate:(path,fields)=>{calls.push({path,fields});return response;}};
 function CRMControls(){}
 const router={push:path=>routes.push(path),replace:path=>{replacements++;if(routeThrows)throw Error('Router unavailable');routes.push(path);},prefetch:noop};
 const deps={react:{...h.react,useCallback:value=>value},'react/jsx-runtime':jsx,'next/navigation':{useRouter:()=>router},
  './demo-guest':{useDemoGuest:()=>guest},'./crm-controls':{CRMControls},'./ui':{AppHeader:noop,Badge:noop,Button:noop,Arrow:noop},
  'motion/react':{AnimatePresence:noop,motion:{div:'div',main:'main'}},'./guide-papers':{SampleGuideIntro:noop}};
 const Component=component('components/entry-client.tsx','EntrySetup',deps,{window:{location:{href:'http://localhost:45860/demo',replace:path=>{if(reloadThrows)throw Error('Navigation unavailable');reloads.push(path);}},history:{replaceState:()=>{historyChanges++;}},scrollTo:noop},
  setTimeout:(callback,delay)=>{const id=++timerId;timers.set(id,{callback,at:now+delay});return id;},clearTimeout:id=>timers.delete(id)});
 function render(){for(let n=0;n<2;n++){h.begin();tree=Component();h.flush();}}
 render();render();
 return {guest,routes,calls,reloads,render,replacements:()=>replacements,historyChanges:()=>historyChanges,timerCount:()=>timers.size,
  advance:ms=>{now+=ms;for(const [id,timer] of [...timers])if(timer.at<=now){timers.delete(id);timer.callback();}render();},crm:()=>find(tree,node=>node.type===CRMControls),
  skip:()=>find(tree,node=>node.props?.children==='Continue without HubSpot'&&typeof node.props.onClick==='function').props.onClick(),
  settle:async(ok=true)=>{resolve(ok?{state:{...guest.state,crm_mode:'skipped'}}:null);for(let n=0;n<8;n++)await Promise.resolve();render();},cleanup:h.cleanup};
}

test('HubSpot onboarding advances once only after the server confirms sharing for a ready real connection',()=>{
 const h=entrySetup();assert.deepEqual(h.routes,[]);assert.equal(h.crm().props.manageConnection,undefined);assert.equal(h.crm().props.onContinue,undefined);
 h.guest.pending=true;h.guest.state={...h.guest.state,connection:{...h.guest.state.connection,consented:true}};h.render();assert.deepEqual(h.routes,[]);
 h.guest.pending=false;h.render();assert.deepEqual(h.routes,['/demo/workspace']);assert.equal(h.replacements(),1);h.render();assert.equal(h.routes.length,1);
 h.guest.state={...h.guest.state,revision:2};h.render();assert.equal(h.routes.length,1);assert.equal(h.calls.length,0);h.cleanup();
});

test('a restored sharing-approved connection resumes chat; incomplete, fake or skipped connections do not advance',()=>{
 const restored=entrySetup({consented:true});assert.deepEqual(restored.routes,['/demo/workspace']);assert.equal(restored.calls.length,0);restored.cleanup();
 for(const options of [{status:'setup',consented:true},{consented:false},{provider:'fake',consented:true},{mode:'skipped',consented:true},{pending:true,consented:true}]){
  const h=entrySetup(options);assert.deepEqual(h.routes,[]);assert.equal(h.calls.length,0);h.cleanup();
 }
});

test('Continue without HubSpot still waits for its own successful skip and is independent of sharing',async()=>{
 for(const ok of [true,false]){
  const h=entrySetup();h.skip();h.render();assert.deepEqual(h.calls,[{path:'crm/skip',fields:{}}]);assert.deepEqual(h.routes,[]);
  await h.settle(ok);assert.deepEqual(h.routes,ok?['/demo/workspace']:[]);assert.equal(h.replacements(),0);h.cleanup();
 }
});

test('approved entry shows real navigation progress without a competing history restore',()=>{
 const h=entrySetup({consented:true});assert.deepEqual(h.routes,['/demo/workspace']);assert.equal(h.historyChanges(),0);
 assert.equal(h.crm().props.continuing,true);assert.equal(h.crm().props.navigationStalled,false);
 assert.equal(h.timerCount(),1);h.cleanup();assert.equal(h.timerCount(),0);h.advance(16_000);assert.deepEqual(h.reloads,[]);
});

test('a stale OAuth opening flag cannot block a server-confirmed sharing-approved workspace',()=>{
 const h=entrySetup();h.crm().props.onOpeningChange(true);h.render();assert.equal(h.crm().props.pending,true);assert.deepEqual(h.routes,[]);
 h.guest.state={...h.guest.state,connection:{...h.guest.state.connection,consented:true}};h.render();
 assert.deepEqual(h.routes,['/demo/workspace']);assert.equal(h.crm().props.continuing,true);h.cleanup();
});

test('a stalled client route gets one same-workspace document-navigation fallback, then a finite retry state',()=>{
 const h=entrySetup({consented:true});h.advance(7_999);assert.deepEqual(h.reloads,[]);assert.equal(h.crm().props.continuing,true);
 h.advance(1);assert.deepEqual(h.reloads,['/demo/workspace']);assert.equal(h.crm().props.continuing,true);assert.equal(h.calls.length,0);
 h.advance(8_000);assert.equal(h.crm().props.continuing,false);assert.equal(h.crm().props.navigationStalled,true);assert.equal(h.timerCount(),0);
 h.advance(60_000);assert.equal(h.reloads.length,1);assert.equal(h.routes.length,1);assert.equal(h.calls.length,0);h.cleanup();
});

test('route and document-navigation failures stop progress and retain recovery without repeating sharing',()=>{
 const route=entrySetup({consented:true,routeThrows:true});assert.equal(route.crm().props.navigationStalled,true);assert.equal(route.crm().props.continuing,false);
 assert.equal(route.timerCount(),0);assert.equal(route.calls.length,0);route.cleanup();
 const reload=entrySetup({consented:true,reloadThrows:true});reload.advance(8_000);
 assert.equal(reload.crm().props.navigationStalled,true);assert.equal(reload.crm().props.continuing,false);assert.equal(reload.timerCount(),0);assert.equal(reload.calls.length,0);reload.cleanup();
 for(const options of [{consented:false},{consented:true,pending:true},{consented:true,mode:'skipped'}]){
  const idle=entrySetup(options);idle.advance(16_000);assert.equal(idle.crm().props.continuing,false);assert.deepEqual(idle.routes,[]);assert.deepEqual(idle.reloads,[]);idle.cleanup();
 }
});
