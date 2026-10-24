'use client';

import {useEffect,useId,useRef,useState,type ReactNode} from 'react';
import {AnimatePresence,LayoutGroup,animate,motion} from 'motion/react';
import {Mark} from './ui';
import {ReplyText} from './reply-text';

type Beat = 'question' | 'suggestion' | 'clarification' | 'review' | 'approved' | 'booked' | 'change-request' | 'change-review' | 'change-approved' | 'rescheduled';
const story: {beat:Beat;at:number}[] = [
  {beat:'question',at:0},
  {beat:'suggestion',at:600},
  {beat:'clarification',at:2300},
  {beat:'review',at:2900},
  {beat:'approved',at:4900},
  {beat:'booked',at:5600},
  {beat:'change-request',at:7600},
  {beat:'change-review',at:8200},
  {beat:'change-approved',at:10200},
  {beat:'rescheduled',at:10900},
];
const spring = {type:'spring' as const,stiffness:250,damping:29,mass:.9};
type Day = {id:string;name:string;date:string;event?:string;time?:string;start?:number;duration?:number;tone?:string};
const days:Day[] = [
  {id:'mon26',name:'Mon',date:'26',event:'Home clean',time:'09:00–13:30',start:9,duration:4.5,tone:'green'},
  {id:'tue27',name:'Tue',date:'27',event:'Deep clean',time:'10:00–16:00',start:10,duration:6,tone:'neutral'},
  {id:'wed28',name:'Wed',date:'28',event:'Home clean',time:'09:00–13:30',start:9,duration:4.5,tone:'blue'},
  {id:'thu29',name:'Thu',date:'29',event:'Home clean',time:'13:30–18:00',start:13.5,duration:4.5,tone:'green'},
  {id:'fri30',name:'Fri',date:'30',event:'Fully booked',time:'09:00–18:00',start:9,duration:9,tone:'red'},
  {id:'sat31',name:'Sat',date:'31'},
  {id:'sun1',name:'Sun',date:'1'},
];
const nextDays:Day[] = [days[4],days[5],days[6],
  {id:'mon2',name:'Mon',date:'2'},
  {id:'tue3',name:'Tue',date:'3',event:'Deep clean',time:'10:00–16:00',start:10,duration:6,tone:'neutral'},
  {id:'wed4',name:'Wed',date:'4',event:'Home clean',time:'09:00–13:30',start:9,duration:4.5,tone:'green'},
  {id:'thu5',name:'Thu',date:'5',event:'Home clean',time:'13:30–18:00',start:13.5,duration:4.5,tone:'blue'},
];
const span = (start:number,duration=4.5)=>({top:`${(start-9)/9*100}%`,height:`${duration/9*100}%`});

function Check({draw=false}:{draw?:boolean}){
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><motion.path d="m5 12 4 4L19 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" initial={draw?{pathLength:0}:false} animate={{pathLength:1}} transition={{duration:.4,delay:.25}}/></svg>;
}
function Question({children}:{children:ReactNode}){
  return <motion.div layout="position" className="schedule-question" initial={{opacity:0,y:6,scale:.98}} animate={{opacity:1,y:0,scale:1}} transition={{duration:.2,ease:[.2,.8,.2,1]}}>{children}</motion.div>;
}
function Reply({children}:{children:ReactNode}){
  return <motion.div layout="position" className="schedule-reply" initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={spring}><div className="schedule-assistant"><Mark/></div><motion.div layout="size" className="schedule-reply-content" style={{borderRadius:'6px 20px 20px 20px'}} transition={spring}>{children}</motion.div></motion.div>;
}
function Thinking(){
  return <Reply><p><span className="schedule-thinking"><i/><i/><i/></span></p></Reply>;
}
function Proposal({change=false,approved}:{change?:boolean;approved:boolean}){
  return <motion.div layoutId={change?undefined:'booking'} className="schedule-proposal" style={{borderRadius:16}} initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={spring}>
    <div className="proposal-facts"><span>{change?'Monday, June 2':'Saturday, May 31'}</span><strong>13:30 <span>– 18:00</span></strong><span>Home clean · $185</span></div>
    <div className={`proposal-approval ${approved?'is-approved':''}`}>{approved?<><Check draw/><span>{change?'Change approved':'Approved'}</span></>:<><span>Ready for approval</span><span className="approval-arrow">↗</span></>}</div>
  </motion.div>;
}
function Confirmation({changed=false}:{changed?:boolean}){
  return <motion.div className="schedule-done" initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={spring}><span className="schedule-done-icon"><Check draw/></span><span>{changed?'See you Monday.':'See you Saturday.'}<small>{changed?'Saturday is free again.':'Your afternoon is booked.'}</small></span></motion.div>;
}

