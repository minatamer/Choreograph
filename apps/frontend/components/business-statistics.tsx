'use client';

import {useEffect,useRef} from 'react';
import {animate,motion,useInView} from 'motion/react';
import {ScrollReveal} from './landing-motion';

function CountUp({value}:{value:number}){
  const output=useRef<HTMLSpanElement>(null);
  const entered=useInView(output,{once:true,amount:.6});
  useEffect(()=>{
    if(!entered||!output.current)return;
    let previous=-1;
    const animation=animate(0,value,{duration:1.8,ease:[.16,1,.3,1],onUpdate:latest=>{const rounded=Math.round(latest);if(rounded!==previous&&output.current){output.current.textContent=String(rounded);previous=rounded;}},onComplete:()=>{if(output.current)output.current.textContent=String(value);}});
    return()=>animation.stop();
  },[entered,value]);
  return <span ref={output} className="count-number" data-count-target={value}>{value}</span>;
}

function FindingVisual({index}:{index:number}){
  if(index===0)return <motion.div className="stat-visual stat-people" aria-hidden="true" initial="hidden" whileInView="visible" viewport={{once:true,amount:.5}}>
    <div className="stat-dot-matrix">{Array.from({length:10},(_,row)=><motion.div key={row} variants={{hidden:{opacity:0,y:6},visible:{opacity:1,y:0,transition:{delay:row*.045,duration:.4}}}}>{Array.from({length:10},(_,column)=><i key={column} className={row*10+column<72?'is-counted':''}/>)}</motion.div>)}</div><span>Prefer the first responder</span>
  </motion.div>;
  if(index===1)return <motion.div className="stat-visual stat-ring" aria-hidden="true" initial="hidden" whileInView="visible" viewport={{once:true,amount:.5}}><svg viewBox="0 0 180 180" fill="none"><circle cx="90" cy="90" r="64" stroke="#dce8e3" strokeWidth="12"/><motion.circle className="stat-ring-progress" cx="90" cy="90" r="64" stroke="#2e8b57" strokeWidth="12" strokeLinecap="round" variants={{hidden:{pathLength:0},visible:{pathLength:.95,transition:{duration:1.5,ease:[.16,1,.3,1]}}}}/><rect x="68" y="66" width="44" height="48" rx="9" stroke="#42755a" strokeWidth="2"/><path d="M68 80h44M80 61v11M100 61v11" stroke="#42755a" strokeWidth="2" strokeLinecap="round"/><motion.path d="m80 96 7 7 14-16" stroke="#2e8b57" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" variants={{hidden:{pathLength:0},visible:{pathLength:1,transition:{delay:.8,duration:.5}}}}/></svg><span>Client-scheduled appointments</span></motion.div>;
  return <motion.figure className="stat-visual stat-comparison" role="img" aria-label="Relative issues resolved per hour: without AI assistance, index 100; with AI assistance, index 115." initial="hidden" whileInView="visible" viewport={{once:true,amount:.5}}>
    <div className="stat-bar-row"><span>Without AI<span>100</span></span><div className="stat-bar-track"><motion.i style={{width:`${100/115*100}%`}} variants={{hidden:{scaleX:0},visible:{scaleX:1,transition:{duration:1.1,ease:[.16,1,.3,1]}}}}/></div></div>
    <div className="stat-bar-row is-assisted"><span>With AI<span>115</span></span><div className="stat-bar-track"><motion.i variants={{hidden:{scaleX:0},visible:{scaleX:1,transition:{delay:.16,duration:1.25,ease:[.16,1,.3,1]}}}}/></div></div>
    <figcaption>Index · without AI = 100</figcaption>
  </motion.figure>;
}

const findings=[
  {
    value:'72',suffix:'%',title:'Be there first.',
    description:'of U.S. consumers say they’re likely to choose the business that responds first.',
    source:'Moneypenny',year:'2026',
    href:'https://www.moneypenny.com/us/resources/news/moneypenny-research-reveals-the-customer-caller-experience-gap',
    sourceLabel:'Read Moneypenny’s 2026 U.S. consumer survey',
  },
  {
    value:'95',suffix:'%+',title:'Let customers choose.',
    description:'of appointments were scheduled directly by clients in SimplyBook.me’s 2024 platform data.',
    source:'SimplyBook.me',year:'2025',
    href:'https://simplybook.me/en/resources/globalstateofbookings2025',
    sourceLabel:'Read SimplyBook.me’s 2025 Global State of Bookings report',
  },
  {
    value:'15',suffix:'%',prefix:'+',title:'Help your team do more.',
    description:'more issues resolved per hour with AI assistance, in a study of 5,172 customer-support agents.',
    source:'Quarterly Journal of Economics',year:'2025',
    href:'https://doi.org/10.1093/qje/qjae044',
    sourceLabel:'Read the 2025 Generative AI at Work study in the Quarterly Journal of Economics',
  },
];

export function BusinessStatistics(){
  return <section className="business-evidence" aria-labelledby="business-evidence-title">
    <ScrollReveal className="business-evidence-intro">
      <span className="eyebrow blue-text">Why it matters</span>
      <h2 id="business-evidence-title">Make the first reply count.</h2>
      <p>Customers want a quick answer and an easy way to book. Give your team room to deliver both.</p>
    </ScrollReveal>
    <div className="business-metrics">
      {findings.map((finding,index)=><ScrollReveal as="article" travel={48+index*18} className={`business-stat metric-${index}`} key={finding.source}>
        <div className="stat-summary">
          <p className="business-stat-value"><span className="sr-only">{finding.prefix}{finding.value}{finding.suffix}</span><span className="stat-count-display" aria-hidden="true">{finding.prefix&&<span className="business-stat-prefix">{finding.prefix}</span>}<CountUp value={Number(finding.value)}/><span className="business-stat-suffix">{finding.suffix}</span></span></p>
          <FindingVisual index={index}/>
        </div>
        <h3>{finding.title}</h3>
        <p className="business-stat-description">{finding.description}</p>
        <a className="business-stat-source" href={finding.href} target="_blank" rel="noopener noreferrer" aria-label={`${finding.sourceLabel} (opens in a new tab)`}>
          <span>{finding.source} · {finding.year}</span><span aria-hidden="true">↗</span>
        </a>
      </ScrollReveal>)}
    </div>
    <p className="business-evidence-note">Published research across consumer surveys, booking-platform data and customer support.</p>
  </section>;
}
