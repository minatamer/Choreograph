'use client';
import {createContext,useCallback,useContext,useEffect,useRef,useState,type ReactNode} from 'react';
import {createPortal} from 'react-dom';
import {api,ApiError,type VerificationConfig} from '@/lib/api';
import {loadTurnstile,mountVerification,type VerificationAction} from '@/lib/turnstile';
import {Button,Mark} from './ui';

export type Verify=(action:VerificationAction,binding:string,signal:AbortSignal,recover?:boolean)=>Promise<string|undefined>;
type Pending={id:string;siteKey:string;action:VerificationAction;binding:string;recover:boolean;finish:(token?:string)=>void};
const VerificationContext=createContext<Verify|undefined>(undefined);
export const useVerification=()=>useContext(VerificationContext);

export function VerificationProvider({children}:{children:ReactNode}){
 const [pending,setPending]=useState<Pending|null>(null);const current=useRef<Pending|null>(null);
 const verify=useCallback<Verify>(async(action,binding,signal,recover=false)=>{
  const config=await api<VerificationConfig>('verification',{signal});
  if(signal.aborted)throw new DOMException('Cancelled','AbortError');
  if(!config.required)return undefined;
  if(!config.enabled||!config.site_key)throw new ApiError('VERIFICATION_UNAVAILABLE','The human check is unavailable. Please try again later.',503);
  current.current?.finish();
  return new Promise<string>((resolve,reject)=>{
   const request:Pending={id:crypto.randomUUID(),siteKey:config.site_key!,action,binding,recover,finish:(token)=>{
    if(current.current!==request)return;current.current=null;signal.removeEventListener('abort',cancel);setPending(null);
    if(token)resolve(token);else reject(new ApiError('VERIFICATION_CANCELLED','The check was cancelled. Your message is still here.',409));
   }};
   const cancel=()=>request.finish();current.current=request;setPending(request);signal.addEventListener('abort',cancel,{once:true});
   if(signal.aborted)cancel();
  });
 },[]);
 useEffect(()=>()=>current.current?.finish(),[]);
 return <VerificationContext.Provider value={verify}>{children}{pending&&<VerificationDialog key={pending.id} pending={pending}/>}</VerificationContext.Provider>;
}

function VerificationDialog({pending}:{pending:Pending}){
 const panel=useRef<HTMLDialogElement>(null),widget=useRef<HTMLDivElement>(null);
 const [attempt,setAttempt]=useState(0),[interactive,setInteractive]=useState(false),[problem,setProblem]=useState(pending.recover);
 useEffect(()=>{const node=panel.current,previous=document.activeElement as HTMLElement|null;
  return()=>{node?.close();requestAnimationFrame(()=>{if(previous?.isConnected&&!previous.matches(':disabled'))previous.focus({preventScroll:true});else document.querySelector<HTMLTextAreaElement>('#enquiry:not(:disabled)')?.focus({preventScroll:true});});};
 },[]);
 useEffect(()=>{
  if(!interactive&&!problem)return;const node=panel.current;if(node&&!node.open)node.showModal();
 },[interactive,problem]);
 useEffect(()=>{
  if(problem)return;let active=true;let cleanup:(()=>void)|undefined;
  const timer=setTimeout(()=>{if(active)setProblem(true);},30_000);
  void loadTurnstile().then(provider=>{if(!active||!widget.current)return;
   cleanup=mountVerification(provider,widget.current,pending.siteKey,pending.action,pending.binding,
    token=>{if(!active)return;clearTimeout(timer);if(token)pending.finish(token);else setProblem(true);},
    ()=>{if(active){clearTimeout(timer);setInteractive(true);}});
  }).catch(()=>{if(active){clearTimeout(timer);setProblem(true);}});
  return()=>{active=false;clearTimeout(timer);cleanup?.();};
 },[pending,attempt,problem]);
 return createPortal(<dialog ref={panel} className="verification-dialog" aria-hidden={!interactive&&!problem} aria-labelledby="human-check-title" aria-describedby="human-check-description" onCancel={event=>{event.preventDefault();pending.finish();}}>
  <div className="verification-heading" hidden={!interactive&&!problem}><span className="assistant-orb" aria-hidden="true"><Mark/></span><h2 id="human-check-title">One quick check.</h2><p id="human-check-description">{problem?'We couldn’t finish the check. Try again to continue.':'Please confirm you’re human to continue.'} Your message and booking details stay here.</p></div>
  <div className="verification-widget" ref={widget}/>
  <div className="verification-actions" hidden={!interactive&&!problem}>{problem&&<Button onClick={()=>{setInteractive(true);setProblem(false);setAttempt(value=>value+1);}}>Try again</Button>}<Button kind="secondary" onClick={()=>pending.finish()}>Cancel</Button></div>
 </dialog>,document.body);
}
