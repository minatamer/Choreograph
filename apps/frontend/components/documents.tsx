'use client';
import {useEffect,useId,useRef,useState} from 'react';
import {type SessionState,type Mutation} from '@/lib/api';
import {Button,Badge} from './ui';
import type {SourceSelection} from './source-reader';
import {GuideReaderDialog} from './guide-reader-dialog';
import {cardSpring} from './expanding-dialog';
import {SourceThumbnail} from './source-thumbnail';
import {AnimatePresence,LayoutGroup,motion} from 'motion/react';
type Props={state:SessionState;pending:boolean;onReplace:(slot:string,fields:Record<string,unknown>)=>Promise<Mutation|SessionState|null>};
type UploadScope={epoch:number;workspace:string};
export function Documents({state,pending,onReplace}:Props){
  const group=useId();const opener=useRef<HTMLElement|null>(null);
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
    setNotice('Processing your document…');
    try{const bytes=new Uint8Array(await file.arrayBuffer());if(!active(token,signal))return;
      let binary='';for(const byte of bytes)binary+=String.fromCharCode(byte);
      const result=await onReplace(slot,{kind:ext==='pdf'?'pdf':'text',data:btoa(binary)});
      if(!active(token,signal))return;
      setNotice(result&&'document_notice'in result?result.document_notice?.message??'The document is ready.':'The document could not be replaced. Your current version is unchanged.');
    }catch{if(active(token,signal))setNotice('The file could not be read. Your current document is unchanged.');}
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
  return <LayoutGroup id={group}><section className="documents-area" data-tour="documents"><div className="section-heading"><div><span className="eyebrow blue-text">The knowledge behind the conversation</span><h2>Juniper’s documents.</h2><p>Already uploaded. Ready for questions. Open a document to see what the front desk can use.</p></div><Badge tone="blue">{state.documents.length} ready documents</Badge></div>
    {notice&&<p role="status" className="document-notice">{notice}</p>}
    <div className="document-grid paper-document-grid">{state.documents.map((doc,index)=><motion.article className="document-card paper-document-card" key={doc.id} initial={{opacity:0,y:26,rotate:-4}} whileInView={{opacity:1,y:0,rotate:0}} viewport={{once:true,amount:.1}} transition={{duration:.6,delay:index*.065,ease:[.2,.8,.2,1]}}><motion.button layoutId={doc.id} style={{borderRadius:3}} transition={cardSpring} className="document-preview-button" type="button" onClick={event=>{opener.current=event.currentTarget;setSelection({version_id:doc.id});}} aria-label={'Read '+doc.title}><SourceThumbnail version={doc.id} page={1} mediaType={doc.media_type} title={doc.title}/></motion.button><div><h3>{doc.title}</h3><small>Version {doc.version} · {doc.media_type==='application/pdf'?`${doc.pages} ${doc.pages===1?'page':'pages'}`:'Text'} · {doc.private?'Your replacement':'Juniper document'}</small></div><div className="document-actions"><Button kind="secondary" onClick={event=>{opener.current=event.currentTarget;setSelection({version_id:doc.id});}} aria-label={'Open '+doc.title}>Read</Button><label className={`file-button ${pending||!state.replacements_left?'disabled':''}`}>Replace<span className="sr-only"> {doc.title}</span><input type="file" accept=".pdf,.txt,.md" disabled={pending||!state.replacements_left} onChange={event=>{void upload(doc.slot,event.target.files?.[0]);event.target.value='';}}/></label></div></motion.article>)}</div>
    <div className="document-example"><p>Try a different pet instruction, then ask the front desk again.</p><Button kind="quiet" disabled={pending||!state.replacements_left} onClick={()=>void revised()}>Use revised preparation document</Button></div><small>{state.replacements_left} replacements left · PDF, TXT or Markdown · 2 MiB · Up to 10 PDF pages. Failed files use one replacement attempt.</small>
    <AnimatePresence>{selected&&<GuideReaderDialog key={selected.version_id} selection={selected} opener={opener.current} onClose={()=>setSelection(null)}/>}</AnimatePresence>
  </section></LayoutGroup>;
}
