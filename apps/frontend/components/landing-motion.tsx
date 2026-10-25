'use client';

import {useEffect,useRef,type ReactNode} from 'react';
import {motion,useScroll,useSpring,useTransform} from 'motion/react';
import {ActionLink} from './ui';

export function LandingHero(){
  const lead=useRef<HTMLDivElement>(null);
  useEffect(()=>{
    let cancelled=false,frame=0;
    // Prepare font metrics and a painted layer before starting the entrance.
    // No fixed delay: the next two frames separate preparation from playback.
    const start=()=>{if(cancelled)return;frame=requestAnimationFrame(()=>{
      frame=requestAnimationFrame(()=>{if(!cancelled&&lead.current)lead.current.dataset.entered='true';});
    });};
    void (document.fonts?.ready??Promise.resolve()).then(start,start);
    return()=>{cancelled=true;cancelAnimationFrame(frame);};
  },[]);
  return <div className="hero-intro">
      <noscript><style>{'.landing-lead{animation:hero-lead-enter .8s cubic-bezier(.2,.8,.2,1) both}'}</style></noscript>
      <div ref={lead} className="landing-lead">
        <h1>Hire a choreographer. <span>Give your business a better rhythm.</span></h1>
        <p>An AI front desk that brings every enquiry, quote and booking into harmony.</p>
        <div className="hero-actions"><ActionLink href="/demo">Try demo</ActionLink></div>
      </div>
  </div>;
}

export function ScrollReveal({children,className='',as='div',travel=56}:{children:ReactNode;className?:string;as?:'div'|'article';travel?:number}){
  const target=useRef<HTMLElement|null>(null);
  const {scrollYProgress}=useScroll({target,offset:['start 0.96','start 0.52']});
  const progress=useSpring(scrollYProgress,{stiffness:160,damping:30});
  const y=useTransform(progress,[0,1],[travel,0]);
  const opacity=useTransform(progress,[0,.75,1],[.32,1,1]);
  const scale=useTransform(progress,[0,1],[.975,1]);
  const Element=as==='article'?motion.article:motion.div;
  return <Element ref={node=>{target.current=node;}} className={className} style={{y,opacity,scale}}>{children}</Element>;
}

export function ProductReveal({children}:{children:ReactNode}){
  return <motion.div className="product-reveal" initial={{opacity:.35,y:48,scale:.975}} whileInView={{opacity:1,y:0,scale:1}} viewport={{once:true,amount:.12}} transition={{duration:.85,ease:[.16,1,.3,1]}}>{children}</motion.div>;
}
