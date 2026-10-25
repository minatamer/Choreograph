import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import ts from 'typescript';

const require=createRequire(import.meta.url),jsx=require('react/jsx-runtime'),noop=()=>null;
function compile(file,name,deps){
 const source=ts.transpileModule(readFileSync(new URL('../apps/frontend/components/'+file,import.meta.url),'utf8'),{
  compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},
 }).outputText;
 return new Function('require','exports',source+'\nreturn '+name+';')(key=>{assert.ok(key in deps,'Unexpected dependency '+key);return deps[key];},{});
}
function find(node,predicate){
 if(!node||typeof node!=='object')return;
 if(predicate(node))return node;
 for(const child of [node.props?.children].flat(Infinity)){const match=find(child,predicate);if(match)return match;}
}
function hooks(){
 let index=0;const slots=[],effects=[];
 return {react:{useId:()=> 'uninstall-fixture',
  useState:initial=>{const n=index++;slots[n]??={value:initial};return [slots[n].value,value=>{slots[n].value=typeof value==='function'?value(slots[n].value):value;}];},
  useRef:initial=>{const n=index++;slots[n]??={current:initial};return slots[n];},
  useEffect:(callback,deps)=>{const n=index++;if(!slots[n]||deps.some((value,j)=>!Object.is(value,slots[n].deps[j]))){const previous=slots[n];slots[n]={deps};effects.push(()=>{previous?.cleanup?.();slots[n].cleanup=callback();});}}},
  begin:()=>{index=0;},flush:()=>{for(const effect of effects.splice(0))effect();},cleanup:()=>slots.forEach(slot=>slot?.cleanup?.())};
}
function fixture({manageConnection=true,provider='hubspot',status='ready',canUninstall=true,pending=false}={}){
 const panelHooks=hooks(),dialogHooks=hooks(),calls=[];let panel,dialog,resolve,reject;
 const response=new Promise((yes,no)=>{resolve=yes;reject=no;});
 const deps={react:dialogHooks.react,'react/jsx-runtime':jsx,'./ui':{Button:noop,Badge:noop,Spinner:function Spinner(){}},'./expanding-dialog':{ExpandingDialog:noop}};
 const Confirmation=compile('confirmation-dialog.tsx','ConfirmationDialog',deps);
 const Panel=compile('crm-controls.tsx','CRMPanel',{...deps,react:panelHooks.react,'next/image':{default:noop},'motion/react':{AnimatePresence:noop},'./confirmation-dialog':{ConfirmationDialog:Confirmation}});
 const props={state:{workspace_id:'workspace',revision:4,crm_provider:provider,crm_available:true,crm_mode:'connected',crm_schema_setup_allowed:true,
   connection:status?{id:'reviewed-connection',provider,label:'HubSpot account 456',state:status,can_uninstall:canUninstall,consented:true,
    destinations:[{id:'pipeline',label:'Sales Pipeline',stages:[{id:'inbound',label:'Inbound Interest'}]}],cleanup_state:'not_requested',uninstall_state:'not_requested'}:null},
  pending,opening:false,setOpening:noop,manageConnection,mutate:(path,fields)=>{calls.push({path,fields});return response;}};
 const opener={isConnected:true};
 function render(){
  for(let n=0;n<2;n++){panelHooks.begin();panel=Panel(props);panelHooks.flush();}
  const wrapper=find(panel,node=>node.type===Confirmation);
  if(wrapper){dialogHooks.begin();dialog=Confirmation(wrapper.props);dialogHooks.flush();}
  else{if(dialog)dialogHooks.cleanup();dialog=undefined;}
 }
 render();
 const button=(root,label)=>find(root,node=>node.props?.children===label);
 return {props,calls,render,panel:()=>panel,dialog:()=>dialog,opener,panelButton:label=>button(panel,label),
  select:(placeholder,value)=>{find(panel,node=>node.type==='select'&&node.props.children[0].props.children===placeholder).props.onChange({target:{value}});render();},
  uninstall:()=>button(panel,'Uninstall HubSpot'),button:label=>button(dialog,label),
  open:()=>{button(panel,'Uninstall HubSpot').props.onClick({currentTarget:opener});render();},
  settle:async(result)=>{resolve(result);for(let n=0;n<8;n++)await Promise.resolve();render();},
  reject:async()=>{reject(Error('Unknown response'));for(let n=0;n<8;n++)await Promise.resolve();render();},
  cleanup:()=>{panelHooks.cleanup();dialogHooks.cleanup();}};
}

