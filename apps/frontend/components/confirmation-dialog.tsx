'use client';
import {useEffect,useId,useRef,useState,type ReactNode} from 'react';
import {ExpandingDialog} from './expanding-dialog';
import {Button} from './ui';

export function ConfirmationDialog({layoutId,title,eyebrow,confirmLabel,cancelLabel='Cancel',children,pending=false,opener,fallbackFocus,onClose,onConfirm,errorMessage='We couldn’t confirm this change. Close this dialog and refresh to check the latest status.'}:{layoutId:string;title:string;eyebrow?:string;confirmLabel:string;cancelLabel?:string;children:ReactNode;pending?:boolean;opener:HTMLElement|null;fallbackFocus?:HTMLElement|null;onClose:()=>void;onConfirm:()=>Promise<boolean>;errorMessage?:string}){
 const titleId=useId();
 const [submitting,setSubmitting]=useState(false),[failed,setFailed]=useState(false);
 const lock=useRef(false),sequence=useRef(0);
 useEffect(()=>()=>{sequence.current++;},[]);
 const busy=pending||submitting;
 function close(){if(!lock.current&&!pending)onClose();}
 async function submit(){
  if(busy||failed||lock.current)return;
  const id=++sequence.current;lock.current=true;setSubmitting(true);let succeeded=false;
  try{
   const accepted=await onConfirm();if(id!==sequence.current)return;
   if(accepted){onClose();succeeded=true;}else setFailed(true);
  }catch{if(id===sequence.current)setFailed(true);}
  finally{if(id===sequence.current&&!succeeded){lock.current=false;setSubmitting(false);}}
 }
 return <ExpandingDialog layoutId={layoutId} className="booking-management-dialog confirmation-dialog" titleId={titleId} label={title} opener={opener} fallbackFocus={fallbackFocus} onClose={close}>
  <header><div>{eyebrow&&<span className="eyebrow blue-text">{eyebrow}</span>}<h2 id={titleId}>{title}</h2></div><Button kind="quiet" disabled={busy} onClick={close}>Close</Button></header>
  {children}
  {failed&&<p className="confirmation-dialog-error" role="alert">{errorMessage}</p>}
  <footer><Button kind="secondary" disabled={busy} onClick={close}>{cancelLabel}</Button><Button busy={submitting} disabled={busy||failed} onClick={()=>void submit()}>{confirmLabel}</Button></footer>
 </ExpandingDialog>;
}
