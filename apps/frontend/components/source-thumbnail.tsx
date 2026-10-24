'use client';
import {useEffect,useRef,useState} from 'react';
import type {PDFDocumentLoadingTask,RenderTask} from 'pdfjs-dist';
import {Mark} from './ui';

/** Lazy thumbnails always read this guest's authorized version, including replacements. */
export function SourceThumbnail({version,page,mediaType,title}:{version:string;page:number;mediaType:string;title:string}){
 const root=useRef<HTMLSpanElement>(null),canvas=useRef<HTMLCanvasElement>(null);
 const [visible,setVisible]=useState(false),[ready,setReady]=useState(false),[problem,setProblem]=useState(false),[text,setText]=useState('');
 useEffect(()=>{const node=root.current;if(!node)return;const observer=new IntersectionObserver(entries=>{
  if(entries.some(entry=>entry.isIntersecting)){setVisible(true);observer.disconnect();}
 },{root:node.closest('.conversation-scroll'),rootMargin:'180px'});observer.observe(node);return()=>observer.disconnect();},[]);
 useEffect(()=>{
  if(!visible)return;const controller=new AbortController();let disposed=false,destroyed=false;
  let loading:PDFDocumentLoadingTask|undefined,render:RenderTask|undefined;
  const destroy=()=>{if(loading&&!destroyed){destroyed=true;void loading.destroy().catch(()=>{});}};
  void(async()=>{
   if(mediaType!=='application/pdf'){
    const response=await fetch(`/api/demo/documents/${version}/source`,{cache:'no-store',signal:controller.signal});
    if(!response.ok)throw Error('unavailable');const content=await response.text();if(Array.from(content).length>32_000)throw Error('large');
    if(!disposed){setText(content);setReady(true);}return;
   }
   const pdfjs=await import('pdfjs-dist');pdfjs.GlobalWorkerOptions.workerSrc='/vendor/pdfjs/pdf.worker.min.mjs';
   const response=await fetch(`/api/demo/documents/${version}/source`,{cache:'no-store',signal:controller.signal});
   if(!response.ok)throw Error('unavailable');const data=new Uint8Array(await response.arrayBuffer());
   if(data.length>2_097_152)throw Error('large');if(disposed)return;
   loading=pdfjs.getDocument({data,useSystemFonts:true,standardFontDataUrl:'/vendor/pdfjs/standard_fonts/',cMapUrl:'/vendor/pdfjs/cmaps/',cMapPacked:true,wasmUrl:'/vendor/pdfjs/wasm/',enableXfa:false});
   const document=await loading.promise;if(disposed)return;const source=await document.getPage(page);if(disposed)return;
   const natural=source.getViewport({scale:1}),view=source.getViewport({scale:320/natural.width});const node=canvas.current;if(!node)return;
   node.width=view.width;node.height=view.height;
   render=source.render({canvas:node,viewport:view,annotationMode:pdfjs.AnnotationMode.DISABLE});await render.promise;
   if(!disposed){root.current?.style.setProperty('aspect-ratio',`${natural.width}/${natural.height}`);setReady(true);}
  })().catch(()=>{if(!disposed)setProblem(true);}).finally(destroy);
  return()=>{disposed=true;controller.abort();render?.cancel();destroy();};
 },[visible,version,page,mediaType]);
 return <span ref={root} className="guide-paper source-preview-paper" aria-hidden="true" data-source-version={version} data-preview-page={page}>
  {mediaType==='application/pdf'?<canvas ref={canvas} data-thumbnail-ready={ready||undefined}/>:<span className="guide-text-paper"><Mark/><strong>{title}</strong><span>{text.slice(0,650)}</span></span>}
  {!ready&&<span className="source-preview-loading"><Mark/><small>{problem?'Open document':visible?'Loading page…':'Document preview'}</small></span>}
  <span className="paper-open">Read cited page ↗</span>
 </span>;
}
