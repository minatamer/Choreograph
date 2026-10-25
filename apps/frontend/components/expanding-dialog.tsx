'use client';
import {useEffect,useLayoutEffect,useRef,useState,type ReactNode} from 'react';
import {createPortal} from 'react-dom';
import {motion} from 'motion/react';
import {useDialogFocus} from './use-dialog-focus';

export const cardSpring={type:'spring' as const,stiffness:250,damping:29,mass:.9};

export function ExpandingDialog({layoutId,className,children,onClose,opener,fallbackFocus,titleId,label}:{layoutId:string;className:string;children:ReactNode;onClose:()=>void;opener:HTMLElement|null;fallbackFocus?:HTMLElement|null;titleId?:string;label?:string}){
 const panel=useRef<HTMLElement>(null);
 const [layoutRevision,setLayoutRevision]=useState(0);
 useLayoutEffect(()=>{
  const node=panel.current;if(!node)return;
  let width=node.clientWidth,height=node.clientHeight;
  const observer=new ResizeObserver(()=>{
   if(node.clientWidth===width&&node.clientHeight===height)return;
   width=node.clientWidth;height=node.clientHeight;setLayoutRevision(value=>value+1);
  });
  observer.observe(node);return()=>observer.disconnect();
 },[]);
 useDialogFocus(panel,onClose);
 useEffect(()=>{
  const roots=[...document.querySelectorAll<HTMLElement>('[data-demo-workspace-root],.app-header,main,[role="dialog"]')].filter(node=>node!==panel.current&&!panel.current?.contains(node));
  const previous=roots.map(node=>({node,inert:node.inert}));
  const html=document.documentElement,body=document.body;
  const htmlOverflow=html.style.overflow,bodyOverflow=body.style.overflow,padding=body.style.paddingRight;
  const gutter=innerWidth-html.clientWidth;
  if(gutter>0)body.style.paddingRight=`${parseFloat(getComputedStyle(body).paddingRight)+gutter}px`;
  html.style.overflow='hidden';body.style.overflow='hidden';roots.forEach(node=>{node.inert=true;});
  return()=>{
   previous.forEach(({node,inert})=>{node.inert=inert;});
   html.style.overflow=htmlOverflow;body.style.overflow=bodyOverflow;body.style.paddingRight=padding;
   // Restore after the focus hook, once the underlying layer is interactive.
   const target=opener?.isConnected?opener:fallbackFocus?.isConnected?fallbackFocus:document.querySelector<HTMLElement>('#enquiry,.workspace-reset');
   target?.focus({preventScroll:true});
  };
 },[opener,fallbackFocus]);
 return createPortal(<motion.div layoutRoot className="expanding-dialog-layer">
  <motion.div className="expanding-dialog-backdrop" aria-hidden="true" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} transition={{duration:.24}} onClick={onClose}/>
  <motion.section layoutId={layoutId} layoutDependency={layoutRevision} className={`expanding-dialog ${className}`} style={{borderRadius:28}} transition={cardSpring} role="dialog" aria-modal="true" aria-labelledby={titleId} aria-label={label} tabIndex={-1} ref={panel}>{children}</motion.section>
 </motion.div>,document.body);
}
