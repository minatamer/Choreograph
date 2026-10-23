'use client';
import {useDemoGuest} from './demo-guest';
import {AppHeader,Badge,Button,Arrow} from './ui';
import {CRMControls} from './crm-controls';
import {useEffect,useRef,useState,useTransition} from 'react';
import {useRouter} from 'next/navigation';
import {AnimatePresence,motion} from 'motion/react';
import {SampleGuideIntro} from './guide-papers';

const previewSteps=[
 {label:'Ask a question',path:'M8 17H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-6l-5 4v-4Zm3-9a2 2 0 1 1 3 1.7c-1 .6-2 .8-2 2.3M12 14h.01'},
 {label:'Get a quote',path:'M8 3h8l4 4v14H4V3h4Zm8 0v5h4M8 11h6M8 15h8M8 18h5'},
 {label:'Book a clean',path:'M7 3v4M17 3v4M3 10h18M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Zm3 10 3 3 5-5'},
];

export function EntryClient({resumeSetup=false}:{resumeSetup?:boolean}){
 const guest=useDemoGuest();const {state,pending,error,needsZone,initialize}=guest;
 const [requested,setRequested]=useState(resumeSetup);const [zone,setZone]=useState('');
 useEffect(()=>{if(resumeSetup&&!state)void initialize();},[resumeSetup,initialize]);
 function start(){if(pending)return;setRequested(true);if(!state)void initialize(needsZone?zone:undefined);}
 const started=requested&&!!state;
 return <><AppHeader/><AnimatePresence mode="wait" initial={false}>{started?
  <motion.div key="setup" initial={{opacity:0,y:12}} animate={{opacity:1,y:0}} transition={{duration:.3}}><EntrySetup/></motion.div>:
  <motion.main key="welcome" id="main" className="entry-page entry-welcome" exit={{opacity:0,y:-12}} transition={{duration:.2}} aria-labelledby="demo-welcome-title">
   <span className="eyebrow blue-text">Your front desk</span><h1 id="demo-welcome-title">Meet Juniper Cleaning.</h1><p className="entry-intro">A fictional home-cleaning company. You’ll try its front desk, with a ready-made schedule and business documents.</p>
   <div className="entry-choices">
    <motion.article className="intro-guides" initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{duration:.5,ease:[.16,1,.3,1]}}><SampleGuideIntro/></motion.article>
    <article className="subtle intro-next"><h2>Try the front desk.</h2>
     <ol className="entry-preview-steps" aria-label="Try the AI front desk">
      {previewSteps.map(({label,path},index)=><motion.li key={label} initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{duration:.4,delay:.15+index*.1}}><span className={`entry-step-icon step-${index}`}><svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d={path} stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg></span><span>{label}</span></motion.li>)}
     </ol>
     <form className="entry-continue" onSubmit={event=>{event.preventDefault();start();}}>
     {error&&<p role="alert">{error.message}</p>}
     {needsZone&&<label className="demo-timezone">Choose your timezone<input value={zone} onChange={event=>setZone(event.target.value)} placeholder="UTC" disabled={pending} required/></label>}
     <Button busy={pending}>Continue<Arrow/></Button><small>No signup needed.</small>
     </form>
    </article>
   </div>
  </motion.main>
 }</AnimatePresence></>;
}

function EntrySetup(){
 const guest=useDemoGuest();const {state,pending,error}=guest;const router=useRouter();
 const [navigating,startNavigation]=useTransition();const [destination,setDestination]=useState<'skip'|'connected'|null>(null);
 const [openingHubSpot,setOpeningHubSpot]=useState(false);const busy=pending||navigating||openingHubSpot;
 const [notice,setNotice]=useState('');
 const heading=useRef<HTMLHeadingElement>(null);
 useEffect(()=>{const value=new URL(window.location.href).searchParams.get('crm');if(value==='unavailable')setNotice('The HubSpot connection could not be completed. You can continue without HubSpot.');if(value==='cancelled')setNotice('Connection cancelled. No HubSpot records were sent.');window.history.replaceState(null,'','/demo');window.scrollTo(0,0);heading.current?.focus({preventScroll:true});router.prefetch('/demo/workspace');},[router]);
 function proceed(){if(busy)return;setDestination('connected');startNavigation(()=>router.push('/demo/workspace'));}
 function skip(){if(busy)return;setDestination('skip');startNavigation(async()=>{const result=await guest.mutate('crm/skip',{});if(result)startNavigation(()=>router.push('/demo/workspace'));});}
 return <main id="main" className="entry-page"><span className="eyebrow blue-text">Juniper Cleaning</span><h1 ref={heading} tabIndex={-1}>Same Juniper. Your choice.</h1><p className="entry-intro">Both paths use Juniper’s documents, assistant and schedule. Connect your HubSpot to follow approved bookings in your own account.</p>
  {error&&<p role="alert">{error.message}</p>}{notice&&<p role="status">{notice}</p>}
  <div className="entry-choices"><article>{state&&<CRMControls state={state} pending={busy} mutate={guest.mutate} onContinue={proceed} continuing={navigating&&destination==='connected'} onOpeningChange={setOpeningHubSpot}/>}</article><article className="subtle"><Badge tone="neutral">No connection needed</Badge><h2>Continue without HubSpot</h2><p>The complete Juniper experience: questions with sources, a quote, a time and a reviewed booking. Nothing is sent to HubSpot.</p><Button kind="secondary" disabled={!state||busy} busy={navigating&&destination==='skip'} onClick={skip}>Continue without HubSpot</Button></article></div><p className="entry-note">Scheduling uses your local timezone.</p></main>;
}
