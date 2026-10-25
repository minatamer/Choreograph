'use client';
import {useRef,useState} from 'react';
import {AnimatePresence} from 'motion/react';
import {ConfirmationDialog} from './confirmation-dialog';
import {Mark} from './ui';
import {ViewSwitch} from './view-switch';
export function ResetDemo({onReset,disabled=false,quiet=false,onDialogOpen}:{onReset:()=>Promise<boolean>;disabled?:boolean;quiet?:boolean;onDialogOpen?:()=>HTMLElement|null}){
 const [open,setOpen]=useState(false);const opener=useRef<HTMLElement|null>(null);
 return <><button type="button" disabled={disabled} className={`workspace-reset ${quiet?'workspace-reset-quiet':'glass-control'}`} aria-label="Reset demo" title="Reset demo" onClick={event=>{opener.current=onDialogOpen?.()??event.currentTarget;setOpen(true);}}><svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M3.5 10a8.5 8.5 0 1 1 2 8.3M3.5 4.5V10H9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg><span className="workspace-reset-label">Reset demo</span></button><AnimatePresence>{open&&<ConfirmationDialog layoutId="reset-demo-confirmation" title="Start a fresh demo?" eyebrow="Start again" confirmLabel="Reset demo" cancelLabel="Keep this demo" pending={disabled} opener={opener.current} onClose={()=>setOpen(false)} onConfirm={onReset} errorMessage="We couldn’t confirm the reset. Close this dialog and refresh to check your demo before trying again."><p>Your current workspace will end. You’ll return to choose whether to connect HubSpot.</p></ConfirmationDialog>}</AnimatePresence></>;
}
export function PoweredBy({compact=false}:{compact?:boolean}){
 return <a className="powered-by" href="/" aria-label="Powered by Choreograph" title="Powered by Choreograph"><span className={compact?'sr-only':''}>Powered by</span><Mark/><span className={compact?'sr-only':''}>choreograph</span></a>;
}
export function CustomerFooter({onReset,onPerspective,ready}:{onReset:()=>Promise<boolean>;onPerspective:(business:boolean)=>void;ready:boolean}){
 return <footer className="customer-toolbar"><PoweredBy/><div className="workspace-controls"><ResetDemo onReset={onReset} disabled={!ready}/><ViewSwitch business={false} onChange={onPerspective}/></div></footer>;
}
