'use client';
import {Mark} from './ui';
import {ViewSwitch} from './view-switch';
export function ResetDemo({onReset,disabled=false,quiet=false}:{onReset:()=>void;disabled?:boolean;quiet?:boolean}){
 return <button type="button" disabled={disabled} className={`workspace-reset ${quiet?'workspace-reset-quiet':'glass-control'}`} aria-label="Reset demo" title="Reset demo" onClick={()=>{if(window.confirm('Start a fresh demo? Your current workspace will end.'))onReset();}}><svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M3.5 10a8.5 8.5 0 1 1 2 8.3M3.5 4.5V10H9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg><span className="workspace-reset-label">Reset demo</span></button>;
}
export function PoweredBy({compact=false}:{compact?:boolean}){
 return <a className="powered-by" href="/" aria-label="Powered by Choreograph" title="Powered by Choreograph"><span className={compact?'sr-only':''}>Powered by</span><Mark/><span className={compact?'sr-only':''}>choreograph</span></a>;
}
export function CustomerFooter({onReset,onPerspective,ready}:{onReset:()=>void;onPerspective:(business:boolean)=>void;ready:boolean}){
 return <footer className="customer-toolbar"><PoweredBy/><div className="workspace-controls"><ResetDemo onReset={onReset} disabled={!ready}/><ViewSwitch business={false} onChange={onPerspective}/></div></footer>;
}
