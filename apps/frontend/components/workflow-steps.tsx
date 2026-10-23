'use client';

import {useRef,useSyncExternalStore,type ReactNode} from 'react';
import {motion,useScroll,useSpring,useTransform,type MotionValue} from 'motion/react';
import {Mark} from './ui';

const lift={hidden:{opacity:0,y:16,scale:.96},visible:{opacity:1,y:0,scale:1,transition:{duration:.65,ease:[.16,1,.3,1] as const}}};
const draw={hidden:{pathLength:0},visible:{pathLength:1,transition:{duration:.7,delay:.9}}};
const phoneQuery='(max-width:740px)';
const subscribePhone=(notify:()=>void)=>{const query=window.matchMedia(phoneQuery);query.addEventListener('change',notify);return()=>query.removeEventListener('change',notify);};
const phoneSnapshot=()=>window.matchMedia(phoneQuery).matches;
const serverPhoneSnapshot=()=>false;

function StepVisual({step}:{step:number}){
  return <motion.div className={`step-visual step-visual-${step}`} aria-hidden="true" initial="hidden" whileInView="visible" viewport={{once:true,amount:.45}} variants={{visible:{transition:{staggerChildren:.16,delayChildren:step*.25}}}}>
    {step===0?<>
      <motion.div variants={lift} className="step-question">What’s included?</motion.div>
      <motion.div variants={lift} className="step-answer"><span className="mini-assistant"><Mark/></span><span>Let’s take a look.<i/><i/></span></motion.div>
      <motion.div variants={lift} className="step-source"><svg viewBox="0 0 24 24" fill="none"><path d="M7 3h7l4 4v14H7zM14 3v5h4M10 12h5M10 16h5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg><span>Service guide<small>Page 2</small></span><motion.i variants={{hidden:{scaleX:0},visible:{scaleX:1,transition:{duration:.6,delay:.5}}}}/></motion.div>
    </>:step===1?<>
      <motion.div variants={lift} className="step-week"><span>WED<strong>28</strong></span><span>THU<strong>29</strong></span><span className="step-date-full">FRI<strong>30</strong></span><motion.span variants={{hidden:{scale:.85,opacity:.3},visible:{scale:1,opacity:1,transition:{delay:.5,type:'spring',stiffness:260,damping:20}}}} className="step-date-selected">SAT<strong>31</strong></motion.span></motion.div>
      <motion.div variants={lift} className="step-busy-slot"><i/>Friday’s full</motion.div>
      <motion.div variants={lift} className="step-open-slot"><span>Saturday afternoon</span><strong>13:30 <span>– 18:00</span></strong><svg viewBox="0 0 24 24" fill="none"><motion.path variants={draw} d="m5 12 4 4L19 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg></motion.div>
    </>:<>
      <motion.div variants={lift} className="step-review"><span>Home clean<strong>$185</strong></span><div><i/><i/></div><motion.span className="step-approved" variants={lift}><svg viewBox="0 0 24 24" fill="none"><motion.path variants={draw} d="m5 12 4 4L19 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>Approved</motion.span></motion.div>
      <motion.div variants={{hidden:{opacity:0,y:12,scale:.9},visible:{opacity:1,y:0,scale:1,transition:{delay:1.2,type:'spring',stiffness:230,damping:19}}}} className="step-confirmed"><span>✓</span>See you Saturday.</motion.div>
    </>}
  </motion.div>;
}

function WorkflowCard({children,index,progress,phone}:{children:ReactNode;index:number;progress:MotionValue<number>;phone:boolean}){
  const target=useRef<HTMLDivElement>(null);
  const {scrollYProgress}=useScroll({target,offset:['start .94','start .45']});
  const local=useSpring(scrollYProgress,{stiffness:160,damping:30});
  const spread=useTransform(progress,[index*.09,.72+index*.12],[0,1]);
  const x=useTransform(spread,value=>`calc(${(1-index)*(1-value)*100}% + ${(1-index)*(1-value)} * var(--workflow-gap))`);
  const y=useTransform(spread,value=>(1-value)*(24+index*10));
  const scale=useTransform(spread,[0,1],[.95,1]);
  const mobileY=useTransform(local,value=>(1-value)*48);
  const mobileScale=useTransform(local,[0,1],[.98,1]);
  const mobileOpacity=useTransform(local,[0,.75,1],[.35,1,1]);
  return <div ref={target} className="workflow-slot"><motion.article className="workflow-step" style={{x:phone?0:x,y:phone?mobileY:y,scale:phone?mobileScale:scale,opacity:phone?mobileOpacity:1}}>{children}</motion.article></div>;
}

export function WorkflowSteps(){
  const phone=useSyncExternalStore(subscribePhone,phoneSnapshot,serverPhoneSnapshot);
  const target=useRef<HTMLDivElement>(null);
  const {scrollYProgress}=useScroll({target,offset:['start .94','start .3']});
  const progress=useSpring(scrollYProgress,{stiffness:150,damping:28});
  return <div ref={target} className="steps workflow-steps">{[
    ['Ask a question','Choose a suggested question or write your own. Read the source beside the answer.'],
    ['Choose a time','Check the week and choose an available appointment.'],
    ['Confirm the booking','Review the quote and approve the request in Business view.'],
  ].map(([title,body],index)=><WorkflowCard index={index} progress={progress} phone={phone} key={title}><div className="step-meta"><strong>0{index+1}</strong><span>{index===0?'Sources':index===1?'Availability':'Approval'}</span></div><StepVisual step={index}/><h3>{title}</h3><p>{body}</p></WorkflowCard>)}</div>;
}
