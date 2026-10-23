'use client';

import {useId} from 'react';
import {LayoutGroup, motion} from 'motion/react';

export function ViewSwitch({business,onChange}:{business:boolean;onChange:(business:boolean)=>void}) {
  const group=useId();
  return <LayoutGroup id={group}><div className="view-switch" role="group" aria-label="Demo perspective">
    {[{value:false,label:'Customer view'},{value:true,label:'Business view'}].map(view=><button key={view.label} type="button" aria-pressed={business===view.value} onClick={()=>onChange(view.value)}>
      {business===view.value&&<motion.span className="view-switch-selection" layoutId="perspective" transition={{type:'spring',stiffness:380,damping:32}}/>}
      <span>{view.label}</span>
    </button>)}
  </div></LayoutGroup>;
}
