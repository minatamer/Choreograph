'use client';
import {useEffect,useId,useRef,useState} from 'react';
import {AnimatePresence,motion} from 'motion/react';
import {APPOINTMENT_STATUS,type CalendarStatus} from '@/lib/appointment-status';
const statuses=[{status:'confirmed',label:'Upcoming'},{status:'completed',label:'Completed'},{status:'cancelled',label:'Cancelled'}] as const;
export function CalendarFilters({visible,onChange}:{visible:ReadonlySet<CalendarStatus>;onChange:(value:Set<CalendarStatus>)=>void}){
 const [open,setOpen]=useState(false),id=useId();const root=useRef<HTMLDivElement>(null),trigger=useRef<HTMLButtonElement>(null),panel=useRef<HTMLDivElement>(null);
 useEffect(()=>{if(!open)return;panel.current?.querySelector<HTMLInputElement>('input')?.focus({preventScroll:true});
  const outside=(event:PointerEvent)=>{if(!root.current?.contains(event.target as Node))setOpen(false);};
  const escape=(event:KeyboardEvent)=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();setOpen(false);trigger.current?.focus({preventScroll:true});}};
  document.addEventListener('pointerdown',outside);document.addEventListener('keydown',escape);
  return()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape);};
 },[open]);
 return <div ref={root} className="calendar-filter-control" onBlur={event=>{if(event.relatedTarget&&!event.currentTarget.contains(event.relatedTarget as Node))setOpen(false);}}>
  <button ref={trigger} type="button" className="glass-control filter-trigger" aria-label="Filter appointments" aria-haspopup="dialog" aria-expanded={open} aria-controls={id} onClick={()=>setOpen(value=>!value)}><svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M4 5h16l-6 7v6l-4 2v-8L4 5Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/></svg>Filters<span>{visible.size===3?'All':visible.size}</span><span aria-hidden="true">⌄</span></button>
  <AnimatePresence>{open&&<motion.div ref={panel} id={id} role="dialog" aria-label="Appointment filters" className="glass-menu calendar-filter-menu" initial={{opacity:0,y:-5,scale:.97}} animate={{opacity:1,y:0,scale:1}} exit={{opacity:0,y:-3}} transition={{duration:.16}}><header><strong>Show appointments</strong><button type="button" onClick={()=>onChange(new Set(statuses.map(item=>item.status)))}>Show all</button></header>{statuses.map(({status,label})=><label key={status} className={status}><span className="filter-status" aria-hidden="true">{APPOINTMENT_STATUS[status].symbol}</span><span>{label}</span><input type="checkbox" checked={visible.has(status)} onChange={()=>{const next=new Set(visible);if(next.has(status))next.delete(status);else next.add(status);onChange(next);}}/></label>)}</motion.div>}</AnimatePresence>
 </div>;
}
