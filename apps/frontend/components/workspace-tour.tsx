'use client';
import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {animate} from 'motion';
import {tourPanels,tourPlacement,tourSpotlight,sameTourBox,TOUR_FADE_MS,type TourBox,type TourViewport} from '@/lib/tour-layout';
import {Button,Mark} from './ui';
import type {BusinessPage} from '@/lib/workspace-navigation';

const steps=[
 {target:'assistant',business:false,title:'Meet your front desk.',text:'You’re a customer of Juniper Cleaning. Its assistant can answer from Juniper’s documents, prepare a quote and find a time.'},
 {target:'questions',business:false,title:'A good place to start.',text:'These replies adapt as you chat. Tap one to send it, or use the plus button for more questions.'},
 {target:'composer',business:false,title:'Talk it through.',text:'Ask naturally, or change your mind. Quotes, sources and available times appear in the conversation. Review the details, then book your clean.'},
 {target:'overview',business:true,page:'overview',title:'Now, the business side.',text:'Follow incoming requests, confirmed bookings and booked value.'},
 {target:'review',business:true,page:'requests',title:'You’re in control.',text:'Customer bookings arrive here with their reserved time and cleaner. Review the details, reschedule or manage the booking.'},
 {target:'calendar',business:true,page:'calendar',title:'See the whole week.',text:'This is the full staff calendar. Approved bookings appear alongside Juniper’s existing jobs. Change the week to explore.'},
 {target:'documents',business:true,page:'guides',title:'The pages behind the answers.',text:'Six documents are already uploaded. Open the original pages, or try a revised document and ask again. Replies link to the source they used.'},
 {target:'hubspot',business:true,page:'connections',title:'Your HubSpot. Your choice.',text:'Both paths use Juniper. Connect your own HubSpot to follow approved bookings after sync. You can disconnect, or uninstall through Finish demo or HubSpot Connected Apps.'},
] as const;
type Layout={view:TourViewport;hole:TourBox|null;card:TourBox};
const viewport=():TourViewport=>({left:window.visualViewport?.offsetLeft??0,top:window.visualViewport?.offsetTop??0,width:window.visualViewport?.width??innerWidth,height:window.visualViewport?.height??innerHeight});

