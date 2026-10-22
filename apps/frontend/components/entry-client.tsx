'use client';
import {useGuest} from './use-guest';
import {AppHeader,Badge,Button} from './ui';
import {CRMControls} from './crm-controls';
import {useEffect,useState} from 'react';
export function EntryClient(){
 const guest=useGuest();const {state,pending,error}=guest;
 const [notice,setNotice]=useState('');
 useEffect(()=>{const value=new URL(window.location.href).searchParams.get('crm');if(value==='unavailable')setNotice('The HubSpot connection could not be completed. You can continue without CRM.');if(value==='cancelled')setNotice('Connection cancelled. No CRM records were sent.');window.history.replaceState(null,'','/demo');},[]);
 async function skip(){const result=await guest.mutate('crm/skip',{});if(result)window.location.assign('/demo/workspace');}
 return <><AppHeader><Badge tone="neutral">Juniper Cleaning · Demo</Badge></AppHeader><main id="main" className="entry-page"><span className="eyebrow blue-text">Juniper Cleaning</span><h1>Try the front desk.</h1><p className="entry-intro">Ask a question, find a time and book a cleaning. Choose whether to connect a CRM.</p>
  {error&&<p role="alert">{error.message}</p>}{notice&&<p role="status">{notice}</p>}{guest.needsZone&&<p>Open the front desk to choose your timezone. <a href="/demo/workspace">Continue</a></p>}
  <div className="entry-choices"><article>{state?<CRMControls state={state} pending={pending} mutate={guest.mutate} onContinue={()=>window.location.assign('/demo/workspace')}/>:<p role="status">Opening your private demo…</p>}</article><article className="subtle"><Badge tone="neutral">No connection needed</Badge><h2>Continue without CRM</h2><p>Explore the same questions, documents, calendar and booking. No records are sent to a CRM.</p><Button kind="secondary" disabled={!state||pending} onClick={()=>void skip()}>Continue without CRM</Button></article></div><p className="entry-note">The company, staff and appointments are fictional. Scheduling uses your local timezone.</p></main></>;
}
