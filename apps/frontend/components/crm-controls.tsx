'use client';
import {useEffect,useRef,useState,type ReactNode} from 'react';
import Image from 'next/image';
import {AnimatePresence} from 'motion/react';
import type {SessionState,Mutation} from '@/lib/api';
import {Badge,Button,Spinner} from './ui';
import {ConfirmationDialog} from './confirmation-dialog';
type Props={state:SessionState;pending:boolean;mutate:(path:string,fields:Record<string,unknown>)=>Promise<Mutation|SessionState|null>;continuing?:boolean;navigationStalled?:boolean;onOpeningChange?:(value:boolean)=>void;feedback?:ReactNode;manageConnection?:boolean};
const noticeKey=(state:SessionState)=>[state.workspace_id,state.revision,state.connection?.id,state.connection?.state].join(':');

export function CRMControls(props:Props){
 const [opening,setOpening]=useState(false);
 useEffect(()=>{const returned=()=>setOpening(false);window.addEventListener('pageshow',returned);return()=>window.removeEventListener('pageshow',returned);},[]);
 useEffect(()=>{props.onOpeningChange?.(opening);},[opening,props.onOpeningChange]);
 return <CRMPanel key={props.state.workspace_id+':'+(props.state.connection?.id??'new')} {...props} opening={opening} setOpening={setOpening}/>;
}
function CRMPanel({state,pending:operationPending,mutate,continuing=false,navigationStalled=false,opening,setOpening,feedback,manageConnection=false}:Props&{opening:boolean;setOpening:(value:boolean)=>void}){
 const [verifying,setVerifying]=useState(false);const verifyLock=useRef(false);
 const [sharing,setSharing]=useState(false);const shareLock=useRef(false);
 const pending=operationPending||opening||continuing||verifying||sharing;
 const [notice,setNotice]=useState<{text:string;key:string;action?:string;error?:boolean}|null>(null);
 const [consent,setConsent]=useState(false);
 const [pipeline,setPipeline]=useState('');const [stage,setStage]=useState('');const [allowSchema,setAllowSchema]=useState(false);
 const [uninstallReview,setUninstallReview]=useState<{id:string;label:string;opener:HTMLElement}|null>(null);
 const [uninstallCleanup,setUninstallCleanup]=useState(true);
 const connection=state.crm_provider==='hubspot'&&state.connection?.provider==='hubspot'?state.connection:null;
 const canFinish=Boolean(connection&&['ready','setup','detached'].includes(connection.state));
 useEffect(()=>{if(uninstallReview&&(!manageConnection||!canFinish||!connection?.can_uninstall||connection.id!==uninstallReview.id))setUninstallReview(null);},[manageConnection,canFinish,connection?.can_uninstall,connection?.id,uninstallReview]);
 const ready=connection?.state==='ready'&&state.crm_mode==='connected';
 const canConnect=state.crm_provider==='hubspot'&&state.crm_available;
 const setup=connection?.state==='setup';const destinations=connection?.destinations??[];const selected=destinations.find(row=>row.id===pipeline);
 const choosing=!ready&&!setup;
 const currentNotice=notice?.key===noticeKey(state)?notice:null;
 const setupNotice=setup&&currentNotice?.action==='setup'?currentNotice:null;
 const sharingNotice=ready&&!connection?.consented&&currentNotice?.action==='consent'?currentNotice:null;
 async function action(path:string,fields:Record<string,unknown>={}){const result=await mutate('crm/'+path,fields);if(result&&'crm_notice'in result)setNotice({text:result.crm_notice??'',key:noticeKey(result.state),action:path,error:path==='setup'&&result.state.connection?.state!=='ready'||path==='consent'&&!result.state.connection?.consented});return result;}
 async function verifyDestination(){
   if(pending||verifyLock.current||!connection||!pipeline||!stage)return;
   verifyLock.current=true;setVerifying(true);setNotice(null);
   try{
     const result=await action('setup',{connection_id:connection.id,confirm:true,pipeline_id:pipeline,stage_id:stage,allow_schema:allowSchema});
     if(!result)setNotice({text:'We couldn’t verify this destination. Please try again.',key:noticeKey(state),action:'setup',error:true});
   }catch{setNotice({text:'We couldn’t verify this destination. Please try again.',key:noticeKey(state),action:'setup',error:true});}
   finally{verifyLock.current=false;setVerifying(false);}
 }
 async function allowSharing(){
   if(pending||shareLock.current||!ready||!consent||!connection)return;
   shareLock.current=true;setSharing(true);setNotice(null);
   try{
     if(!await action('consent',{connection_id:connection.id,confirm:true}))setNotice({text:'Sharing could not be confirmed. Please try again.',key:noticeKey(state),action:'consent',error:true});
   }catch{setNotice({text:'Sharing could not be confirmed. Please try again.',key:noticeKey(state),action:'consent',error:true});}
   finally{shareLock.current=false;setSharing(false);}
 }
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
 return <section className={`crm-controls${choosing?' crm-choice':''}`} aria-label="HubSpot connection" data-tour="hubspot">
  <div className="section-heading"><div><div className="crm-brand">{!choosing&&<Image src="/brand/hubspot-logo.svg" alt="HubSpot" width={128} height={36}/>}<Badge tone={ready?'green':'neutral'}>{ready?'Connected':canConnect?'Optional':'Unavailable'}</Badge></div><h2 className={choosing?'crm-connect-heading':undefined}>{ready?'Your HubSpot connection':setup?'Choose a booking destination':<><span>Continue with</span><Image className="crm-heading-wordmark" src="/brand/hubspot-logo.svg" alt="HubSpot" width={128} height={36}/></>}</h2><p>{ready||setup?connection?.label:'Save approved bookings in your own HubSpot account.'}</p></div></div>
  {currentNotice?.text&&!setupNotice&&!sharingNotice&&<p className="crm-notice" role={currentNotice.error?'alert':'status'}>{currentNotice.text}</p>}
  {connection&&['finishing','finished','needs_attention'].includes(connection.state)&&<div className="crm-preview"><strong>Connection status</strong><p>Demo records: {connection.cleanup_state.replaceAll('_',' ')}<br/>App uninstall: {connection.uninstall_state.replaceAll('_',' ')}</p>{connection.state==='needs_attention'&&<small>Some changes need attention. Check HubSpot’s Connected Apps settings.</small>}</div>}
  {choosing&&<><small>{connection?.state==='finishing'?'Your connection change is still pending.':canConnect?'Choose your account and approve access on HubSpot.':state.crm_provider!=='hubspot'?'HubSpot connections haven’t been set up for this demo yet. You can continue without HubSpot.':'HubSpot connection capacity is temporarily unavailable. You can continue without HubSpot.'}</small>{feedback}<Button className="crm-connect-button" busy={opening} disabled={pending||!canConnect||connection?.state==='finishing'} onClick={()=>void connect()}>Continue with HubSpot</Button></>}
  {!choosing&&feedback}
  {setup&&connection&&<div className="crm-preview crm-destination"><p>Choose where bookings are saved. Nothing has been shared. Juniper’s sample quotes use USD, so this account’s company currency must be USD.</p>
    <label>Pipeline<select value={pipeline} disabled={pending} onChange={event=>{setPipeline(event.target.value);setStage('');}}><option value="">Choose a pipeline</option>{destinations.map(row=><option key={row.id} value={row.id}>{row.label}</option>)}</select></label>
    <label>Stage<select value={stage} disabled={pending||!selected} onChange={event=>setStage(event.target.value)}><option value="">Choose an open stage</option>{selected?.stages.map(row=><option key={row.id} value={row.id}>{row.label}</option>)}</select></label>
    {state.crm_schema_setup_allowed?<label className="checkbox-label"><input type="checkbox" checked={allowSchema} disabled={pending} onChange={event=>setAllowSchema(event.target.checked)}/>Create Choreograph ID fields in contacts and deals if needed.</label>:<small>An account admin must prepare compatible Choreograph ID fields before sharing.</small>}
    <Button busy={verifying} disabled={pending||!pipeline||!stage} onClick={()=>void verifyDestination()}>{verifying?'Verifying destination…':'Verify destination'}</Button>
    {setupNotice?.text&&<div className="crm-setup-feedback" role={setupNotice.error?'alert':'status'}><strong>{setupNotice.error?'Couldn’t verify destination':'HubSpot destination'}</strong><p>{setupNotice.text}</p></div>}
  </div>}
  {ready&&<>{!connection.consented&&<div className="crm-preview"><strong>Records to share</strong><p>{connection.contact_name} · {connection.contact_email||'No email address'}</p>{connection.destination_label&&<p>{connection.destination_label}</p>}<small>The reviewed service, time, cleaner, quote total and booking status are shared with this account. No messages are sent.</small></div>}
    <small>Demo records are removed on reset or after two hours, while HubSpot access remains available.</small>
    {!connection.consented?<><label className="checkbox-label"><input type="checkbox" checked={consent} onChange={event=>setConsent(event.target.checked)} disabled={pending}/>Allow Juniper’s sample contact and reviewed booking records, including existing bookings, in this account.</label><Button busy={sharing} disabled={!consent||pending} onClick={()=>void allowSharing()}>{manageConnection?'Allow sharing':'Allow sharing and continue'}</Button></>:<p className="crm-sharing"><Badge tone="green">Sharing allowed</Badge> Reviewed bookings{connection.destination_label?' · '+connection.destination_label:''}</p>}
    {sharingNotice?.text&&<div className="crm-setup-feedback" role="alert"><strong>Couldn’t allow sharing</strong><p>{sharingNotice.text}</p></div>}
    {!manageConnection&&connection.consented&&continuing&&<div className="crm-entry-progress" role="status" aria-busy="true"><Spinner/><span>Opening the front desk…</span></div>}
    {!manageConnection&&connection.consented&&navigationStalled&&<div className="crm-setup-feedback" role="alert"><strong>Taking longer than expected</strong><p>Your HubSpot sharing choice is saved. Open the front desk below.</p><a className="button secondary" href="/demo/workspace?tour=start">Open the front desk</a></div>}
  </>}
  {manageConnection&&canFinish&&connection&&<><Button kind="secondary" disabled={pending||!connection.can_uninstall} onClick={event=>{if(pending||!connection.can_uninstall)return;setUninstallCleanup(true);setUninstallReview({id:connection.id,label:connection.label,opener:event.currentTarget});}}>Uninstall HubSpot</Button>{!connection.can_uninstall&&<small>Another active demo uses this account. Reset that demo before uninstalling.</small>}</>}
  {!choosing&&!manageConnection&&<small className="crm-exit-note">Manage your connection later in Business → Connections.</small>}
  <AnimatePresence>{uninstallReview&&<ConfirmationDialog key={uninstallReview.id} layoutId={`hubspot-uninstall-${uninstallReview.id}`} title="Uninstall Choreograph from HubSpot?" eyebrow="Review connection" confirmLabel="Uninstall HubSpot" cancelLabel="Keep connected" pending={pending} opener={uninstallReview.opener} onClose={()=>setUninstallReview(null)} onConfirm={async()=>{
    if(!manageConnection||!canFinish||!connection?.can_uninstall||connection.id!==uninstallReview.id)return false;
    return Boolean(await action('finish',{connection_id:uninstallReview.id,confirm:true,cleanup:uninstallCleanup,uninstall:true}));
  }} errorMessage="We couldn’t confirm the uninstall request. Close this dialog and refresh Connections to check its status.">
    <div className="management-current"><strong>{uninstallReview.label}</strong><span>This removes the Choreograph app from this HubSpot account and stops sharing. Your bookings stay in this demo.</span></div>
    <label className="checkbox-label"><input type="checkbox" checked={uninstallCleanup} disabled={pending} onChange={event=>setUninstallCleanup(event.target.checked)}/>Also remove this demo’s contact and booking records.</label>
    <p>If unchecked, the demo records stay. HubSpot notifies account admins after uninstall.</p>
  </ConfirmationDialog>}</AnimatePresence>
 </section>;
}
