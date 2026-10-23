'use client';
import {useId,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {AnimatePresence,LayoutGroup,motion} from 'motion/react';
import type {SessionState} from '@/lib/api';
import {overviewDay} from '@/lib/business-overview-data';
import {ActivityDayDialog} from './activity-day-dialog';

type Day={day:string;hours:number};
const dateLabel=(day:string)=>new Intl.DateTimeFormat(undefined,{weekday:'short',month:'short',day:'numeric',timeZone:'UTC'}).format(new Date(day+'T12:00Z'));
const hours=(value:number)=>Number(value.toFixed(1));
function counts(day:ReturnType<typeof overviewDay>){
 return [`${day.appointments} ${day.appointments===1?'appointment':'appointments'}`,day.blocked?`${day.blocked} unavailable ${day.blocked===1?'block':'blocks'}`:'',day.cancelled?`${day.cancelled} cancelled`:''].filter(Boolean).join(' · ');
}

export function CalendarActivityChart({days,events,requests,zone,pending,onClear,onCalendar}:{days:Day[];events:SessionState['calendar'];requests:SessionState['requests'];zone:string;pending:boolean;onClear:(id:string)=>Promise<boolean>;onCalendar:()=>void}){
 const chart=useRef<HTMLDivElement>(null),buttons=useRef<(HTMLButtonElement|null)[]>([]);
 const [width,setWidth]=useState(720),[hovered,setHovered]=useState<number|null>(null),[focused,setFocused]=useState<number|null>(null),[opened,setOpened]=useState<number|null>(null);
 const group=useId(),gradient=useId(),titleId=useId();
 const breakdown=useMemo(()=>days.map(day=>overviewDay(events,day.day,zone)),[days,events,zone]);
 useLayoutEffect(()=>{const node=chart.current;if(!node)return;setWidth(Math.max(1,node.getBoundingClientRect().width));const observer=new ResizeObserver(entries=>setWidth(Math.max(1,entries[0].contentRect.width)));observer.observe(node);return()=>observer.disconnect();},[]);
 const max=Math.max(4,...days.map(day=>day.hours)),preview=hovered??focused;
 const points=days.map((day,index)=>({x:28+index*(width-48)/6,y:154-day.hours/max*122}));
 const line=points.map((point,index)=>`${index?'L':'M'}${point.x},${point.y}`).join(' '),area=`${line} L${width-20},154 L28,154 Z`;
 const total=days.reduce((sum,day)=>sum+day.hours,0),layoutId=(index:number)=>'activity-day-'+days[index].day;
 function indexAt(event:{clientX:number;currentTarget:HTMLDivElement}){return Math.max(0,Math.min(6,Math.round((event.clientX-event.currentTarget.getBoundingClientRect().left-28)/Math.max(1,width-48)*6)));}
 function keyboard(key:string,index:number){const next=key==='ArrowRight'?(index+1)%7:key==='ArrowLeft'?(index+6)%7:key==='Home'?0:key==='End'?6:null;if(next!==null)buttons.current[next]?.focus({preventScroll:true});return next!==null;}
 return <LayoutGroup id={group}><figure className="interactive-activity" aria-label="Calendar staff hours by day">
  <div className="activity-chart" ref={chart} onPointerMove={event=>{if(event.pointerType!=='touch')setHovered(indexAt(event));}} onPointerLeave={()=>setHovered(null)} onClick={event=>setOpened(indexAt(event))}>
   <svg viewBox={`0 0 ${width} 180`} role="img" aria-label={`${hours(total)} staff hours in this week. Choose a day below to explore appointments.`}>
    <defs><linearGradient id={gradient} x1="0" y1="0" x2="0" y2="1"><stop stopColor="#1967d2" stopOpacity=".24"/><stop offset="1" stopColor="#1967d2" stopOpacity="0"/></linearGradient></defs>
    {[32,93,154].map((y,index)=><g key={y}><path d={`M28 ${y}H${width-20}`} stroke="#b8cde644" strokeDasharray={index===2?undefined:'3 5'}/><text x="8" y={y+4} fontSize="10" fill="#78899f">{hours(max*(1-index/2))}</text></g>)}
    <motion.path d={area} fill={`url(#${gradient})`} initial={{opacity:0}} animate={{opacity:1}} transition={{duration:1}}/>
    {preview!==null&&opened===null&&<path d={`M${points[preview].x} 24V154`} stroke="#1967d2" strokeOpacity=".35" strokeDasharray="3 4"/>}
    <motion.path d={line} fill="none" stroke="#1967d2" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" initial={{pathLength:0}} animate={{pathLength:1}} transition={{duration:1.1,ease:[.16,1,.3,1]}}/>
    {points.map((point,index)=><circle key={index} cx={point.x} cy={point.y} r={preview===index?6:3.5} fill={preview===index?'#1967d2':'#fff'} stroke="#1967d2" strokeWidth="2"/>)}
   </svg>
   {preview!==null&&opened===null&&<div className="activity-tooltip" role="tooltip" style={{left:Math.max(0,Math.min(width-172,points[preview].x-86))}}><strong>{dateLabel(days[preview].day)}</strong><span>{hours(days[preview].hours)} staff hours</span><small>{counts(breakdown[preview])}</small></div>}
  </div>
  <figcaption className="activity-days" onKeyDown={event=>{if(event.key==='Escape'){setHovered(null);setFocused(null);}}}>{days.map((day,index)=><motion.button type="button" key={day.day} ref={node=>{buttons.current[index]=node;}} layoutId={layoutId(index)} style={{left:points[index].x,borderRadius:12}} aria-haspopup="dialog" aria-expanded={opened===index} aria-label={`${dateLabel(day.day)}: ${hours(day.hours)} staff hours, ${counts(breakdown[index])}. View day.`} data-active={preview===index||undefined} onPointerEnter={event=>{if(event.pointerType!=='touch')setHovered(index);}} onPointerLeave={()=>setHovered(null)} onFocus={()=>setFocused(index)} onBlur={()=>setFocused(null)} onKeyDown={event=>{if(keyboard(event.key,index))event.preventDefault();}} onClick={()=>setOpened(index)}><span>{new Intl.DateTimeFormat(undefined,{weekday:'short',timeZone:'UTC'}).format(new Date(day.day+'T12:00Z'))}</span><strong>{hours(day.hours)}<small> h</small></strong></motion.button>)}</figcaption>
  <p className="activity-chart-hint">Choose a day to see its appointments.</p>
 </figure><AnimatePresence>{opened!==null&&<ActivityDayDialog key={days[opened].day} day={days[opened]} data={breakdown[opened]} requests={requests} zone={zone} layoutId={layoutId(opened)} titleId={titleId} opener={buttons.current[opened]} onClose={()=>setOpened(null)} onCalendar={onCalendar} pending={pending} onClear={onClear}/>}</AnimatePresence></LayoutGroup>;
}
