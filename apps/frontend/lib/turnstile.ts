export type VerificationAction='workspace'|'assistant'|'documents';
export interface TurnstileOptions{
 sitekey:string;action:VerificationAction;cData:string;size:'compact';theme:'light';language:'en';
 appearance:'interaction-only';retry:'never';'refresh-expired':'never';'refresh-timeout':'never';'response-field':false;
 callback:(token:string)=>void;'before-interactive-callback':()=>void;'error-callback':()=>boolean;
 'expired-callback':()=>void;'timeout-callback':()=>void;'unsupported-callback':()=>void;
}
export interface Turnstile{render:(container:HTMLElement,options:TurnstileOptions)=>string;remove:(id:string)=>void}
declare global{interface Window{turnstile?:Turnstile}}

let scriptPromise:Promise<Turnstile>|null=null;
export function loadTurnstile():Promise<Turnstile>{
 if(window.turnstile)return Promise.resolve(window.turnstile);
 if(scriptPromise)return scriptPromise;
 scriptPromise=new Promise<Turnstile>((resolve,reject)=>{
  const script=document.createElement('script');let settled=false;
  const finish=(problem?:Error)=>{if(settled)return;settled=true;clearTimeout(timer);script.onload=null;script.onerror=null;
   if(problem){script.remove();reject(problem);}else if(window.turnstile)resolve(window.turnstile);else{script.remove();reject(Error('VERIFICATION_UNAVAILABLE'));}};
  const timer=setTimeout(()=>finish(Error('VERIFICATION_TIMEOUT')),12_000);
  script.src='https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';script.async=true;script.defer=true;
  script.onload=()=>finish();script.onerror=()=>finish(Error('VERIFICATION_UNAVAILABLE'));document.head.appendChild(script);
 }).catch(error=>{scriptPromise=null;throw error;});
 return scriptPromise;
}

/** Fresh operation-owned widget. Late/synchronous callbacks cannot escape cleanup. */
export function mountVerification(api:Turnstile,container:HTMLElement,siteKey:string,action:VerificationAction,binding:string,
 complete:(token?:string)=>void,interact:()=>void){
 let active=true,widget:string|null=null;
 const finish=(token?:string)=>{if(!active)return;active=false;complete(token);};
 try{widget=api.render(container,{sitekey:siteKey,action,cData:binding,size:'compact',theme:'light',language:'en',
  appearance:'interaction-only',retry:'never','refresh-expired':'never','refresh-timeout':'never','response-field':false,
  callback:finish,'before-interactive-callback':()=>{if(active)interact();},
  'error-callback':()=>{finish();return true;},'expired-callback':()=>finish(),
  'timeout-callback':()=>finish(),'unsupported-callback':()=>finish()});
 }catch{finish();}
 return()=>{active=false;if(widget===null)return;const owned=widget;widget=null;try{api.remove(owned);}catch{/* Vendor cleanup cannot prevent cancellation. */}};
}
