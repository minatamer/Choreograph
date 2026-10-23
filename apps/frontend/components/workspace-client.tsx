'use client';
import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import {useDemoGuest} from './demo-guest';
import {AppHeader,Button,Spinner} from './ui';
import {BusinessReview} from './business-review';
import {Documents} from './documents';
import {ChatWorkspace} from './chat-workspace';
import {CRMControls} from './crm-controls';
import {ViewSwitch} from './view-switch';
import {WorkspaceTour} from './workspace-tour';
import {tourWasSeen} from '@/lib/tour-preference';

export function WorkspaceClient(){
  const guest=useDemoGuest();const [business,setBusiness]=useState(false);const [zone,setZone]=useState('');
  const [composerText,setComposerText]=useState('');
  const [calendarWeek,setCalendarWeek]=useState('');
  const [tourOpen,setTourOpen]=useState(false);const checkedTour=useRef(false);
  const workspace=useRef<HTMLDivElement>(null);
  const {state,pending,error}=guest;
  const {initialize}=guest;
  useEffect(()=>{if(!state&&!error&&!guest.needsZone)void initialize();},[initialize]);
  useEffect(()=>{setComposerText('');setCalendarWeek('');},[state?.workspace_id]);
  useEffect(()=>{setBusiness(new URL(window.location.href).searchParams.get('view')==='business');},[]);
  useLayoutEffect(()=>{
    if(business)return;
    const node=workspace.current;if(!node)return;
    const htmlOverflow=document.documentElement.style.overflow,bodyOverflow=document.body.style.overflow;
    document.documentElement.style.overflow='hidden';document.body.style.overflow='hidden';window.scrollTo({top:0,behavior:'instant'});
    let frame=0;const update=()=>{node.style.setProperty('--workspace-height',`${window.visualViewport?.height??innerHeight}px`);node.style.setProperty('--workspace-top',`${window.visualViewport?.offsetTop??0}px`);};
    const schedule=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(update);};update();
    window.addEventListener('resize',schedule);window.visualViewport?.addEventListener('resize',schedule);window.visualViewport?.addEventListener('scroll',schedule);
    return()=>{cancelAnimationFrame(frame);document.documentElement.style.overflow=htmlOverflow;document.body.style.overflow=bodyOverflow;window.removeEventListener('resize',schedule);window.visualViewport?.removeEventListener('resize',schedule);window.visualViewport?.removeEventListener('scroll',schedule);};
  },[business]);
  useEffect(()=>{if(!state||pending||checkedTour.current)return;checkedTour.current=true;if(!tourWasSeen(()=>localStorage)&&!composerText&&!document.querySelector('.source-reader')&&!document.activeElement?.matches('input,textarea'))setTourOpen(true);},[state,pending,composerText]);
  function perspective(value:boolean){if(value===business)return;setBusiness(value);const url=new URL(window.location.href);url.searchParams.set('view',value?'business':'customer');window.history.replaceState(null,'',url);window.scrollTo({top:0,behavior:'smooth'});}
  async function retry(){const accepted=await guest.retry();if(accepted!==null)setComposerText(current=>current.trim()===accepted?'':current);}
  return <><div ref={workspace} className={business?'business-workspace':'customer-workspace'} data-demo-workspace-root><AppHeader className="workspace-app-header">{state&&<><div className="workspace-header-tools"><button type="button" className="workspace-reset" aria-label="Reset demo" title="Reset demo" onClick={()=>{if(window.confirm('Start a fresh demo? Your current workspace will end.'))void guest.reset();}}><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M3.5 10a8.5 8.5 0 1 1 2 8.3M3.5 4.5V10H9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg><span className="workspace-reset-label">Reset demo</span></button></div><ViewSwitch business={business} onChange={perspective}/></>}</AppHeader>
    <main id="main" className={`workspace-page ${business?'business-page':'customer-page'}`}>
      {error&&<div className="error-banner" role="alert"><p>{error.message}</p>{['SESSION_EXPIRED','SESSION_REQUIRED'].includes(error.code)?<Button kind="secondary" onClick={()=>void guest.initialize(undefined,true)}>Start a new demo</Button>:<div><Button kind="secondary" onClick={()=>void retry()}>Try again</Button><Button kind="quiet" onClick={()=>void guest.initialize()}>Refresh</Button></div>}</div>}
      {guest.needsZone&&<form onSubmit={event=>{event.preventDefault();if(!pending)void guest.initialize(zone);}} className="timezone-choice"><h1>Choose your timezone</h1><label>Timezone<input value={zone} onChange={event=>setZone(event.target.value)} placeholder="UTC" disabled={pending} required/></label><Button busy={pending}>Continue</Button></form>}
      {!state&&!guest.needsZone&&!error&&<div className="workspace-loading" role="status"><Spinner/><span className="sr-only">Loading the front desk</span></div>}
      {state&&<>{business&&<div className="workspace-heading"><div><span className="eyebrow blue-text">Business view · Juniper Cleaning</span><h1>Your week, arranged.</h1><p>Review a request. Make room for the day.</p></div></div>}
        {business?<BusinessReview state={state} onClear={async id=>Boolean(await guest.mutate(`calendar/${id}/clear`,{}))} pending={pending} selectedWeek={calendarWeek} onWeek={setCalendarWeek} onAction={(record,action,fields)=>void guest.mutate(`requests/${record.id}/${action}`,{request_revision:record.revision,confirm:true,...fields})}/>:<ChatWorkspace key={state.workspace_id} state={state} pending={pending} text={composerText} setText={setComposerText} onSend={text=>guest.mutate('chat',{text})} onEdit={fields=>void guest.mutate('draft',fields,'PUT')} onSubmit={()=>void guest.mutate('requests',{accept_quote:true})} onBusiness={()=>perspective(true)} onTour={()=>setTourOpen(true)}/>}
        {business&&<Documents key={state.workspace_id} state={state} pending={pending} onReplace={(slot,fields)=>guest.mutate(`documents/${slot}/replace`,fields)}/>}
        {business&&<CRMControls state={state} pending={pending} mutate={guest.mutate}/>}
      </>}
    </main></div>{state&&tourOpen&&<WorkspaceTour key={state.workspace_id} business={business} onPerspective={perspective} onClose={()=>setTourOpen(false)}/>}</>;
}
