'use client';
import {useLayoutEffect,useRef} from 'react';
import {animate} from 'motion';

/** Follow new conversation activity in the history pane, never the document. */
export function useChatScroll(activity:string){
 const pane=useRef<HTMLDivElement>(null),content=useRef<HTMLDivElement>(null);
 const reveal=useRef<(element:HTMLElement)=>void>(()=>{});
 const follow=useRef<(immediate?:boolean)=>void>(()=>{});
 const followActivity=useRef(()=>{});
 useLayoutEffect(()=>{
  const node=pane.current,body=content.current;if(!node||!body)return;
  let frame=0;let first=true;let following=true;let target:number|undefined;let revealed:HTMLElement|undefined;let focusOnArrival=false;let motion:ReturnType<typeof animate>|undefined;
  const stop=()=>{motion?.stop();motion=undefined;target=undefined;};
  const focus=()=>{if(focusOnArrival&&revealed?.isConnected){focusOnArrival=false;revealed.focus({preventScroll:true});}};
  const revealCard=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{
   if(!revealed?.isConnected){revealed=undefined;return;}
   const top=Math.max(0,Math.min(node.scrollHeight-node.clientHeight,
    node.scrollTop+revealed.getBoundingClientRect().top-node.getBoundingClientRect().top-16));
   if(target===top)return;
   stop();target=top;first=false;
   if(Math.abs(top-node.scrollTop)<1){focus();return;}
   motion=animate(node.scrollTop,top,{duration:.42,ease:[.2,.8,.2,1],onUpdate:value=>{node.scrollTop=value;},onComplete:focus});
  });};
  reveal.current=element=>{cancelAnimationFrame(frame);stop();following=false;revealed=element;focusOnArrival=true;body.style.minHeight='';revealCard();};
  follow.current=(immediate=false)=>{cancelAnimationFrame(frame);
   if(immediate){stop();node.scrollTop=Math.max(0,node.scrollHeight-node.clientHeight);first=false;return;}
   frame=requestAnimationFrame(()=>{
   const top=Math.max(0,node.scrollHeight-node.clientHeight);
   // Pending, response and resize notifications can describe the same destination.
   if(target===top)return;
   stop();target=top;
   if(first){node.scrollTop=top;first=false;return;}
   if(Math.abs(top-node.scrollTop)<1)return;
   motion=animate(node.scrollTop,top,{duration:.3,ease:[.2,.8,.2,1],onUpdate:value=>{node.scrollTop=value;}});
  });};
  const observer=new ResizeObserver(entries=>{
   const viewport=entries.some(entry=>entry.target===node);
   if(viewport&&!following)body.style.minHeight='';
   if(revealed)revealCard();else if(following)follow.current(viewport);
  });observer.observe(body);observer.observe(node);
  const interrupt=()=>{following=false;revealed=undefined;focusOnArrival=false;cancelAnimationFrame(frame);stop();};
  const interact=(event:Event)=>{
   if(!(event.target instanceof Element)||!event.target.closest('.calendar-card,.chat-review,.request-sent,.booking-outcome'))return;
   interrupt();
   // Keep the history footprint when a review becomes a shorter sent/confirmed card.
   body.style.minHeight=`${body.getBoundingClientRect().height}px`;
  };
  const newActivity=()=>{revealed=undefined;focusOnArrival=false;following=true;body.style.minHeight='';follow.current();};
  followActivity.current=newActivity;
  node.addEventListener('wheel',interrupt,{passive:true});node.addEventListener('touchstart',interrupt,{passive:true});node.addEventListener('pointerdown',interact,true);node.addEventListener('click',interact,true);node.addEventListener('keydown',interact,true);newActivity();
  return()=>{follow.current=()=>{};followActivity.current=()=>{};reveal.current=()=>{};interrupt();observer.disconnect();body.style.minHeight='';node.removeEventListener('wheel',interrupt);node.removeEventListener('touchstart',interrupt);node.removeEventListener('pointerdown',interact,true);node.removeEventListener('click',interact,true);node.removeEventListener('keydown',interact,true);};
 },[]);
 useLayoutEffect(()=>followActivity.current(),[activity]);
 return {pane,content,reveal};
}