test('Connections exposes uninstall for ready, setup and detached real accounts only',()=>{
 for(const status of ['ready','setup','detached']){const h=fixture({status});assert.equal(h.uninstall().props.disabled,false);assert.equal(h.calls.length,0);h.cleanup();}
 for(const options of [{manageConnection:false},{provider:'fake'},{status:null},{status:'finishing'},{status:'finished'},{status:'needs_attention'}]){
  const h=fixture(options);assert.equal(h.uninstall(),undefined);assert.equal(h.calls.length,0);h.cleanup();
 }
});

test('uninstall opens the shared designed dialog with the reviewed account; dismissal makes no command',()=>{
 for(const close of ['Keep connected','Close','surface']){
  const h=fixture();h.open();assert.equal(h.calls.length,0);assert.equal(h.dialog().props.opener,h.opener);
  assert.equal(h.dialog().props.label,'Uninstall Choreograph from HubSpot?');
  assert.ok(find(h.dialog(),node=>node.type==='strong'&&node.props.children==='HubSpot account 456'));
  if(close==='surface')h.dialog().props.onClose();else h.button(close).props.onClick();
  h.render();assert.equal(h.dialog(),undefined);assert.equal(h.calls.length,0);h.cleanup();
 }
});

test('confirmed uninstall queues the existing command with chosen cleanup, once, and waits for acknowledgement',async()=>{
 for(const cleanup of [true,false]){
  const h=fixture();h.open();const checkbox=find(h.dialog(),node=>node.type==='input');assert.equal(checkbox.props.checked,true);
  checkbox.props.onChange({target:{checked:cleanup}});h.render();
  h.button('Uninstall HubSpot').props.onClick();h.button('Uninstall HubSpot').props.onClick();h.render();
  assert.deepEqual(h.calls,[{path:'crm/finish',fields:{connection_id:'reviewed-connection',confirm:true,cleanup,uninstall:true}}]);
  assert.equal(h.button('Uninstall HubSpot').props.busy,true);h.dialog().props.onClose();h.render();assert.ok(h.dialog());
  await h.settle({state:{...h.props.state,connection:{...h.props.state.connection,state:'finishing'}},crm_notice:'Pending'});
  assert.equal(h.dialog(),undefined);assert.equal(h.calls.length,1);h.cleanup();
 }
});

test('shared-account and in-flight guards prevent uninstall; a changed connection invalidates the review',()=>{
 for(const options of [{canUninstall:false},{pending:true}]){
  const h=fixture(options);assert.equal(h.uninstall().props.disabled,true);h.open();assert.equal(h.dialog(),undefined);assert.equal(h.calls.length,0);h.cleanup();
 }
 for(const changes of [{can_uninstall:false},{id:'another-connection'},{state:'finishing'}]){
  const h=fixture();h.open();Object.assign(h.props.state.connection,changes);h.render();assert.equal(h.dialog(),undefined);assert.equal(h.calls.length,0);h.cleanup();
 }
});

test('unknown or failed uninstall acknowledgement stays in the dialog and cannot replay',async()=>{
 for(const failure of ['null','throw']){
  const h=fixture();h.open();h.button('Uninstall HubSpot').props.onClick();h.render();
  if(failure==='null')await h.settle(null);else await h.reject();
  assert.ok(find(h.dialog(),node=>node.props?.role==='alert'));assert.equal(h.button('Uninstall HubSpot').props.disabled,true);
  h.button('Uninstall HubSpot').props.onClick();assert.equal(h.calls.length,1);
  h.button('Close').props.onClick();h.render();assert.equal(h.dialog(),undefined);h.cleanup();
 }
});

test('pending and completed results remain separate from uninstall request acceptance',()=>{
 const h=fixture({status:'finishing'});h.props.state.connection.cleanup_state='removed';h.props.state.connection.uninstall_state='not_requested';h.render();
 const result=find(h.panel(),node=>node.type==='p'&&Array.isArray(node.props.children)&&node.props.children[0]==='Demo records: ');
 assert.ok(result);assert.ok(result.props.children.includes('removed'));assert.ok(result.props.children.includes('not requested'));
 assert.equal(h.uninstall(),undefined);assert.equal(h.calls.length,0);h.cleanup();
});

