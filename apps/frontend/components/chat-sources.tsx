'use client';
import {useId,useRef,useState} from 'react';
import {AnimatePresence,LayoutGroup,motion} from 'motion/react';
import type {SessionState} from '@/lib/api';
import {citationGroups} from '@/lib/chat-sources';
import type {SourceSelection} from './source-reader';
import {SourceThumbnail} from './source-thumbnail';
import {GuideReaderDialog} from './guide-reader-dialog';
import {cardSpring} from './expanding-dialog';
import {ReplyText} from './reply-text';

export function ChatSources({claims,animate}:{claims:SessionState['messages'][number]['claims'];animate:boolean}){
 const group=useId(),opener=useRef<HTMLElement|null>(null);
 const [selected,setSelected]=useState<{key:string;selection:SourceSelection}|null>(null);
 return <LayoutGroup id={group}><div className="chat-source-groups">{citationGroups(claims).map(({key,source,claims:passages})=><section className="chat-source-group" key={key}>
  <div className="source-answer-excerpts">{passages.map((claim,index)=><p className="source-answer-excerpt" key={claim.passage_id+':'+index}><ReplyText text={claim.excerpt} animate={animate}/></p>)}</div>
  <motion.button type="button" className="chat-source-card" layoutId={key} transition={cardSpring} style={{borderRadius:14}} whileHover={{y:-3}} whileTap={{scale:.98}} aria-haspopup="dialog" aria-label={`Read ${source.title}, page ${source.page}, cited passages`} onClick={event=>{opener.current=event.currentTarget;setSelected({key,selection:{version_id:source.version_id,page:source.page,highlights:passages.map(claim=>({passage_id:claim.passage_id,page:claim.page,excerpt:claim.excerpt}))}});}}>
   <SourceThumbnail version={source.version_id} page={source.page} mediaType={source.media_type} title={source.title}/>
   <span className="chat-source-caption"><strong>{source.title}</strong><small>{source.media_type==='application/pdf'?`Page ${source.page}`:source.section} · v{source.version}</small><span>Read source <span aria-hidden="true">↗</span></span></span>
  </motion.button>
 </section>)}</div><AnimatePresence>{selected&&<GuideReaderDialog key={selected.key} layoutId={selected.key} selection={selected.selection} opener={opener.current} onClose={()=>setSelected(null)}/>}</AnimatePresence></LayoutGroup>;
}
