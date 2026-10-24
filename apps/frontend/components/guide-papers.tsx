'use client';
import {useEffect,useId,useRef,useState} from 'react';
import {AnimatePresence,LayoutGroup,motion} from 'motion/react';
import {ExpandingDialog,cardSpring} from './expanding-dialog';
import {GuideReaderDialog} from './guide-reader-dialog';
import {SourceThumbnail} from './source-thumbnail';
import Image from 'next/image';
import samples from '@/lib/sample-guides.json';
import type {KnowledgeDocument} from '@/lib/api';
import {Button,Mark} from './ui';

export function GuidePaper({slot,current=true}:{slot:string;current?:boolean}){
 const source=current?samples.find(row=>row.slot===slot):undefined;
 const page=source?.previews[0];
 return <span className="guide-paper" aria-hidden="true">{page?<Image src={'/guide-previews/'+page.file} width={page.width} height={page.height} alt="" unoptimized/>:<span className="guide-text-paper"><Mark/><strong>{source?.title??'Your updated document'}</strong>{source?.text?<span>{source.text.replace(/^# [^\n]+\n+/, '').replace(/^#+ /gm,'').slice(0,470)}</span>:<><i/><i/><i/><i/><small>Open to read the current version</small></>}</span>}<span className="paper-open">Read document ↗</span></span>;
}

export function SampleGuideIntro(){
 const [selected,setSelected]=useState<string|null>(null),[page,setPage]=useState(0),[perPage,setPerPage]=useState(3);
 const group=useId(),opener=useRef<HTMLElement|null>(null),carousel=useRef<HTMLDivElement>(null);
 useEffect(()=>{const node=carousel.current;if(!node)return;const size=()=>setPerPage(node.clientWidth>=800?5:node.clientWidth>=620?4:node.clientWidth>=390?3:2);size();const observer=new ResizeObserver(size);observer.observe(node);return()=>observer.disconnect();},[]);
 useEffect(()=>{const index=samples.findIndex(source=>source.slot===selected);setPage(previous=>index>=0?Math.floor(index/perPage):Math.min(previous,Math.ceil(samples.length/perPage)-1));},[perPage,selected]);
 const first=page*perPage;
 return <LayoutGroup id={group}><div className="intro-guide-story">
  <strong>Juniper’s documents are already here.</strong><p>Open a document to see what the assistant uses.</p>
  <div ref={carousel} className="intro-guide-carousel" role="region" aria-label="Juniper’s six preloaded documents" aria-roledescription="carousel" style={{gridTemplateColumns:`repeat(${perPage},minmax(0,1fr))`}}>{samples.map((source,index)=><motion.button hidden={index<first||index>=first+perPage} layoutId={source.slot} className="intro-guide-tile" whileHover={{y:-3}} whileTap={{scale:.98}} transition={cardSpring} style={{borderRadius:14}} type="button" key={source.slot} onClick={event=>{opener.current=event.currentTarget;setSelected(source.slot);}} aria-label={'Preview '+source.title} aria-haspopup="dialog" initial={{opacity:0,y:5}} animate={{opacity:1,y:0}}><GuidePaper slot={source.slot}/><strong>{source.title}</strong><span className="intro-guide-action">Read document <span aria-hidden="true">↗</span></span></motion.button>)}</div>
  <div className="intro-carousel-controls"><button type="button" className="glass-control" aria-label="Previous documents" disabled={!page} onClick={()=>setPage(value=>value-1)}>←</button><span aria-live="polite">{first+1}–{Math.min(first+perPage,samples.length)} of {samples.length} documents</span><button type="button" className="glass-control" aria-label="Next documents" disabled={first+perPage>=samples.length} onClick={()=>setPage(value=>value+1)}>→</button></div>
 </div><AnimatePresence>{selected&&<SampleGuidePreview key={selected} slot={selected} opener={opener.current} onClose={()=>setSelected(null)}/>}</AnimatePresence></LayoutGroup>;
}

function SampleGuidePreview({slot,onClose,opener}:{slot:string;onClose:()=>void;opener:HTMLElement|null}){
 const source=samples.find(row=>row.slot===slot)!;const [page,setPage]=useState(0);
 const image=source.previews[page];
 return <ExpandingDialog layoutId={slot} className="sample-guide-preview" label={source.title+' preview'} opener={opener} onClose={onClose}><header><div><span className="eyebrow blue-text">Juniper document</span><h2>{source.title}</h2></div><Button kind="quiet" onClick={onClose} aria-label="Close document preview">Close</Button></header>{image?<Image src={'/guide-previews/'+image.file} width={image.width} height={image.height} alt={`${source.title}, page ${page+1}`} unoptimized/>:<article className="faq-original">{source.text?.split('\n\n').map((paragraph,index)=>{const [first,...rest]=paragraph.split('\n');return first.startsWith('#')?<section key={index}><h3>{first.replace(/^#+ /,'')}</h3>{rest.length>0&&<p>{rest.join('\n')}</p>}</section>:<p key={index}>{paragraph}</p>;})}</article>}<footer><Button kind="secondary" disabled={!page} onClick={()=>setPage(value=>value-1)}>Previous</Button><small>Page {page+1} of {source.pages} · Version {source.version}</small><Button kind="secondary" disabled={page>=source.pages-1} onClick={()=>setPage(value=>value+1)}>Next</Button></footer></ExpandingDialog>;
}

export function GuestGuideShelf({documents}:{documents:KnowledgeDocument[]}){
 const group=useId();const opener=useRef<HTMLElement|null>(null);const [selection,setSelection]=useState<string|null>(null);
 const selected=documents.find(doc=>doc.id===selection);
 useEffect(()=>{if(selection&&!selected)setSelection(null);},[selection,selected]);
 return <LayoutGroup id={group}><div className="guest-guide-shelf">{documents.map(doc=><motion.button layoutId={doc.id} transition={cardSpring} style={{borderRadius:3}} initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} type="button" className="guest-guide" key={doc.id} onClick={event=>{opener.current=event.currentTarget;setSelection(doc.id);}} aria-haspopup="dialog"><SourceThumbnail version={doc.id} page={1} mediaType={doc.media_type} title={doc.title}/><span>{doc.title}<small>{doc.private?'Your document':`${doc.pages} ${doc.pages===1?'page':'pages'} · Juniper document`}</small></span></motion.button>)}</div><AnimatePresence>{selected&&<GuideReaderDialog key={selected.id} selection={{version_id:selected.id}} opener={opener.current} onClose={()=>setSelection(null)}/>}</AnimatePresence></LayoutGroup>;
}
