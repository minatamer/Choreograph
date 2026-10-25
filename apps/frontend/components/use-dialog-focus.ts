'use client';
import {useEffect,useRef,type RefObject} from 'react';

export function useDialogFocus(panel:RefObject<HTMLElement|null>,onClose:()=>void){
 const close=useRef(onClose);useEffect(()=>{close.current=onClose;},[onClose]);
 useEffect(()=>{
  const previous=document.activeElement as HTMLElement|null;
  (panel.current?.querySelector<HTMLElement>('button:not(:disabled)')??panel.current)?.focus({preventScroll:true});
  const key=(event:KeyboardEvent)=>{
   if(event.defaultPrevented||panel.current?.closest('[inert]'))return;
   if(event.key==='Escape'){event.preventDefault();event.stopPropagation();close.current();}
   if(event.key!=='Tab')return;
   const nodes=panel.current?.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),[tabindex="0"]');
   if(!nodes?.length){event.preventDefault();panel.current?.focus({preventScroll:true});return;}
   const first=nodes[0],last=nodes[nodes.length-1];
   if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
   else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
  };
  document.addEventListener('keydown',key);
  return()=>{document.removeEventListener('keydown',key);if(previous?.isConnected&&!previous.matches(':disabled'))previous.focus({preventScroll:true});};
 },[panel]);
}
