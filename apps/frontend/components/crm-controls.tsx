'use client';
import {useEffect,useState} from 'react';
import Image from 'next/image';
import type {SessionState,Mutation} from '@/lib/api';
import {Badge,Button} from './ui';
type Props={state:SessionState;pending:boolean;mutate:(path:string,fields:Record<string,unknown>)=>Promise<Mutation|SessionState|null>;onContinue?:()=>void;continuing?:boolean;onOpeningChange?:(value:boolean)=>void};
const noticeKey=(state:SessionState)=>[state.workspace_id,state.revision,state.connection?.id,state.connection?.state].join(':');

export function CRMControls(props:Props){
 const [opening,setOpening]=useState(false);
 useEffect(()=>{const returned=()=>setOpening(false);window.addEventListener('pageshow',returned);return()=>window.removeEventListener('pageshow',returned);},[]);
 useEffect(()=>{props.onOpeningChange?.(opening);},[opening,props.onOpeningChange]);
 return <CRMPanel key={props.state.workspace_id+':'+(props.state.connection?.id??'new')} {...props} opening={opening} setOpening={setOpening}/>;
}
function CRMPanel({state,pending:operationPending,mutate,onContinue,continuing=false,opening,setOpening}:Props&{opening:boolean;setOpening:(value:boolean)=>void}){
 const pending=operationPending||opening||continuing;
 const [notice,setNotice]=useState<{text:string;key:string}|null>(null);
 const [consent,setConsent]=useState(false);const [cleanup,setCleanup]=useState(true);const [uninstall,setUninstall]=useState(false);const [finishOpen,setFinishOpen]=useState(false);
 const [pipeline,setPipeline]=useState('');const [stage,setStage]=useState('');const [allowSchema,setAllowSchema]=useState(false);
 const connection=state.crm_provider==='hubspot'&&state.connection?.provider==='hubspot'?state.connection:null;
 const ready=connection?.state==='ready'&&state.crm_mode==='connected';
 const canConnect=state.crm_provider==='hubspot'&&state.crm_available;
 const setup=connection?.state==='setup';const destinations=connection?.destinations??[];const selected=destinations.find(row=>row.id===pipeline);
 async function action(path:string,fields:Record<string,unknown>={}){const result=await mutate('crm/'+path,fields);if(result&&'crm_notice'in result)setNotice({text:result.crm_notice??'',key:noticeKey(result.state)});return result;}
 async function connect(){
   if(pending)return;
   setOpening(true);let leaving=false;
   try{
     const result=await action('connect');
     if(result&&'oauth'in result&&result.oauth){
       if(!result.oauth.simulated&&result.oauth.authorize_url){window.location.assign(result.oauth.authorize_url);leaving=true;}
       else setNotice({text:'HubSpot could not be opened. Please try again or continue without HubSpot.',key:noticeKey(result.state)});
     }
   }catch{setNotice({text:'HubSpot could not be opened. Please try again or continue without HubSpot.',key:noticeKey(state)});}
   finally{if(!leaving)setOpening(false);}
 }
 return <section className="crm-controls" aria-label="HubSpot connection" data-tour="hubspot">
  <div className="section-heading"><div><div className="crm-brand"><Image src="/brand/hubspot-logo.svg" alt="HubSpot" width={128} height={36}/><Badge tone={ready?'green':'neutral'}>{ready?'Connected':canConnect?'Optional':'Unavailable'}</Badge></div><h2>{ready?'Your HubSpot connection':setup?'Choose a booking destination':'Continue with HubSpot'}</h2><p>{ready||setup?connection?.label:'Save approved bookings in your own HubSpot account.'}</p></div></div>
  {notice?.text&&notice.key===noticeKey(state)&&<p className="crm-notice" role="status">{notice.text}</p>}
  {connection&&['finishing','finished','needs_attention'].includes(connection.state)&&<div className="crm-preview"><strong>Finish results</strong><p>App-created records: {connection.cleanup_state.replaceAll('_',' ')}<br/>Account uninstall: {connection.uninstall_state.replaceAll('_',' ')}</p>{connection.state==='needs_attention'&&<small>Some records may remain. Review your HubSpot account’s Connected Apps settings.</small>}</div>}
  {!ready&&!setup&&<><Button busy={opening} disabled={pending||!canConnect||connection?.state==='finishing'} onClick={()=>void connect()}>Continue with HubSpot</Button><small>{connection?.state==='finishing'?'Finishing is still pending.':canConnect?'Choose your account and approve access on HubSpot.':state.crm_provider!=='hubspot'?'HubSpot connections haven’t been set up for this demo yet. You can continue without HubSpot.':'HubSpot connection capacity is temporarily unavailable. You can continue without HubSpot.'}</small></>}
  {setup&&connection&&<div className="crm-preview crm-destination"><p>Choose where bookings are saved. Nothing has been shared. Juniper’s sample quotes use USD, so this account’s company currency must be USD.</p>
    <label>Pipeline<select value={pipeline} disabled={pending} onChange={event=>{setPipeline(event.target.value);setStage('');}}><option value="">Choose a pipeline</option>{destinations.map(row=><option key={row.id} value={row.id}>{row.label}</option>)}</select></label>
    <label>Stage<select value={stage} disabled={pending||!selected} onChange={event=>setStage(event.target.value)}><option value="">Choose an open stage</option>{selected?.stages.map(row=><option key={row.id} value={row.id}>{row.label}</option>)}</select></label>
    {state.crm_schema_setup_allowed?<label className="checkbox-label"><input type="checkbox" checked={allowSchema} disabled={pending} onChange={event=>setAllowSchema(event.target.checked)}/>Create Choreograph ID fields in contacts and deals if needed.</label>:<small>An account admin must prepare compatible Choreograph ID fields before sharing.</small>}
    <Button disabled={pending||!pipeline||!stage} onClick={()=>void action('setup',{connection_id:connection.id,confirm:true,pipeline_id:pipeline,stage_id:stage,allow_schema:allowSchema})}>Verify destination</Button>
    <div className="action-row"><Button kind="quiet" disabled={pending} onClick={()=>void action('disconnect')}>Disconnect this workspace</Button><Button kind="quiet" disabled={pending} onClick={()=>setFinishOpen(value=>!value)}>Finish demo</Button></div>
  </div>}
  {ready&&<><div className="crm-preview"><strong>Records to share</strong><p>{connection.contact_name} · {connection.contact_email}</p>{connection.destination_label&&<p>{connection.destination_label}</p>}<small>The reviewed service, time, cleaner, quote total and booking status are shared with this account. No messages are sent.</small></div>
    <small>App-created records are removed when you reset or this two-hour workspace ends, while access remains available. The account installation stays unless you explicitly uninstall it.</small>
    {!connection.consented?<><label className="checkbox-label"><input type="checkbox" checked={consent} onChange={event=>setConsent(event.target.checked)} disabled={pending}/>Allow Juniper’s sample contact and reviewed booking records, including existing bookings, in this account.</label><Button disabled={!consent||pending} onClick={()=>void action('consent',{connection_id:connection.id,confirm:true})}>Allow sharing</Button></>:<p className="crm-sharing"><Badge tone="green">Sharing allowed</Badge> Only reviewed bookings are shared.</p>}
    {onContinue&&<Button kind="secondary" disabled={pending} busy={continuing} onClick={onContinue}>Continue to the front desk</Button>}
    <div className="action-row"><Button kind="quiet" disabled={pending} onClick={()=>void action('disconnect')}>Disconnect this workspace</Button><Button kind="quiet" disabled={pending} onClick={()=>setFinishOpen(value=>!value)}>Finish demo</Button></div>
  </>}
  {connection?.state==='detached'&&<Button kind="quiet" disabled={pending} onClick={()=>setFinishOpen(value=>!value)}>Finish demo</Button>}
  {connection&&finishOpen&&<div className="finish-options"><h3>Finish your connection</h3><p>Choose what to remove before ending access.</p><label className="checkbox-label"><input type="checkbox" checked={cleanup} onChange={event=>setCleanup(event.target.checked)}/>Remove only this workspace’s app-created contact and booking records.</label><label className="checkbox-label"><input type="checkbox" checked={uninstall} disabled={!connection.can_uninstall} onChange={event=>setUninstall(event.target.checked)}/>Uninstall the app from this HubSpot account.</label><small>{connection.can_uninstall?'HubSpot emails account admins after a real uninstall. Uninstall and record cleanup are separate actions.':'Another active workspace uses this account. You can disconnect this workspace; account-wide uninstall is unavailable.'}</small><Button disabled={pending} onClick={()=>void action('finish',{connection_id:connection.id,confirm:true,cleanup,uninstall}).then(result=>{if(result)setFinishOpen(false);})}>Finish with these choices</Button></div>}
  <small className="crm-exit-note">Disconnect anytime. Uninstall in HubSpot’s Connected Apps; admins are notified.</small>
 </section>;
}