export function WorkspaceTour({business,page,onPerspective,onClose}:{business:boolean;page:BusinessPage;onPerspective:(business:boolean,page?:BusinessPage)=>void;onClose:()=>void}){
 const [index,setIndex]=useState(-1);const [layout,setLayout]=useState<Layout|null>(null);const [leaving,setLeaving]=useState(false);const [ready,setReady]=useState(false);
 const card=useRef<HTMLElement>(null);const timer=useRef<ReturnType<typeof setTimeout>|null>(null);const moving=useRef(false);
 const closing=useRef(false);const stopScroll=useRef<(()=>void)|null>(null);
 const callbacks=useRef({onPerspective,onClose});callbacks.current={onPerspective,onClose};
 const origin=useRef({focus:typeof document==='undefined'?null:document.activeElement as HTMLElement|null});
 const step=index>=0?steps[index]:null;
 useEffect(()=>{
  const root=document.querySelector<HTMLElement>('[data-demo-workspace-root]');const previousInert=root?.inert??false;
  if(root)root.inert=true;
  return()=>{if(root)root.inert=previousInert;if(timer.current)clearTimeout(timer.current);requestAnimationFrame(()=>{const previous=origin.current.focus;const target=previous?.isConnected&&previous!==document.body&&!previous.matches(':disabled')?previous:document.querySelector<HTMLElement>('#enquiry:not(:disabled),.workspace-reset');target?.focus({preventScroll:true});});};
 },[]);
 function finish(){
  if(closing.current)return;closing.current=true;moving.current=true;stopScroll.current?.();if(timer.current)clearTimeout(timer.current);setLeaving(true);
  timer.current=setTimeout(()=>{callbacks.current.onPerspective(false,'overview');callbacks.current.onClose();},TOUR_FADE_MS);
 }
 function move(next:number){
  if(moving.current)return;if(next>=steps.length){finish();return;}
  moving.current=true;setLeaving(true);
  timer.current=setTimeout(()=>{setReady(false);setIndex(next);setLeaving(false);if(next>=0){const destination=steps[next];callbacks.current.onPerspective(destination.business,'page'in destination?destination.page:undefined);}},TOUR_FADE_MS);
 }
 useLayoutEffect(()=>{
  if(step&&(business!==step.business||(step.business&&'page'in step&&page!==step.page)))return;
  let frame=0;let disposed=false;let scroll:ReturnType<typeof animate>|undefined;
  let target=step?document.querySelector<HTMLElement>(`[data-tour="${step.target}"]`):null;
  if(target&&target.getBoundingClientRect().height>viewport().height*.5)target=target.querySelector<HTMLElement>('.section-heading,.card-heading,header,.queue-title')??target;
  const measure=()=>{
   if(disposed)return;
   const view=viewport();const bounds=target?.isConnected?target.getBoundingClientRect():null;
   const hole=bounds&&bounds.width>0&&bounds.height>0?tourSpotlight(bounds,view):null;
   const box=tourPlacement(hole?{...hole,right:hole.left+hole.width,bottom:hole.top+hole.height}:null,view,card.current?.offsetHeight??300);
   setLayout(previous=>previous&&sameTourBox(previous.card,box)&&(!previous.hole&&!hole||previous.hole&&hole&&sameTourBox(previous.hole,hole))&&sameTourBox(previous.view,view)?previous:{view,hole,card:box});
  };
   const show=()=>{if(disposed||closing.current)return;measure();setReady(true);moving.current=false;requestAnimationFrame(()=>card.current?.querySelector<HTMLButtonElement>('button:not(:disabled)')?.focus({preventScroll:true}));};
  const targetBounds=target?.getBoundingClientRect();
  const top=targetBounds?Math.max(0,Math.min(scrollY+targetBounds.top-118,document.documentElement.scrollHeight-innerHeight)):scrollY;
  if(targetBounds&&Math.abs(top-scrollY)>4){scroll=animate(scrollY,top,{duration:.55,ease:[.65,0,.35,1],onUpdate:value=>window.scrollTo({top:value,behavior:'instant'}),onComplete:show});}else show();
  stopScroll.current=()=>scroll?.stop();
  const schedule=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(measure);};
  const observer=new ResizeObserver(schedule);if(card.current)observer.observe(card.current);if(target)observer.observe(target);
  window.addEventListener('resize',schedule);window.addEventListener('scroll',schedule,{passive:true});window.visualViewport?.addEventListener('resize',schedule);window.visualViewport?.addEventListener('scroll',schedule);
  return()=>{disposed=true;scroll?.stop();cancelAnimationFrame(frame);observer.disconnect();window.removeEventListener('resize',schedule);window.removeEventListener('scroll',schedule);window.visualViewport?.removeEventListener('resize',schedule);window.visualViewport?.removeEventListener('scroll',schedule);};
 },[index,business,page]);
 useEffect(()=>{
  const key=(event:KeyboardEvent)=>{
   if(event.key==='Escape'){event.preventDefault();finish();}
   if(event.key!=='Tab')return;
   const nodes=card.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)');if(!nodes?.length)return;
   if(event.shiftKey&&document.activeElement===nodes[0]){event.preventDefault();nodes[nodes.length-1].focus();}
   else if(!event.shiftKey&&document.activeElement===nodes[nodes.length-1]){event.preventDefault();nodes[0].focus();}
  };
  document.addEventListener('keydown',key);return()=>document.removeEventListener('keydown',key);
 });
 const view=layout?.view??{left:0,top:0,width:390,height:844};
 return createPortal(<div className="workspace-tour-layer" role="dialog" aria-modal="true" aria-labelledby="tour-title"><div className="tour-presentation" data-leaving={leaving} data-ready={ready}>
  {tourPanels(layout?.hole??null,view).map((panel,index)=><div key={index} className="tour-scrim" style={panel}/>)}
  {layout?.hole&&<div className="tour-highlight" style={layout.hole}/>}
  <section className="workspace-tour-card" ref={card} style={{left:layout?.card.left??16,top:layout?.card.top??16,width:layout?.card.width??Math.min(348,view.width-32),maxHeight:view.height-32}}>
   <div className="tour-card-heading"><span className="tour-brand"><Mark/></span><span>{step?`${index+1} of ${steps.length}`:'A little introduction'}</span><button type="button" className="tour-close" aria-label="Close tour" onClick={finish}>×</button></div>
   <h2 id="tour-title">{step?.title??'A better time starts here.'}</h2><p>{step?.text??'Take a quick look around Juniper’s front desk. See the conversation, the documents behind its answers, and what happens on the business side.'}</p>
   {step&&<div className="tour-progress" aria-label={`Step ${index+1} of ${steps.length}`}>{steps.map((_,position)=><span key={position} data-current={position<=index}/>)}</div>}
   <div className="tour-actions"><Button kind="quiet" onClick={finish}>Skip tour</Button>{index>=0&&<Button kind="secondary" onClick={()=>move(index-1)}>Back</Button>}<Button onClick={()=>move(index+1)}>{step?(index===steps.length-1?'Finish':'Next'):'Show me around'}<span aria-hidden="true">→</span></Button></div>
  </section>
 </div></div>,document.body);
}
