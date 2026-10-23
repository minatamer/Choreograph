'use client';
import {useEffect,useRef} from 'react';
export function ReplyText({text,animate=false}:{text:string;animate?:boolean}){
 const element=useRef<HTMLSpanElement>(null);
 useEffect(()=>{
  const node=element.current;if(!node||!animate)return;
  const letters=Array.from(new Intl.Segmenter(undefined,{granularity:'grapheme'}).segment(text),part=>part.segment);
  const interval=Math.min(9,1600/Math.max(1,letters.length));let frame=0;let start:number|undefined;let last=0;
  node.textContent='';
  const tick=(now:number)=>{start??=now;const count=Math.min(letters.length,Math.floor((now-start)/interval)+1);if(count!==last){node.textContent=letters.slice(0,count).join('');last=count;}if(count<letters.length)frame=requestAnimationFrame(tick);};
  frame=requestAnimationFrame(tick);return()=>cancelAnimationFrame(frame);
 },[text,animate]);
 if(!animate)return <>{text}</>;
 return <span className="typed-reply"><span ref={element} aria-hidden="true"/><span className="reply-measure" aria-hidden="true">{text}</span><span className="sr-only">{text}</span></span>;
}
