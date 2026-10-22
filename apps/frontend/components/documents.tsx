'use client';
import {useEffect,useRef,useState} from 'react';
import {type SessionState,type Mutation} from '@/lib/api';
import {Button,Badge} from './ui';
import {SourceReader,type SourceSelection} from './source-reader';
type Props={state:SessionState;pending:boolean;onReplace:(slot:string,fields:Record<string,unknown>)=>Promise<Mutation|SessionState|null>};
type UploadScope={epoch:number;workspace:string};
export function Documents({state,pending,onReplace}:Props){
  const [selection,setSelection]=useState<SourceSelection|null>(null);const [notice,setNotice]=useState('');
  const lifetime=useRef({epoch:0,mounted:false,workspace:state.workspace_id});
  const sample=useRef<AbortController|null>(null);
  useEffect(()=>{const current=lifetime.current;current.epoch++;current.mounted=true;current.workspace=state.workspace_id;
    return()=>{current.epoch++;current.mounted=false;sample.current?.abort();};
  },[state.workspace_id]);
  const scope=():UploadScope=>({epoch:lifetime.current.epoch,workspace:state.workspace_id});
  const active=(token:UploadScope,signal?:AbortSignal)=>lifetime.current.mounted&&lifetime.current.epoch===token.epoch&&
    lifetime.current.workspace===token.workspace&&!signal?.aborted;
  const selected=selection&&state.documents.some(doc=>doc.id===selection.version_id)?selection:null;
  useEffect(()=>{if(selection&&!selected)setSelection(null);},[selection,selected]);
  async function upload(slot:string,file:File|undefined,token=scope(),signal?:AbortSignal){
    if(!file||!active(token,signal))return;
    if(file.size>2_097_152){setNotice('Choose a file smaller than 2 MiB.');return;}
    const ext=file.name.split('.').at(-1)?.toLowerCase();if(!ext||!['pdf','txt','md'].includes(ext)){setNotice('Choose a PDF, TXT or Markdown file.');return;}
    setNotice('Processing your guide…');
    try{const bytes=new Uint8Array(await file.arrayBuffer());if(!active(token,signal))return;
      let binary='';for(const byte of bytes)binary+=String.fromCharCode(byte);
      const result=await onReplace(slot,{kind:ext==='pdf'?'pdf':'text',data:btoa(binary)});
      if(!active(token,signal))return;
      setNotice(result&&'document_notice'in result?result.document_notice?.message??'The guide is ready.':'The guide could not be replaced. Your current version is unchanged.');
    }catch{if(active(token,signal))setNotice('The file could not be read. Your current guide is unchanged.');}
  }
  async function revised(){
    const token=scope();if(!active(token))return;
    sample.current?.abort();const controller=new AbortController();sample.current=controller;
    try{
      const response=await fetch('/samples/preparation-guide-v2.pdf',{signal:controller.signal});if(!active(token,controller.signal))return;
      if(!response.ok){setNotice('The sample could not be opened. Try again.');return;}
      const blob=await response.blob();if(!active(token,controller.signal))return;
      await upload('preparation',new File([blob],'preparation-guide-v2.pdf',{type:'application/pdf'}),token,controller.signal);
    }catch{if(active(token,controller.signal))setNotice('The sample could not be opened. Try again.');}
    finally{if(sample.current===controller)sample.current=null;}
  }
  return <section className="documents-area"><div className="section-heading"><div><h2>Documents</h2><p>Juniper’s service and preparation guides.</p></div><Badge tone="neutral">{state.replacements_left} replacements left</Badge></div>
    {notice&&<p role="status" className="document-notice">{notice}</p>}
    <div className="document-grid">{state.documents.map(doc=><article className="document-card" key={doc.id}><div className="document-icon" aria-hidden="true">↗</div><div><h3>{doc.title}</h3><small>Version {doc.version} · {doc.media_type==='application/pdf'?`${doc.pages} ${doc.pages===1?'page':'pages'}`:'Text'} · {doc.private?'Your replacement':'Sample'}</small></div><div className="document-actions"><Button kind="secondary" onClick={()=>setSelection({version_id:doc.id})}>Read guide</Button><label className={`file-button ${pending||!state.replacements_left?'disabled':''}`}>Replace<span className="sr-only"> {doc.title}</span><input type="file" accept=".pdf,.txt,.md" disabled={pending||!state.replacements_left} onChange={event=>{void upload(doc.slot,event.target.files?.[0]);event.target.value='';}}/></label></div></article>)}</div>
    <div className="document-example"><p>Try a different pet instruction, then ask the front desk again.</p><Button kind="quiet" disabled={pending||!state.replacements_left} onClick={()=>void revised()}>Use revised preparation guide</Button></div><small>PDF, TXT or Markdown · 2 MiB · Up to 10 PDF pages. Failed files use one replacement attempt.</small>
    {selected&&<SourceReader key={selected.version_id} selection={selected} onClose={()=>setSelection(null)}/>}
  </section>;
}
