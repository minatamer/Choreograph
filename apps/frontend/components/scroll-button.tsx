'use client';

import {useEffect,useRef,type ReactNode} from 'react';
import {animate} from 'motion';

export function ScrollButton({targetId,className,children}:{targetId:string;className:string;children:ReactNode}){
  const cancelScroll=useRef<(()=>void)|null>(null);
  useEffect(()=>()=>cancelScroll.current?.(),[]);

  useEffect(()=>{
    // Retire old section URLs without adding a navigation/history entry.
    if(window.location.hash===`#${targetId}`){
      window.history.replaceState(window.history.state,'',window.location.pathname+window.location.search);
    }
  },[targetId]);

  function scroll(){
    cancelScroll.current?.();
    const target=document.getElementById(targetId);
    if(!target)return;
    if(!target.hasAttribute('tabindex'))target.tabIndex=-1;
    const padding=parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop)||0;
    const margin=parseFloat(getComputedStyle(target).scrollMarginTop)||0;
    const top=Math.max(0,Math.min(
      window.scrollY+target.getBoundingClientRect().top-padding-margin,
      document.documentElement.scrollHeight-window.innerHeight,
    ));
    if(Math.abs(top-window.scrollY)<1){
      target.focus({preventScroll:true});
      return;
    }

    const interruptions=['wheel','touchstart','pointerdown','keydown','resize'] as const;
    const cleanup=()=>{
      interruptions.forEach(event=>window.removeEventListener(event,cancel));
      cancelScroll.current=null;
    };
    const animation=animate(window.scrollY,top,{
      duration:.9,
      ease:[.65,0,.35,1],
      // Animate every frame ourselves: native smooth scrolling can be skipped
      // by browser/platform motion preferences. The owner requires this motion.
      onUpdate:value=>window.scrollTo({top:value,behavior:'instant'}),
      onComplete:()=>{
        cleanup();
        target.focus({preventScroll:true});
      },
    });
    const cancel=(event?:Event)=>{
      // Enter can bubble to window after activating the button. Only scrolling,
      // focus navigation and Escape should interrupt this keyboard activation.
      if(event instanceof KeyboardEvent&&!['ArrowUp','ArrowDown','PageUp','PageDown','Home','End','Escape','Tab',' '].includes(event.key))return;
      animation.stop();cleanup();
    };
    cancelScroll.current=cancel;
    interruptions.forEach(event=>window.addEventListener(event,cancel,{passive:true}));
  }

  return <button type="button" className={className} aria-controls={targetId} onClick={scroll}>{children}</button>;
}
