'use client';
import {useEffect,useState} from 'react';
import {useGuest} from './use-guest';
import {AppHeader,Badge,Button} from './ui';
import {BusinessReview} from './business-review';
import {Documents} from './documents';
import {ChatWorkspace} from './chat-workspace';
import {CRMControls} from './crm-controls';

export function WorkspaceClient(){
  const guest=useGuest();const [business,setBusiness]=useState(false);const [zone,setZone]=useState('');
  const [composerText,setComposerText]=useState('');
  const {state,pending,error}=guest;
  useEffect(()=>setComposerText(''),[state?.workspace_id]);
  useEffect(()=>{setBusiness(new URL(window.location.href).searchParams.get('view')==='business');},[]);
  function perspective(value:boolean){setBusiness(value);const url=new URL(window.location.href);url.searchParams.set('view',value?'business':'customer');window.history.replaceState(null,'',url);}
  async function retry(){const accepted=await guest.retry();if(accepted!==null)setComposerText(current=>current.trim()===accepted?'':current);}
  return <><AppHeader><span className="demo-company">Juniper Cleaning <Badge tone="neutral">Demo</Badge></span>{state&&<Button kind="secondary" onClick={()=>perspective(!business)}>{business?'Customer view':'Business view'}</Button>}</AppHeader>
    <main id="main" className="workspace-page">
      {error&&<div className="error-banner" role="alert"><p>{error.message}</p>{['SESSION_EXPIRED','SESSION_REQUIRED'].includes(error.code)?<Button kind="secondary" onClick={()=>void guest.initialize(undefined,true)}>Start a new demo</Button>:<div><Button kind="secondary" onClick={()=>void retry()}>Try again</Button><Button kind="quiet" onClick={()=>void guest.initialize()}>Refresh</Button></div>}</div>}
      {guest.needsZone&&<form onSubmit={event=>{event.preventDefault();void guest.initialize(zone);}} className="timezone-choice"><h1>Choose your timezone</h1><label>IANA timezone<input value={zone} onChange={event=>setZone(event.target.value)} placeholder="e.g. Africa/Cairo" required/></label><Button>Continue</Button></form>}
      {!state&&!guest.needsZone&&!error&&<p role="status">Opening your demo…</p>}
      {state&&<><div className="workspace-heading"><div><span className="eyebrow blue-text">{business?'Business view':'Juniper front desk'}</span><h1>{business?'Booking requests':'What can we help with?'}</h1><p>{business?'Review a request before reserving a time.':'Cleaning questions, a quote or a time that works.'}</p></div><div className="workspace-context"><Badge tone="neutral">{state.profile==='live'?'Live assistance':'Sample mode'}</Badge><small>{state.timezone}</small></div></div>
        {business?<BusinessReview state={state} pending={pending} onAction={(record,action,fields)=>void guest.mutate(`requests/${record.id}/${action}`,{request_revision:record.revision,confirm:true,...fields})}/>:<ChatWorkspace key={state.workspace_id} state={state} pending={pending} text={composerText} setText={setComposerText} onSend={text=>guest.mutate('chat',{text})} onEdit={fields=>void guest.mutate('draft',fields,'PUT')} onSubmit={()=>void guest.mutate('requests',{accept_quote:true})} onBusiness={()=>perspective(true)}/>}
        {business&&<Documents key={state.workspace_id} state={state} pending={pending} onReplace={(slot,fields)=>guest.mutate(`documents/${slot}/replace`,fields)}/>}
        {business&&<CRMControls state={state} pending={pending} mutate={guest.mutate}/>}
        <footer className="workspace-footer"><small>Fictional company and appointments · {state.crm_mode==='connected'?(state.connection?.provider==='fake'?'CRM simulated':'CRM connected'):'CRM not connected'}</small><button onClick={()=>{if(window.confirm('Start a fresh demo? Your current workspace will end.'))void guest.reset();}}>Reset demo</button></footer>
      </>}
    </main></>;
}
