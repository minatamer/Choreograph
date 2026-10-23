'use client';
import {useEffect,useRef,useState} from 'react';
import {animate,motion,useMotionValue,useScroll,useTransform} from 'motion/react';
import {ScrollButton} from './scroll-button';

export function HeroScrollCue(){
  const root=useRef<HTMLDivElement>(null),[shown,setShown]=useState(false);
  const admission=useMotionValue(0),height=useMotionValue(1);const {scrollY}=useScroll();
  const opacity=useTransform(()=>admission.get()*Math.max(0,1-scrollY.get()/(height.get()*.65)));
  useEffect(()=>{
    const hero=root.current?.closest<HTMLElement>('.landing-hero');if(!hero)return;
    let timer:ReturnType<typeof setTimeout>|undefined,admitted=false;
    let fade:ReturnType<typeof animate>|undefined;
    const measure=()=>height.set(hero.clientHeight||innerHeight);
    const eligible=()=>document.visibilityState==='visible'&&window.scrollY<height.get()*.65;
    const hide=()=>{admitted=false;setShown(false);fade?.stop();admission.set(0);};
    const wait=()=>{clearTimeout(timer);if(!eligible())return;timer=setTimeout(()=>{if(!eligible())return;admitted=true;setShown(true);fade=animate(admission,1,{duration:.5});},5000);};
    const scroll=()=>{if(admitted){if(!eligible()){hide();clearTimeout(timer);}}else wait();};
    const visibility=()=>{clearTimeout(timer);hide();wait();};
    measure();wait();const observer=new ResizeObserver(measure);observer.observe(hero);
    window.addEventListener('scroll',scroll,{passive:true});document.addEventListener('visibilitychange',visibility);
    return()=>{clearTimeout(timer);fade?.stop();observer.disconnect();window.removeEventListener('scroll',scroll);document.removeEventListener('visibilitychange',visibility);};
  },[admission,height]);
  return <motion.div ref={root} className="hero-scroll-hint" style={{opacity}} inert={!shown} aria-hidden={!shown} data-ready={shown}><ScrollButton targetId="flow" className="hero-scroll-cue">
    <span className="scroll-cue-desktop"><svg viewBox="0 0 24 34" fill="none" aria-hidden="true"><rect x="4.5" y="2.5" width="15" height="28" rx="7.5" stroke="currentColor" strokeWidth="1.4"/><rect className="scroll-cue-wheel" x="11" y="8" width="2" height="6" rx="1" fill="currentColor"/></svg><span>Scroll for more</span></span>
    <span className="scroll-cue-touch"><svg className="scroll-cue-finger" viewBox="0 0 28 32" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M9 16V6a2 2 0 0 1 4 0v7a2 2 0 0 1 4 0v2a2 2 0 0 1 4 0v2a2 2 0 0 1 4 0v4a7 7 0 0 1-7 7h-2c-3 0-4.5-1.5-6-4l-4-6a2 2 0 0 1 3-2l2 2"/><path d="M13 13v4m4-2v3m4-1v2"/></svg><span>Swipe up for more</span></span>
  </ScrollButton></motion.div>;
}