export function HeroSchedule(){
  const group=useId();
  const [beat,setBeat]=useState<Beat>('question');
  const [landed,setLanded]=useState(false);
  const [cycle,setCycle]=useState(0);
  const [started,setStarted]=useState(false);
  const stage=useRef<HTMLElement>(null);
  const conversation=useRef<HTMLDivElement>(null);
  const phase=story.findIndex(item=>item.beat===beat);
  const booked=phase>=5;
  const changing=phase>=6;
  const nextWeek=phase>=7;
  const changed=phase>=9;
  const bookingDay=changed?'mon2':'sat31';
  const confirmed=(phase>5&&!changed)||landed;

  useEffect(()=>{
    if(!stage.current)return;
    const observer=new IntersectionObserver(entries=>{
      if(entries.some(entry=>entry.isIntersecting)){
        setStarted(true);
        observer.disconnect();
      }
    },{threshold:.25});
    observer.observe(stage.current);
    return ()=>observer.disconnect();
  },[]);

  useEffect(()=>{
    if(!started)return;
    const timers=story.slice(1).map(({beat:next,at})=>window.setTimeout(()=>{
      if(next==='booked'||next==='rescheduled')setLanded(false);
      setBeat(next);
    },at));
    timers.push(window.setTimeout(()=>{setBeat('question');setLanded(false);setCycle(value=>value+1);},15500));
    return ()=>timers.forEach(window.clearTimeout);
  },[cycle,started]);

  useEffect(()=>{
    const animations=[conversation.current].flatMap(viewport=>{
      if(!viewport)return [];
      const top=Math.max(0,viewport.scrollHeight-viewport.clientHeight);
      if(Math.abs(top-viewport.scrollTop)<1)return [];
      return [animate(viewport.scrollTop,top,{
        duration:.3,ease:[.25,.1,.25,1],onUpdate:value=>{viewport.scrollTop=value;},
      })];
    });
    return ()=>animations.forEach(animation=>animation.stop());
  },[beat,landed,cycle]);

  return <figure ref={stage} className="hero-schedule" data-beat={beat} data-scenario={changing?'reschedule':'booking'}>
    <figcaption className="sr-only">Illustrated cleaning enquiry: Friday is full, Saturday morning does not suit the customer, and Saturday 1:30–6 pm is booked after approval. A second reviewed change moves the appointment to Monday afternoon and frees Saturday.</figcaption>
    <LayoutGroup id={group}>
      <div className="demo-workspace glass">
        <div className="docked-chat" aria-hidden="true">
          <div className="chat-preview-heading"><Mark/><span>Front desk</span></div>
          <motion.div layoutScroll ref={conversation} className="schedule-conversation">
            <div className="schedule-chat" key={cycle}>
              <Question>Could you do Friday morning?</Question>
              {phase===0&&<Thinking/>}
              {phase>=1&&<Reply><p><ReplyText text="Friday’s full. Let’s find a better fit. How does Saturday at 10 am sound?" animate/></p></Reply>}
              {phase>=2&&<Question>I can’t do Saturday morning. Is the afternoon available?</Question>}
              {phase===2&&<Thinking/>}
              {phase>=3&&<Reply><p><ReplyText text="Absolutely. Saturday at 1:30 pm gives us time for the whole clean." animate/></p>
                {(phase===3||phase===4)&&<Proposal approved={phase===4}/>}
                <AnimatePresence>{booked&&(phase>5||landed)&&<Confirmation/>}</AnimatePresence>
              </Reply>}
              {changing&&<Question>Could we move Saturday’s clean to Monday instead?</Question>}
              {phase===6&&<Thinking/>}
              {nextWeek&&<Reply><p><ReplyText text="Of course. Monday at 1:30 pm is free. Shall we move it?" animate/></p>
                {!changed&&<Proposal change approved={phase===8}/>}
                <AnimatePresence>{changed&&landed&&<Confirmation changed/>}</AnimatePresence>
              </Reply>}
            </div>
          </motion.div>
        </div>
        <div className="schedule-stage" aria-hidden="true">
          <div className="schedule-topline"><span>Your week</span><motion.span key={nextWeek?'next':'first'} initial={{opacity:0}} animate={{opacity:1}} transition={{duration:.3}}>{nextWeek?'May 30 – Jun 5':'May 26 – Jun 1'}</motion.span></div>
          <div className="schedule-grid">
            <div className="schedule-hours"><span>09:00</span><span>12:00</span><span>15:00</span><span>18:00</span></div>
            {(nextWeek?nextDays:days).map(day=>{
              const saturday=day.id==='sat31';
              const monday=day.id==='mon2';
              const candidate=(saturday&&phase>=1&&!booked)||(monday&&nextWeek&&!changed);
              const released=saturday&&changed;
              const focus=nextWeek?saturday||monday:day.id==='fri30'||saturday;
              const start=saturday&&phase<3?10:13.5;
              return <motion.div layout="position" key={day.id} className="schedule-day" data-day={day.id} data-focus={focus} initial={{opacity:0}} animate={{opacity:1}} transition={spring}>
                <div className={`schedule-date ${candidate||booked&&day.id===bookingDay?'is-chosen':''}`}><span>{day.name}</span><strong>{day.date}</strong></div>
                <div className="schedule-lane">
                  {day.event&&<motion.div className={`schedule-event event-${day.tone}`} style={{...span(day.start!,day.duration!),borderRadius:10}} initial={{opacity:0,y:12}} animate={{opacity:1,y:0,scale:day.id==='fri30'&&phase===1?1.025:1}} transition={spring}><span>{day.time}</span><strong>{day.event}</strong>{day.id==='fri30'&&<span className="event-occupied-line"/>}</motion.div>}
                  {(saturday||monday)&&<motion.div className={`schedule-opening ${released?'is-released':''}`} initial={false} animate={{...span(start),opacity:candidate||released?1:0,scale:candidate||released?1:.98}} transition={spring}><span>{start===10?'10:00':'13:30'}</span><span>{released?'Available again':'Room for you'}</span><span className="opening-plus">+</span></motion.div>}
                  {booked&&day.id===bookingDay&&<motion.div layoutId="booking" className="schedule-booking" data-booking-day={day.id} style={{...span(13.5),borderRadius:10}} initial={false} animate={{opacity:1}} transition={spring} onLayoutAnimationComplete={()=>setLanded(true)}>
                    <motion.div className="booked-contents" initial={{opacity:0}} animate={{opacity:1}} transition={{delay:.25,duration:.2}}><span>13:30–18:00</span><span className="booking-check">{confirmed&&<Check draw/>}</span><strong>Home clean</strong><span className="booking-confirmed">{confirmed?'Confirmed':''}</span></motion.div>
                  </motion.div>}
                </div>
              </motion.div>;
            })}
          </div>
        </div>
      </div>
    </LayoutGroup>
  </figure>;
}
