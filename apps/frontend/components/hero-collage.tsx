'use client';

import Image from 'next/image';
import {useEffect,useState} from 'react';
import {motion,useMotionValue,useScroll,useTransform} from 'motion/react';
import {Mark} from './ui';

// Decorative, fictional interface panels mixed with licensed photography.
// Photo sources and licence are recorded in SBS-008.
const strips=[
  ['meeting','week','chat'],
  ['chat','planner','day'],
  ['week','team','chat'],
  ['planner','day','meeting'],
] as const;
type Frame=typeof strips[number][number];

function CalendarFrame({day=false}:{day?:boolean}){
  return <div className={`collage-calendar ${day?'is-day':''}`}>
    <div className="collage-window-title"><Mark/><span>{day?'A little room in your day.':'A week, well arranged.'}</span></div>
    {day?<><div className="collage-day-title"><span>Saturday</span><strong>31</strong></div><div className="collage-agenda"><span>09:00</span><p>Team catch-up</p><span>11:00</span><p>Time to focus</p><span>13:30</span><p>Home clean <i>✓</i></p></div></>:<><div className="collage-week-labels">{['M','T','W','T','F'].map((label,index)=><span key={index}>{label}<strong>{26+index}</strong></span>)}</div><div className="collage-week-grid">{[0,1,2,3,4].map(index=><div key={index}><i/><i/></div>)}</div></>}
  </div>;
}
function ChatFrame(){
  return <div className="collage-chat"><div className="collage-window-title"><Mark/><span>A good conversation.</span></div><p className="collage-chat-question">Could we find a time next week?</p><p className="collage-chat-answer">Of course. How does Monday afternoon sound?</p><p className="collage-chat-question">Perfect. See you then!</p><div className="collage-chat-booking"><span>Monday, 2 June</span><strong>13:30 <span>– 18:00</span></strong><span>Home clean <i>✓</i></span></div></div>;
}
function FilmFrame({kind}:{kind:Frame}){
  return <div className={`collage-frame frame-${kind}`}>{kind==='week'||kind==='day'?<CalendarFrame day={kind==='day'}/>:kind==='chat'?<ChatFrame/>:<Image src={`/illustrations/collage/${kind}.jpg`} alt="" width={1000} height={750} sizes="(max-width:600px) 240px, (max-width:1100px) 300px, 440px" quality={75} loading="eager"/>}</div>;
}

export function HeroCollage(){
  const [moving,setMoving]=useState(true);
  const viewportHeight=useMotionValue(900);
  const {scrollY}=useScroll();
  // Preserve a faint trace throughout the landing, without a section boundary.
  const opacity=useTransform(()=>.045+.955*Math.exp(-1.6*Math.max(0,scrollY.get())/viewportHeight.get()));
  useEffect(()=>{
    const update=()=>setMoving(document.visibilityState==='visible');
    const resize=()=>viewportHeight.set(Math.max(1,window.innerHeight));
    document.addEventListener('visibilitychange',update);
    window.addEventListener('resize',resize);
    resize();
    update();
    return ()=>{document.removeEventListener('visibilitychange',update);window.removeEventListener('resize',resize);};
  },[viewportHeight]);
  return <motion.div className="hero-collage" data-moving={moving} aria-hidden="true" style={{opacity}}><div className="collage-strips"><div className="collage-track">{[0,1].map(copy=><div className="collage-reel" key={copy}>{strips.map((frames,index)=><div className={`collage-strip strip-${index}`} key={index}>{frames.map((kind,frame)=><FilmFrame kind={kind} key={frame}/>)}</div>)}</div>)}</div></div></motion.div>;
}
