'use client';
import {useEffect,useRef,useState} from 'react';
import type {PDFDocumentLoadingTask,PDFDocumentProxy,RenderTask} from 'pdfjs-dist';
import {api,type DocumentDetail} from '@/lib/api';
import {Button,Badge} from './ui';
export type SourceSelection={version_id:string;passage_id?:string;page?:number;excerpt?:string};

export function SourceReader({selection,onClose,embedded=false}:{selection:SourceSelection;onClose:()=>void;embedded?:boolean}){
  const [loadedDetail,setDetail]=useState<DocumentDetail|null>(null);const [problem,setProblem]=useState('');
  const detail=loadedDetail?.document.id===selection.version_id?loadedDetail:null;
  const [pdf,setPDF]=useState<{version_id:string;document:PDFDocumentProxy;annotationMode:number}|null>(null);
  const [page,setPage]=useState(selection.page??1);const [zoom,setZoom]=useState(1);const [ready,setReady]=useState(false);
  const [renderedPage,setRenderedPage]=useState(0);
  const canvas=useRef<HTMLCanvasElement>(null);const viewport=useRef<HTMLDivElement>(null);const panel=useRef<HTMLElement>(null);
  const close=useRef(onClose);
  const renderQueue=useRef<Promise<void>>(Promise.resolve());
  useEffect(()=>{close.current=onClose;},[onClose]);
  const [width,setWidth]=useState(460);
  useEffect(()=>{const controller=new AbortController();setDetail(null);setProblem('');setReady(false);setRenderedPage(0);
    void api<DocumentDetail>(`documents/${selection.version_id}`,{signal:controller.signal}).then(value=>{if(!controller.signal.aborted)setDetail(value);}).catch(()=>{if(!controller.signal.aborted)setProblem('This source is no longer available in this demo.');});
    return()=>controller.abort();
  },[selection.version_id]);
  useEffect(()=>{setPage(selection.page??1);},[selection.version_id,selection.page]);
  useEffect(()=>{const node=viewport.current;if(!node)return;const observer=new ResizeObserver(entries=>setWidth(Math.max(160,entries[0].contentRect.width)));observer.observe(node);return()=>observer.disconnect();},[detail]);
  useEffect(()=>{
    setPDF(null);setReady(false);setRenderedPage(0);
    if(!detail||detail.document.media_type!=='application/pdf')return;
    const controller=new AbortController();let disposed=false;let loading:PDFDocumentLoadingTask|undefined;
    setProblem('');
    void(async()=>{
      const pdfjs=await import('pdfjs-dist');pdfjs.GlobalWorkerOptions.workerSrc='/vendor/pdfjs/pdf.worker.min.mjs';
      if(disposed)return;
      const response=await fetch(`/api/demo/documents/${detail.document.id}/source`,{cache:'no-store',signal:controller.signal});
      if(!response.ok)throw new Error('unavailable');
      const data=new Uint8Array(await response.arrayBuffer());if(data.length>2_097_152)throw new Error('large');
      if(disposed)return;
      loading=pdfjs.getDocument({data,useSystemFonts:true,standardFontDataUrl:'/vendor/pdfjs/standard_fonts/',
        cMapUrl:'/vendor/pdfjs/cmaps/',cMapPacked:true,wasmUrl:'/vendor/pdfjs/wasm/',enableXfa:false});
      const document=await loading.promise;
      if(!disposed)setPDF({version_id:detail.document.id,document,annotationMode:pdfjs.AnnotationMode.DISABLE});
    })().catch(()=>{if(!disposed)setProblem('The page could not be displayed. The supported passage is available below.');});
    return()=>{disposed=true;controller.abort();void loading?.destroy().catch(()=>{});};
  },[detail]);
  useEffect(()=>{
    if(!pdf||pdf.version_id!==selection.version_id)return;
    let disposed=false;let task:RenderTask|undefined;
    setReady(false);setRenderedPage(0);setProblem('');
    // Reuse only this mounted reader's document. Wait for a cancelled render
    // before another task can use the same canvas during rapid page/size changes.
    const previous=renderQueue.current;
    const current=(async()=>{
      await previous;if(disposed)return;
      const source=await pdf.document.getPage(page);if(disposed)return;
      const natural=source.getViewport({scale:1});const ratio=Math.min(2,window.devicePixelRatio||1);const scale=ratio*width/natural.width*zoom;
      const view=source.getViewport({scale});const node=canvas.current;if(!node)return;
      node.width=view.width;node.height=view.height;node.style.width=`${width*zoom}px`;node.style.height=`${view.height/ratio}px`;
      task=source.render({canvas:node,viewport:view,annotationMode:pdf.annotationMode});await task.promise;
      if(!disposed){setReady(true);setRenderedPage(page);}
    })().catch(()=>{if(!disposed)setProblem('The page could not be displayed. The supported passage is available below.');});
    renderQueue.current=current;
    return()=>{disposed=true;task?.cancel();};
  },[pdf,page,width,zoom,selection.version_id]);
  useEffect(()=>{if(embedded)return;const previous=document.activeElement as HTMLElement|null;
    if(window.matchMedia('(max-width: 900px)').matches)panel.current?.querySelector<HTMLButtonElement>('button')?.focus({preventScroll:true});
    const key=(event:KeyboardEvent)=>{if(event.defaultPrevented||panel.current?.closest('[inert]')||document.querySelector('[role="dialog"][aria-modal="true"]'))return;if(event.key==='Escape')close.current();if(event.key==='Tab'&&window.matchMedia('(max-width: 900px)').matches){
      const nodes=panel.current?.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),[tabindex="0"]');if(!nodes?.length)return;
      const first=nodes[0],last=nodes[nodes.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}};
    document.addEventListener('keydown',key);return()=>{document.removeEventListener('keydown',key);
      const target=previous?.isConnected&&previous!==document.body&&!previous.matches(':disabled')?previous:document.querySelector<HTMLTextAreaElement>('#enquiry:not(:disabled)');
      target?.focus({preventScroll:true});};
  },[embedded]);
  const passage=detail?.passages.find(p=>p.id===selection.passage_id&&p.page===page)??detail?.passages.find(p=>p.page===page);
  return <aside className={`source-reader ${embedded?'embedded-source-reader':'glass'}`} aria-label="Document reader" ref={panel}>
    <div className="source-toolbar"><div><Badge tone="blue">Source</Badge><h2>{detail?.document.title??'Opening document…'}</h2>{detail&&<small>Version {detail.document.version} · {detail.document.private?'Your replacement':'Juniper document'}</small>}</div><Button kind="quiet" onClick={onClose} aria-label="Close document reader">Close</Button></div>
    {problem&&<p role="status">{problem}</p>}
    {detail&&<><div className="source-controls"><Button kind="quiet" disabled={page<=1} onClick={()=>setPage(p=>p-1)}>Previous</Button><span>Page {page} of {detail.document.pages}</span><Button kind="quiet" disabled={page>=detail.document.pages} onClick={()=>setPage(p=>p+1)}>Next</Button>{detail.document.media_type==='application/pdf'&&<label>Zoom<select value={zoom} onChange={event=>setZoom(Number(event.target.value))}><option value={1}>Fit</option><option value={1.25}>125%</option><option value={1.5}>150%</option></select></label>}</div>
      <div className="source-page" ref={viewport}>{detail.document.media_type==='application/pdf'?<><canvas ref={canvas} data-rendered-page={renderedPage} aria-label={`${detail.document.title}, page ${page}`} role="img"/>{!ready&&!problem&&<p role="status">Loading page…</p>}</>:<div className="text-source">{detail.passages.map(p=><section key={p.id}><h3>{p.section}</h3><p>{p.content}</p></section>)}</div>}</div>
      {passage&&<section className="supported-excerpt"><strong>Supported excerpt · {passage.section}</strong><p>Text highlight shown below the original page.</p><blockquote><mark>{selection.excerpt&&passage.content.includes(selection.excerpt)?selection.excerpt:passage.content}</mark></blockquote></section>}
    </>}
  </aside>;
}
