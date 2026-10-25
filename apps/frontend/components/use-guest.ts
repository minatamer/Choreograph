'use client';
import {useCallback,useEffect,useRef,useState} from 'react';
import {api,ApiError,type SessionState,type Mutation} from '@/lib/api';
import type {Verify} from './verification-provider';
import type {VerificationAction} from '@/lib/turnstile';
type Operation={path:string;method:string;body:unknown;key:string;csrf:string;chatText?:string};
export function useGuest(autoInitialize=true,verify?:Verify){
  const [state,setState]=useState<SessionState|null>(null);
  const [pending,setPending]=useState(false);
  const [error,setError]=useState<{code:string;message:string}|null>(null);
  const [needsZone,setNeedsZone]=useState(false);
  const serial=useRef(0);const active=useRef<AbortController|null>(null);const last=useRef<Operation|null>(null);
  const polls=useRef({key:'',count:0});
  const showFailure=useCallback((problem:unknown)=>{
    const failure=problem instanceof ApiError?problem:{code:'NETWORK_UNAVAILABLE',message:'Couldn’t reach the front desk. Try again.'};
    if(['SESSION_EXPIRED','SESSION_REQUIRED'].includes(failure.code)){last.current=null;setState(null);}
    // A confirmed provider failure cannot replay an uncertain paid attempt.
    // Refresh preserves the composer's text; another Send is a new action.
    if(/^(AI_|ASSISTANT_|ANSWER_|EMBEDDING_)/.test(failure.code))last.current=null;
    setError(failure);
    return failure;
  },[]);
  useEffect(()=>{
    if(!state||pending)return;
    const waiting=state.requests.some(row=>['pending','retrying','reconciling','processing'].includes(row.crm_state))||state.connection?.state==='finishing';
    const key=state.workspace_id+':'+state.requests.map(row=>row.id+':'+row.revision).join(',')+':'+state.connection?.state;
    if(polls.current.key!==key)polls.current={key,count:0};
    if(!waiting)return;
    if(polls.current.count>=60){last.current=null;setError({code:'SYNC_PENDING',message:'Sync is still pending. Refresh to check again.'});return;}
    const controller=new AbortController();const tag=serial.current;const workspace=state.workspace_id;const generation=state.generation;
    let timer:ReturnType<typeof setTimeout>;
    async function poll(){
      polls.current.count++;
      try{
        const next=await api<SessionState>('session',{signal:controller.signal});
        if(controller.signal.aborted||tag!==serial.current)return;
        if(next.workspace_id!==workspace||next.generation!==generation){last.current=null;setState(null);setError({code:'SESSION_CHANGED',message:'This demo changed. Refresh before continuing.'});return;}
        setError(null);setState(next);
      }catch(problem){
        if(controller.signal.aborted||tag!==serial.current)return;
        last.current=null;
        const failure=showFailure(problem);
        if(['SESSION_EXPIRED','SESSION_REQUIRED'].includes(failure.code))return;
        if(polls.current.count<60)timer=setTimeout(()=>void poll(),2000);
      }
    }
    timer=setTimeout(()=>void poll(),2000);
    return()=>{clearTimeout(timer);controller.abort();};
  },[state,pending,showFailure]);
  const initialize=useCallback(async(zone?:string,restart=false)=>{
    active.current?.abort();const controller=new AbortController();active.current=controller;const tag=++serial.current;
    polls.current={key:'',count:0};last.current=null;
    setPending(true);setError(null);
    try{
      let detected=zone;
      try{detected??=Intl.DateTimeFormat().resolvedOptions().timeZone;}catch{}
      let value:SessionState;
      if(detected){
        let restored:SessionState|undefined;
        if(!restart){try{restored=await api<SessionState>('session',{signal:controller.signal});}
          catch(problem){if(!(problem instanceof ApiError)||problem.status!==401)throw problem;}}
        if(restored)value=restored;
        else{const key=crypto.randomUUID();let proof=await verify?.('workspace',key,controller.signal);
          const options={method:'POST',body:{timezone:detected,restart},key,signal:controller.signal};
          try{value=await api<SessionState>('session',{...options,proof});}
          catch(problem){
            if(!(problem instanceof ApiError)||problem.code!=='VERIFICATION_REQUIRED'||!verify)throw problem;
            proof=await verify('workspace',key,controller.signal,true);
            value=await api<SessionState>('session',{...options,proof});
          }}
      }else{
        try{value=await api<SessionState>('session',{signal:controller.signal});}
        catch(error){if(error instanceof ApiError&&error.status===401){setState(null);last.current=null;setNeedsZone(true);return;}throw error;}
      }
      if(tag===serial.current){setState(value);setNeedsZone(false);}
    }catch(error){if(tag===serial.current&&!controller.signal.aborted)showFailure(error);}
    finally{if(tag===serial.current)setPending(false);}
  },[showFailure,verify]);
  useEffect(()=>{if(autoInitialize)void initialize();return()=>{active.current?.abort();serial.current++;};},[autoInitialize,initialize]);
  const perform=useCallback(async(operation:Operation)=>{
    active.current?.abort();const controller=new AbortController();active.current=controller;const tag=++serial.current;
    last.current=operation;setPending(true);setError(null);
    try{
      const action:VerificationAction|undefined=operation.path==='chat'?'assistant':operation.path==='reset'?'workspace':/^documents\/[^/]+\/replace$/.test(operation.path)?'documents':undefined;
      // Chat first lets the server validate its recent, session-bound human
      // receipt. Missing/expired receipts fail before any AI work and ask once.
      let proof=action&&action!=='assistant'?await verify?.(action,operation.key,controller.signal):undefined;
      let value:Mutation|SessionState;
      try{value=await api<Mutation|SessionState>(operation.path,{...operation,proof,signal:controller.signal});}
      catch(problem){
        if(!(problem instanceof ApiError)||problem.code!=='VERIFICATION_REQUIRED'||!action||!verify)throw problem;
        // Missing proof is the ordinary first check, not a failed human check.
        // An actually rejected proof keeps the existing explicit recovery UI.
        proof=await verify(action,operation.key,controller.signal,proof!==undefined);
        value=await api<Mutation|SessionState>(operation.path,{...operation,proof,signal:controller.signal});
      }
      const next='state'in value?value.state:value;
      if(tag!==serial.current||controller.signal.aborted)return null;
      setState(next);
      return value;
    }catch(error){if(tag===serial.current&&!controller.signal.aborted)showFailure(error);return null;}
    finally{if(tag===serial.current)setPending(false);}
  },[showFailure,verify]);
  const mutate=useCallback((path:string,fields:Record<string,unknown>,method='POST')=>{
    if(!state)return Promise.resolve(null);
    return perform({path,method,body:{generation:state.generation,revision:state.revision,...fields},key:crypto.randomUUID(),csrf:state.csrf,
      ...(path==='chat'&&typeof fields.text==='string'?{chatText:fields.text.trim()}:{})});
  },[state,perform]);
  const reset=useCallback(()=>{
    if(!state)return Promise.resolve(null);
    return perform({path:'reset',method:'POST',body:{generation:state.generation,timezone:state.timezone},key:crypto.randomUUID(),csrf:state.csrf});
  },[state,perform]);
  const retry=useCallback(async()=>{const operation=last.current;const value=operation?await perform(operation):await initialize();return value?operation?.chatText??null:null;},[perform,initialize]);
  return {state,pending,error,needsZone,initialize,mutate,reset,retry};
}