test('destination verification shows progress immediately and blocks duplicate submissions',async()=>{
 const h=fixture({status:'setup'});h.select('Choose a pipeline','pipeline');h.select('Choose an open stage','inbound');
 find(h.panel(),node=>node.type==='input'&&node.props.type==='checkbox').props.onChange({target:{checked:true}});h.render();
 h.panelButton('Verify destination').props.onClick();h.panelButton('Verify destination').props.onClick();h.render();
 assert.equal(h.panelButton('Verifying destination…').props.busy,true);
 assert.deepEqual(h.calls,[{path:'crm/setup',fields:{connection_id:'reviewed-connection',confirm:true,pipeline_id:'pipeline',stage_id:'inbound',allow_schema:true}}]);
 await h.settle(null);assert.equal(h.panelButton('Verify destination').props.busy,false);h.cleanup();
});

test('rejected setup displays the server explanation directly beneath Verify, retaining the selected destination',async()=>{
 const h=fixture({status:'setup'});h.select('Choose a pipeline','pipeline');h.select('Choose an open stage','inbound');h.panelButton('Verify destination').props.onClick();h.render();
 const state={...h.props.state,revision:5};h.props.state=state;
 await h.settle({state,crm_notice:'HubSpot’s account currency could not be verified. Try again shortly. No records were shared.'});
 const form=find(h.panel(),node=>node.props?.className==='crm-preview crm-destination');
 const feedback=find(form,node=>node.props?.className==='crm-setup-feedback');assert.equal(feedback.props.role,'alert');
 assert.equal(find(feedback,node=>node.type==='strong').props.children,'Couldn’t verify destination');
 assert.match(find(feedback,node=>node.type==='p').props.children,/currency could not be verified/);
 const items=form.props.children.flat(Infinity);assert.ok(items.indexOf(feedback)>items.indexOf(h.panelButton('Verify destination')));
 assert.ok(find(form,node=>node.type==='select'&&node.props.value==='pipeline'));
 assert.ok(find(form,node=>node.type==='select'&&node.props.value==='inbound'));h.cleanup();
});

test('successful setup reveals sharing review without a way to enter the HubSpot path before consent',async()=>{
 const h=fixture({status:'setup',manageConnection:false});h.props.state.connection.consented=false;
 h.select('Choose a pipeline','pipeline');h.select('Choose an open stage','inbound');h.panelButton('Verify destination').props.onClick();h.render();
 const state={...h.props.state,revision:5,connection:{...h.props.state.connection,state:'ready'}};h.props.state=state;
 await h.settle({state,crm_notice:'Destination verified. Review the fictional data before allowing sharing.'});
 assert.equal(h.panelButton('Verify destination'),undefined);assert.equal(h.panelButton('Continue to the front desk'),undefined);
 assert.equal(h.panelButton('Allow sharing and continue').props.disabled,true);assert.equal(h.calls.length,1);h.cleanup();
});

test('connection management stays on the dashboard and is absent throughout onboarding',()=>{
 for(const status of ['setup','ready','detached']){
  const entry=fixture({status,manageConnection:false});
  for(const label of ['Disconnect this workspace','Finish demo','Uninstall HubSpot','Continue to the front desk'])assert.equal(entry.panelButton(label),undefined);
  entry.cleanup();
  const dashboard=fixture({status});assert.ok(dashboard.panelButton('Uninstall HubSpot'));
  for(const label of ['Disconnect this workspace','Finish demo','Finish with these choices'])assert.equal(dashboard.panelButton(label),undefined);dashboard.cleanup();
 }
});

test('the full data preview remains before sharing, with compact destination status after approval',()=>{
 const h=fixture();h.props.state.connection.contact_name='Demo Guest';h.props.state.connection.contact_email='';h.props.state.connection.destination_label='Sales Pipeline';
 h.render();assert.equal(find(h.panel(),node=>node.type==='strong'&&node.props.children==='Records to share'),undefined);
 h.props.state.connection.consented=false;h.render();
 assert.ok(find(h.panel(),node=>node.type==='strong'&&node.props.children==='Records to share'));
 assert.ok(find(h.panel(),node=>node.type==='p'&&Array.isArray(node.props.children)&&node.props.children.includes('No email address')));h.cleanup();
});

