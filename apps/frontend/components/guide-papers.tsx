'use client';
import {useEffect,useId,useRef,useState} from 'react';
import {AnimatePresence,LayoutGroup,motion} from 'motion/react';
import {ExpandingDialog,cardSpring} from './expanding-dialog';
import {GuideReaderDialog} from './guide-reader-dialog';
import Image from 'next/image';
import samples from '@/lib/sample-guides.json';
import type {KnowledgeDocument} from '@/lib/api';
import {Button,Mark} from './ui';

export function GuidePaper({slot,current=true}:{slot:string;current?:boolean}){
 const source=current?samples.find(row=>row.slot===slot):undefined;
 const page=source?.previews[0];
 return <span className="guide-paper" aria-hidden="true">{page?<Image src={'/guide-previews/'+page.file} width={page.width} height={page.height} alt="" unoptimized/>:<span className="guide-text-paper"><Mark/><strong>{source?.title??'Your updated guide'}</strong>{source?.text?<span>{source.text.replace(/^# [^\n]+\n+/, '').replace(/^#+ /gm,'').slice(0,470)}</span>:<><i/><i/><i/><i/><small>Open to read the current version</small></>}</span>}<span className="paper-open">Read guide ↗</span></span>;
}

export function SampleGuideIntro(){
 const [selected,setSelected]=useState<string|null>(null);const group=useId();const opener=useRef<HTMLElement|null>(null);
 return <LayoutGroup id={group}><div className="intro-guide-story"><div className="intro-paper-fan" aria-label="Juniper’s preloaded guides">{samples.slice(0,3).map(source=><motion.button layoutId={source.slot} transition={cardSpring} style={{borderRadius:3}} type="button" key={source.slot} onClick={event=>{opener.current=event.currentTarget;setSelected(source.slot);}} aria-label={'Preview '+source.title}><GuidePaper slot={source.slot}/></motion.button>)}</div><strong>Juniper’s guides are already here.</strong><p>Ask about a service or policy. Check the exact page behind the answer.</p><div className="intro-guide-links">{samples.map((source,index)=><motion.button layoutId={index>2?source.slot:undefined} transition={cardSpring} type="button" key={source.slot} onClick={event=>{opener.current=event.currentTarget;setSelected(source.slot);}}>{source.title}</motion.button>)}</div></div><AnimatePresence>{selected&&<SampleGuidePreview key={selected} slot={selected} opener={opener.current} onClose={()=>setSelected(null)}/>}</AnimatePresence></LayoutGroup>;
}

function SampleGuidePreview({slot,onClose,opener}:{slot:string;onClose:()=>void;opener:HTMLElement|null}){
 const source=samples.find(row=>row.slot===slot)!;const [page,setPage]=useState(0);
 const image=source.previews[page];
 return <ExpandingDialog layoutId={slot} className="sample-guide-preview" label={source.title+' preview'} opener={opener} onClose={onClose}><header><div><span className="eyebrow blue-text">Juniper guide</span><h2>{source.title}</h2></div><Button kind="quiet" onClick={onClose} aria-label="Close guide preview">Close</Button></header>{image?<Image src={'/guide-previews/'+image.file} width={image.width} height={image.height} alt={`${source.title}, page ${page+1}`} unoptimized/>:<article className="faq-original">{source.text?.split('\n\n').map((paragraph,index)=>{const [first,...rest]=paragraph.split('\n');return first.startsWith('#')?<section key={index}><h3>{first.replace(/^#+ /,'')}</h3>{rest.length>0&&<p>{rest.join('\n')}</p>}</section>:<p key={index}>{paragraph}</p>;})}</article>}<footer><Button kind="secondary" disabled={!page} onClick={()=>setPage(value=>value-1)}>Previous</Button><small>Page {page+1} of {source.pages} · Version {source.version}</small><Button kind="secondary" disabled={page>=source.pages-1} onClick={()=>setPage(value=>value+1)}>Next</Button></footer></ExpandingDialog>;
}

export function GuestGuideShelf({documents}:{documents:KnowledgeDocument[]}){
 const group=useId();const opener=useRef<HTMLElement|null>(null);const [selection,setSelection]=useState<string|null>(null);
 const selected=documents.find(doc=>doc.id===selection);
 useEffect(()=>{if(selection&&!selected)setSelection(null);},[selection,selected]);
 return <LayoutGroup id={group}><div className="guest-guide-shelf">{documents.map(doc=><motion.button layoutId={doc.id} transition={cardSpring} style={{borderRadius:3}} initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} type="button" className="guest-guide" key={doc.id} onClick={event=>{opener.current=event.currentTarget;setSelection(doc.id);}} aria-haspopup="dialog"><GuidePaper slot={doc.slot} current={!doc.private&&doc.version==='1.0'}/><span>{doc.title}<small>{doc.private?'Your guide':`${doc.pages} ${doc.pages===1?'page':'pages'} · Juniper guide`}</small></span></motion.button>)}</div><AnimatePresence>{selected&&<GuideReaderDialog key={selected.id} selection={{version_id:selected.id}} opener={opener.current} onClose={()=>setSelection(null)}/>}</AnimatePresence></LayoutGroup>;
}
