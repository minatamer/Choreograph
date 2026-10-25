'use client';
import {useEffect,useLayoutEffect,useRef,useState,useTransition} from 'react';
import {useRouter} from 'next/navigation';
import {motion} from 'motion/react';
import {useDemoGuest} from './demo-guest';
import {Button,Spinner} from './ui';
import {BusinessReview} from './business-review';
import {BusinessOverview} from './business-overview';
import {StaffCalendar} from './staff-calendar';
import {BusinessSidebar} from './business-sidebar';
import {HeroCollage} from './hero-collage';
import {CustomerFooter} from './workspace-controls';
import {Documents} from './documents';
import {ChatWorkspace} from './chat-workspace';
import {CRMControls} from './crm-controls';
import {WorkspaceTour} from './workspace-tour';
import {tourWasSeen} from '@/lib/tour-preference';
import {businessPages,workspaceLocation,workspaceSearch,type BusinessPage} from '@/lib/workspace-navigation';
import type {CalendarStatus} from '@/lib/appointment-status';

export function WorkspaceClient(){
 const router=useRouter();const [resetNavigating,startResetNavigation]=useTransition();const resetFrom=useRef<string|null>(null);
 const guest=useDemoGuest();const [business,setBusiness]=useState(false),[page,setPage]=useState<BusinessPage>('overview'),[collapsed,setCollapsed]=useState(false),[zone,setZone]=useState('');
 const [composerText,setComposerText]=useState(''),[calendarWeek,setCalendarWeek]=useState('');
 const [visible,setVisible]=useState<Set<CalendarStatus>>(()=>new Set(['confirmed','completed','cancelled']));
 const [tourOpen,setTourOpen]=useState(false);const checkedTour=useRef(false),workspace=useRef<HTMLDivElement>(null),heading=useRef<HTMLHeadingElement>(null);
 const {state,pending,error,initialize}=guest;
 useEffect(()=>{
  if(!resetFrom.current||!state||state.workspace_id===resetFrom.current)return;
  resetFrom.current=null;setTourOpen(false);startResetNavigation(()=>router.replace('/demo?step=connect'));
 },[state,router]);
 useEffect(()=>{if(!state&&!error&&!guest.needsZone)void initialize();},[initialize]);
 useEffect(()=>{setComposerText('');setCalendarWeek('');setVisible(new Set(['confirmed','completed','cancelled']));},[state?.workspace_id]);
 useEffect(()=>{const restore=()=>{const value=workspaceLocation(window.location.search);setBusiness(value.business);setPage(value.page);};restore();window.addEventListener('popstate',restore);return()=>window.removeEventListener('popstate',restore);},[]);
 useLayoutEffect(()=>{
  if(business)return;const node=workspace.current;if(!node)return;
  const htmlOverflow=document.documentElement.style.overflow,bodyOverflow=document.body.style.overflow;
  document.documentElement.style.overflow='hidden';document.body.style.overflow='hidden';window.scrollTo({top:0,behavior:'instant'});
  let frame=0;const update=()=>{node.style.setProperty('--workspace-height',`${window.visualViewport?.height??innerHeight}px`);node.style.setProperty('--workspace-top',`${window.visualViewport?.offsetTop??0}px`);};
  const schedule=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(update);};update();
  window.addEventListener('resize',schedule);window.visualViewport?.addEventListener('resize',schedule);window.visualViewport?.addEventListener('scroll',schedule);
  return()=>{cancelAnimationFrame(frame);document.documentElement.style.overflow=htmlOverflow;document.body.style.overflow=bodyOverflow;window.removeEventListener('resize',schedule);window.visualViewport?.removeEventListener('resize',schedule);window.visualViewport?.removeEventListener('scroll',schedule);};
 },[business]);
 useEffect(()=>{if(business&&!tourOpen)heading.current?.focus({preventScroll:true});},[business,page,tourOpen,state?.workspace_id]);
 useEffect(()=>{if(!state||pending||checkedTour.current)return;checkedTour.current=true;if(!tourWasSeen(()=>localStorage)&&!composerText&&!document.querySelector('.source-reader')&&!document.activeElement?.matches('input,textarea'))setTourOpen(true);},[state,pending,composerText]);
 function navigate(value:boolean,nextPage:BusinessPage=page,replace=false){
  const changed=value!==business||nextPage!==page;setBusiness(value);setPage(nextPage);
  const url=new URL(window.location.href);url.search=workspaceSearch(url.search,value,nextPage);
  if(url.href!==window.location.href)window.history[replace?'replaceState':'pushState'](null,'',url);
  if(changed)window.scrollTo({top:0,behavior:'instant'});
 }
 async function retry(){const accepted=await guest.retry();if(accepted!==null)setComposerText(current=>current.trim()===accepted?'':current);}
 const destination=businessPages.find(item=>item.id===page)!;
 const week=calendarWeek||state?.calendar_week_start||state?.scenario.week_start||'';
 const perspective=(value:boolean)=>navigate(value,page,true);
 async function reset(){
  if(!state)return false;resetFrom.current=state.workspace_id;
  return Boolean(await guest.reset());
 }
 return <><div ref={workspace} className={business?'business-workspace':'customer-workspace'} data-collapsed={collapsed} data-demo-workspace-root>
  {!business&&state&&<HeroCollage faded/>}
  {business&&<BusinessSidebar ready={!!state&&!pending&&!resetNavigating} businessName="Juniper Cleaning" page={page} collapsed={collapsed} onCollapse={()=>setCollapsed(value=>!value)} onNavigate={value=>navigate(true,value)} onReset={reset} onPerspective={perspective}/>}
  <main id="main" className={`workspace-page ${business?'business-page':'customer-page'}`}>
   {error&&<div className="error-banner" role="alert"><p>{error.message}</p>{['SESSION_EXPIRED','SESSION_REQUIRED'].includes(error.code)?<Button kind="secondary" onClick={()=>void guest.initialize(undefined,true)}>Start a new demo</Button>:<div><Button kind="secondary" onClick={()=>void retry()}>Try again</Button><Button kind="quiet" onClick={()=>void guest.initialize()}>Refresh</Button></div>}</div>}
   {guest.needsZone&&<form onSubmit={event=>{event.preventDefault();if(!pending)void guest.initialize(zone);}} className="timezone-choice"><h1>Choose your timezone</h1><label>Timezone<input value={zone} onChange={event=>setZone(event.target.value)} placeholder="UTC" disabled={pending} required/></label><Button busy={pending}>Continue</Button></form>}
   {!state&&!guest.needsZone&&!error&&<div className="workspace-loading" role="status"><Spinner/><span className="sr-only">Loading the front desk</span></div>}
   {state&&<>{business?<><header className="business-page-heading"><h1 ref={heading} tabIndex={-1}>{destination.label}</h1><p>{destination.description}</p></header><motion.div key={page} className="business-content" initial={{opacity:0}} animate={{opacity:1}} transition={{duration:.2}}>
    {page==='overview'&&<BusinessOverview state={state} week={week} onWeek={setCalendarWeek} onNavigate={(nextPage,targetWeek)=>{if(targetWeek){const first=state.calendar_first_week_start??state.calendar_week_start??week,last=state.calendar_last_week_start??first;setCalendarWeek(targetWeek<first?first:targetWeek>last?last:targetWeek);}navigate(true,nextPage);}} pending={pending} onClear={async id=>Boolean(await guest.mutate(`calendar/${id}/clear`,{}))}/>}
    {page==='requests'&&<BusinessReview state={state} pending={pending} onAction={(record,action,fields)=>guest.mutate(`requests/${record.id}/${action}`,{request_revision:record.revision,confirm:true,...fields})}/>}
    {page==='calendar'&&<StaffCalendar state={state} week={week} onWeek={setCalendarWeek} visible={visible} onVisibilityChange={setVisible} pending={pending} onClear={async id=>Boolean(await guest.mutate(`calendar/${id}/clear`,{}))}/>}
    {page==='guides'&&<Documents key={state.workspace_id} state={state} pending={pending} onReplace={(slot,fields)=>guest.mutate(`documents/${slot}/replace`,fields)}/>}
    {page==='connections'&&<CRMControls state={state} pending={pending} mutate={guest.mutate} manageConnection/>}
   </motion.div></>:<ChatWorkspace key={state.workspace_id} state={state} pending={pending} text={composerText} setText={setComposerText} onSend={text=>guest.mutate('chat',{text})} onEdit={fields=>guest.mutate('draft',fields,'PUT')} onSubmit={request=>void (request?guest.mutate(`requests/${request.id}/approve`,{request_revision:request.revision,confirm:true}):guest.mutate('bookings',{accept_quote:true}))} onBookingAction={(record,action,fields)=>guest.mutate(`requests/${record.id}/${action}`,{request_revision:record.revision,confirm:true,...fields})} onBusiness={()=>navigate(true,'requests')} onTour={()=>setTourOpen(true)}/>}</>}
  </main>{!business&&<CustomerFooter ready={!!state&&!pending&&!resetNavigating} onReset={reset} onPerspective={perspective}/>}
 </div>{state&&tourOpen&&<WorkspaceTour key={state.workspace_id} business={business} page={page} onPerspective={(value,nextPage)=>navigate(value,nextPage??page,true)} onClose={()=>setTourOpen(false)}/>}</>;
}