test('sharing requires its checkbox, sends once and waits for the server before showing success',async()=>{
 const h=fixture({manageConnection:false});h.props.state.connection.consented=false;h.render();
 h.panelButton('Allow sharing and continue').props.onClick();assert.equal(h.calls.length,0);
 find(h.panel(),node=>node.type==='input'&&node.props.type==='checkbox').props.onChange({target:{checked:true}});h.render();
 h.panelButton('Allow sharing and continue').props.onClick();h.panelButton('Allow sharing and continue').props.onClick();h.render();
 assert.equal(h.panelButton('Allow sharing and continue').props.busy,true);
 assert.deepEqual(h.calls,[{path:'crm/consent',fields:{connection_id:'reviewed-connection',confirm:true}}]);
 assert.equal(find(h.panel(),node=>node.props?.children==='Opening the front desk…'),undefined);
 const state={...h.props.state,revision:5,connection:{...h.props.state.connection,consented:true}};h.props.state=state;
 await h.settle({state,crm_notice:'Sharing allowed.'});
 assert.equal(h.panelButton('Allow sharing and continue'),undefined);assert.equal(find(h.panel(),node=>node.props?.className==='crm-entry-progress'),undefined);
 h.props.continuing=true;h.render();assert.ok(find(h.panel(),node=>node.props?.className==='crm-entry-progress'));h.cleanup();
});

test('the entry spinner reflects an active route attempt and stalled navigation exposes a real same-origin link',()=>{
 const h=fixture({manageConnection:false});assert.equal(find(h.panel(),node=>node.props?.className==='crm-entry-progress'),undefined);
 h.props.continuing=true;h.render();
 const progress=find(h.panel(),node=>node.props?.className==='crm-entry-progress');assert.equal(progress.props.role,'status');assert.equal(progress.props['aria-busy'],'true');
 assert.ok(find(progress,node=>node.type?.name==='Spinner'));
 h.props.continuing=false;h.props.navigationStalled=true;h.render();assert.equal(find(h.panel(),node=>node.props?.className==='crm-entry-progress'),undefined);
 const retry=find(h.panel(),node=>node.type==='a'&&node.props.href==='/demo/workspace');assert.equal(retry.props.children,'Open the front desk');assert.equal(h.calls.length,0);h.cleanup();
 const dashboard=fixture();dashboard.props.continuing=true;dashboard.props.navigationStalled=true;dashboard.render();
 assert.equal(find(dashboard.panel(),node=>node.props?.className==='crm-entry-progress'),undefined);assert.equal(find(dashboard.panel(),node=>node.type==='a'&&node.props.href==='/demo/workspace'),undefined);dashboard.cleanup();
});

test('failed or unknown sharing stays on the consent step with an inline error',async()=>{
 for(const failure of ['null','throw']){
  const h=fixture({manageConnection:false});h.props.state.connection.consented=false;h.render();
  find(h.panel(),node=>node.type==='input'&&node.props.type==='checkbox').props.onChange({target:{checked:true}});h.render();
  h.panelButton('Allow sharing and continue').props.onClick();h.render();
  if(failure==='null')await h.settle(null);else await h.reject();
  assert.ok(find(h.panel(),node=>node.props?.className==='crm-setup-feedback'&&node.props.role==='alert'));
  assert.equal(h.panelButton('Allow sharing and continue').props.disabled,false);
  assert.equal(find(h.panel(),node=>node.props?.children==='Opening the front desk…'),undefined);assert.equal(h.calls.length,1);h.cleanup();
 }
});

test('failed or interrupted setup still shows a local error and re-enables verification',async()=>{
 for(const failure of ['null','throw']){
  const h=fixture({status:'setup'});h.select('Choose a pipeline','pipeline');h.select('Choose an open stage','inbound');h.panelButton('Verify destination').props.onClick();h.render();
  if(failure==='null')await h.settle(null);else await h.reject();
  assert.ok(find(h.panel(),node=>node.props?.className==='crm-setup-feedback'&&node.props.role==='alert'));
  assert.equal(h.panelButton('Verify destination').props.disabled,false);assert.equal(h.calls.length,1);h.cleanup();
 }
});
