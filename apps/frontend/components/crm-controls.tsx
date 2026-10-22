'use client';
import {useState} from 'react';
import type {SessionState,Mutation} from '@/lib/api';
import type {components} from '@/lib/generated/api';
import {Badge,Button} from './ui';
type Challenge=components['schemas']['OAuthChallenge'];
type Props={state:SessionState;pending:boolean;mutate:(path:string,fields:Record<string,unknown>)=>Promise<Mutation|SessionState|null>;onContinue?:()=>void};
const noticeKey=(state:SessionState)=>[state.workspace_id,state.revision,state.connection?.id,state.connection?.state].join(':');

export function CRMControls({state,pending,mutate,onContinue}:Props){
 return <CRMPanel key={state.workspace_id+':'+(state.connection?.id??'new')} state={state} pending={pending} mutate={mutate} onContinue={onContinue}/>;
}
function CRMPanel({state,pending,mutate,onContinue}:Props){
 const [challenge,setChallenge]=useState<Challenge|null>(null);const [notice,setNotice]=useState<{text:string;key:string}|null>(null);
 const [consent,setConsent]=useState(false);const [cleanup,setCleanup]=useState(true);const [uninstall,setUninstall]=useState(false);const [finishOpen,setFinishOpen]=useState(false);
 const [pipeline,setPipeline]=useState('');const [stage,setStage]=useState('');const [allowSchema,setAllowSchema]=useState(false);
 const connection=state.connection;const ready=connection?.state==='ready'&&state.crm_mode==='connected';
 const crmProvider=state.crm_provider??connection?.provider??'fake';
 const setup=connection?.state==='setup';const destinations=connection?.destinations??[];const selected=destinations.find(row=>row.id===pipeline);
 async function action(path:string,fields:Record<string,unknown>={}){const result=await mutate('crm/'+path,fields);if(result&&'crm_notice'in result)setNotice({text:result.crm_notice??'',key:noticeKey(result.state)});return result;}
 async function connect(){const result=await action('connect');if(result&&'oauth'in result&&result.oauth){
   if(result.oauth.authorize_url)window.location.assign(result.oauth.authorize_url);else setChallenge(result.oauth);
 }}
 async function callback(denied=false){if(!challenge)return;const result=await action('callback',{state:challenge.state,code:denied?'':'approved',denied});if(result)setChallenge(null);}
 return <section className="crm-controls" aria-label="HubSpot connection">
  <div className="section-heading"><div><Badge tone={ready?'green':'neutral'}>HubSpot{crmProvider==='fake'?' · simulated':crmProvider==='disabled'?' · unavailable':''}</Badge><h2>{ready?'Your CRM connection':setup?'Choose a booking destination':'Connect your HubSpot'}</h2><p>{ready||setup?connection?.label:'Share a reviewed fictional booking with your own account.'}</p></div></div>
  {notice?.text&&notice.key===noticeKey(state)&&<p className="crm-notice" role="status">{notice.text}</p>}
  {connection&&['finishing','finished','needs_attention'].includes(connection.state)&&<div className="crm-preview"><strong>Finish results{connection.provider==='fake'?' · simulated':''}</strong><p>Demo records: {connection.cleanup_state.replaceAll('_',' ')}<br/>Account uninstall: {connection.uninstall_state.replaceAll('_',' ')}</p>{connection.state==='needs_attention'&&<small>Some records may remain. Review your HubSpot account’s Connected Apps settings.</small>}</div>}
  {challenge&&<div className="simulated-consent"><h3>Simulate a HubSpot connection</h3><p>This local demo uses a simulated account. Nothing is sent to HubSpot.</p><p>A real connection would ask you to choose an account, approve access and confirm an unverified app.</p><div className="action-row"><Button disabled={pending} onClick={()=>void callback()}>Connect simulated account</Button><Button kind="quiet" disabled={pending} onClick={()=>void callback(true)}>Cancel connection</Button></div></div>}
  {!ready&&!setup&&!challenge&&<><Button disabled={pending||!state.crm_available||connection?.state==='finishing'} onClick={()=>void connect()}>{state.crm_available?'Connect your HubSpot':'Connection temporarily unavailable'}</Button><small>{connection?.state==='finishing'?'Finishing is still pending.':'You can use the whole booking flow without a CRM.'}</small></>}
  {setup&&connection&&<div className="crm-preview crm-destination"><p>Choose where this account will receive fictional bookings. Nothing has been shared.</p>
    <label>Pipeline<select value={pipeline} disabled={pending} onChange={event=>{setPipeline(event.target.value);setStage('');}}><option value="">Choose a pipeline</option>{destinations.map(row=><option key={row.id} value={row.id}>{row.label}</option>)}</select></label>
    <label>Stage<select value={stage} disabled={pending||!selected} onChange={event=>setStage(event.target.value)}><option value="">Choose an open stage</option>{selected?.stages.map(row=><option key={row.id} value={row.id}>{row.label}</option>)}</select></label>
    {state.crm_schema_setup_allowed?<label className="checkbox-label"><input type="checkbox" checked={allowSchema} disabled={pending} onChange={event=>setAllowSchema(event.target.checked)}/>Create Choreograph demo ID fields in contacts and deals if needed.</label>:<small>An account admin must prepare compatible demo ID fields before sharing.</small>}
    <Button disabled={pending||!pipeline||!stage} onClick={()=>void action('setup',{connection_id:connection.id,confirm:true,pipeline_id:pipeline,stage_id:stage,allow_schema:allowSchema})}>Verify destination</Button>
    <div className="action-row"><Button kind="quiet" disabled={pending} onClick={()=>void action('disconnect')}>Disconnect this workspace</Button><Button kind="quiet" disabled={pending} onClick={()=>setFinishOpen(value=>!value)}>Finish demo</Button></div>
  </div>}
  {ready&&<><div className="crm-preview"><strong>Fictional data only</strong><p>{connection.contact_name} · {connection.contact_email}</p>{connection.destination_label&&<p>{connection.destination_label}</p>}<small>The reviewed service, time, cleaner, quote total and booking status are shared with this account. No messages are sent.</small></div>
    <small>Demo records are removed when you reset or this two-hour workspace ends, while access remains available. The account installation stays unless you explicitly uninstall it.</small>
    {!connection.consented?<><label className="checkbox-label"><input type="checkbox" checked={consent} onChange={event=>setConsent(event.target.checked)} disabled={pending}/>Allow these fictional contact and booking records in this account.</label><Button disabled={!consent||pending} onClick={()=>void action('consent',{connection_id:connection.id,confirm:true})}>Allow demo records</Button></>:<p className="crm-sharing"><Badge tone="green">Sharing allowed</Badge> Only reviewed bookings are shared.</p>}
    {onContinue&&<Button kind="secondary" onClick={onContinue}>Continue to the front desk</Button>}
    <div className="action-row"><Button kind="quiet" disabled={pending} onClick={()=>void action('disconnect')}>Disconnect this workspace</Button><Button kind="quiet" disabled={pending} onClick={()=>setFinishOpen(value=>!value)}>Finish demo</Button></div>
  </>}
  {connection?.state==='detached'&&<Button kind="quiet" disabled={pending} onClick={()=>setFinishOpen(value=>!value)}>Finish demo</Button>}
  {connection&&finishOpen&&<div className="finish-options"><h3>Finish the CRM demo</h3><p>Choose what to remove before ending access.</p><label className="checkbox-label"><input type="checkbox" checked={cleanup} onChange={event=>setCleanup(event.target.checked)}/>Remove only this demo’s app-created contact and booking records.</label><label className="checkbox-label"><input type="checkbox" checked={uninstall} disabled={!connection.can_uninstall} onChange={event=>setUninstall(event.target.checked)}/>Uninstall the app from this HubSpot account.</label><small>{connection.can_uninstall?'HubSpot emails account admins after a real uninstall. Uninstall and record cleanup are separate actions.':'Another active demo uses this account. You can disconnect this workspace; account-wide uninstall is unavailable.'}</small><Button disabled={pending} onClick={()=>void action('finish',{connection_id:connection.id,confirm:true,cleanup,uninstall}).then(result=>{if(result)setFinishOpen(false);})}>Finish with these choices</Button></div>}
 </section>;
}
