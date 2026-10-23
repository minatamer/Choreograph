'use client';

import {useId} from 'react';
import {LayoutGroup, motion} from 'motion/react';

export function ViewSwitch({business,onChange,compact=false}:{business:boolean;onChange:(business:boolean)=>void;compact?:boolean}) {
  const group=useId();
  return <LayoutGroup id={group}><div className={`view-switch ${compact?'compact':''}`} role="group" aria-label="Demo perspective">
    {[{value:false,label:'Customer view'},{value:true,label:'Business view'}].map(view=><button key={view.label} type="button" aria-label={view.label} title={compact?view.label:undefined} aria-pressed={business===view.value} onClick={()=>onChange(view.value)}>
      {business===view.value&&<motion.span className="view-switch-selection" layoutId="perspective" transition={{type:'spring',stiffness:380,damping:32}}/>}
      {compact&&<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none"><path d={view.value?'M4 4h6v6H4V4Zm10 0h6v6h-6V4ZM4 14h6v6H4v-6Zm10 0h6v6h-6v-6Z':'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM4 21v-2a8 8 0 0 1 16 0v2'} stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/></svg>}{!compact&&<span className="view-switch-label">{view.label}</span>}
    </button>)}
  </div></LayoutGroup>;
}
