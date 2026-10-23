'use client';
import {useLayoutEffect,useRef,useState,type Dispatch,type SetStateAction} from 'react';
import {money,duration,type SessionState,type Mutation} from '@/lib/api';
import {conversationShortcuts,isTourRequest} from '@/lib/chat-questions';
import {acceptedMessage,conversationMessages,type PendingMessage} from '@/lib/chat-messages';
import {Button,Badge,Arrow,Mark,Spinner} from './ui';
import {WeekCalendar} from './week-calendar';
import {BookingOutcome} from './booking-outcome';
import {SourceReader,type SourceSelection} from './source-reader';
import {ConversationLibrary} from './conversation-library';
import {useChatScroll} from './use-chat-scroll';
import {ReplyText} from './reply-text';
import {ChatReview} from './chat-review';

type Props={state:SessionState;pending:boolean;text:string;setText:Dispatch<SetStateAction<string>>;onSend:(text:string)=>Promise<Mutation|SessionState|null>;onEdit:(fields:Record<string,unknown>)=>void;onSubmit:()=>void;onBusiness:()=>void;onTour:()=>void};

export function ChatWorkspace({state,pending,text,setText,onSend,onEdit,onSubmit,onBusiness,onTour}:Props){
 const [selection,setSelection]=useState<SourceSelection|null>(null);const [library,setLibrary]=useState<'questions'|'guides'|null>(null);
 const [sending,setSending]=useState<PendingMessage|null>(null);const sendingLock=useRef(false);
 const messageKeys=useRef(new Map<string,string>());
 const composer=useRef<HTMLTextAreaElement>(null);const composing=useRef(false);
 const initialMessages=useRef(new Set(state.messages.map(message=>message.id)));
 const latestMessage=state.messages.at(-1);const latest=state.requests.at(-1);
 const {pane,content}=useChatScroll(`${latestMessage?.id??''}:${sending?.key??''}`);
 useLayoutEffect(()=>{const node=composer.current;if(!node)return;let width=0;const size=()=>{node.style.height='auto';node.style.height=Math.min(96,Math.max(44,node.scrollHeight))+'px';};size();const observer=new ResizeObserver(entries=>{const next=entries[0].contentRect.width;if(Math.abs(next-width)>.5){width=next;size();}});observer.observe(node);return()=>observer.disconnect();},[text]);
 const starters=[
  {title:'Moving out, with pets',text:`I’m moving out of my two-bedroom apartment on ${state.scenario.busy_date} at 09:00. Does that include carpet shampooing? I have two cats. Can you do the oven too?`,icon:'↗',detail:'A question, a quote, a busy day'},
  {title:'Find a regular clean',text:'I’d like a regular clean for my one-bedroom apartment. When is it free this week?',icon:'▦',detail:'Explore this week’s available times'},
  {title:'Help me choose',text:'Can you help me clean my place next Friday?',icon:'＋',detail:'A little guidance to get started'},
 ];
 async function send(value=text){
  const sent=value.trim();if(pending||sendingLock.current||!sent)return;
  if(isTourRequest(sent)){setText(current=>current.trim()===sent?'':current);onTour();return;}
  const submission={key:crypto.randomUUID(),text:sent,count:state.messages.length};
  sendingLock.current=true;setSending(submission);
  try{const result=await onSend(sent);if(result){const accepted=acceptedMessage(('state'in result?result.state:result).messages,submission);if(accepted)messageKeys.current.set(accepted.id,submission.key);setText(current=>current.trim()===sent?'':current);}else setText(current=>current||sent);}
  finally{sendingLock.current=false;setSending(null);composer.current?.focus({preventScroll:true});}
 }
 const busy=pending||!!sending;
 const hasCalendar=latestMessage?.cards.includes('week')&&state.quote;
 const shortcuts=conversationShortcuts(state);
 return <><div className={`chat-layout customer-conversation ${selection?'source-open':''} ${state.messages.length?'has-messages':''}`}><section className="chat-column" aria-label="Juniper conversation">
  <header className="conversation-intro" data-tour="assistant"><span className="assistant-orb" aria-hidden="true"><Mark/></span><div><h1>Juniper’s front desk</h1><p>Questions, quotes & bookings</p></div><button type="button" className="guide-shelf-toggle" onClick={()=>setLibrary('guides')}>{state.documents.length} documents <span aria-hidden="true">↗</span></button></header>
  <div ref={pane} className="conversation-scroll" role="region" aria-label="Conversation history" tabIndex={0}><div ref={content} className="conversation-content">
  {!state.messages.length&&<div className="conversation-empty"><h2>Let’s make room for your day.</h2><p>Choose a starting point, or ask below.</p><div className="chat-starters">{starters.map(start=><button key={start.title} disabled={busy} onClick={()=>void send(start.text)}><span aria-hidden="true">{start.icon}</span><strong>{start.title}</strong><small>{start.detail}</small></button>)}</div></div>}
  <div className="chat-messages" aria-live="polite" aria-relevant="additions">
   {conversationMessages(state.messages,sending,messageKeys.current).map(({key,message})=><article key={key} className={`chat-message ${message.role} ${initialMessages.current.has(message.id)?'history-message':'new-message'}`} aria-label={message.role==='user'?'Your message':'Juniper reply'}>
    {message.role==='assistant'&&<span className="assistant-orb" aria-hidden="true"><Mark/></span>}
    <div className="message-body"><p className="message-text">{message.role==='assistant'?<ReplyText text={message.text} animate={!initialMessages.current.has(message.id)}/>:message.text}</p>
     {!!message.claims.length&&<div className="answer-passages">{message.claims.map(claim=><section className="sourced-answer" key={claim.passage_id}><p className="source-answer-excerpt"><ReplyText text={claim.excerpt} animate={!initialMessages.current.has(message.id)}/></p><button className={`source-citation ${selection?.passage_id===claim.passage_id?'selected-source':''}`} onClick={()=>setSelection({version_id:claim.version_id,passage_id:claim.passage_id,page:claim.page,excerpt:claim.excerpt})}><span aria-hidden="true">▤</span><span>{claim.title}<small>{claim.media_type==='application/pdf'?`Page ${claim.page}`:claim.section} · v{claim.version}</small></span><span aria-hidden="true">↗</span></button></section>)}</div>}
     {message.id===latestMessage?.id&&message.role==='assistant'&&<>
      {message.cards.includes('quote')&&state.quote&&<div className="chat-quote"><div><small>Your quote</small><strong>{money(state.quote.cents)}</strong></div><Badge tone="blue">{duration(state.quote.minutes)}</Badge><span>{state.quote.items.map(item=>item.name).join(' + ')}</span>{!hasCalendar&&<Button kind="secondary" disabled={busy} onClick={()=>void send('When is this service free this week?')}>Find a time</Button>}</div>}
     </>}
    </div>
   </article>)}
   {sending&&<div className="assistant-working" role="status"><span className="assistant-orb" aria-hidden="true"><Mark/></span><Spinner/><span>Juniper is working on it</span></div>}
   {hasCalendar&&latestMessage&&<div className="chat-calendar"><WeekCalendar key={latestMessage.id} state={state} pending={busy} initialDate={latestMessage.requested_date??undefined} onSelect={preferred_at=>onEdit({preferred_at})}/></div>}
   <ChatReview state={state} pending={busy} onSubmit={onSubmit}/>
   {latest?.status==='awaiting_review'&&<div className="request-sent"><Badge tone="amber">Awaiting review</Badge><p>Your request is with Juniper. Let’s take a look from the business side.</p><Button kind="secondary" onClick={onBusiness}>Review in Business view</Button></div>}
   {latest?.booking&&<BookingOutcome request={latest} zone={state.timezone} onReview={onBusiness}/>}
  </div></div></div>
  <div className="chat-compose-area">
   <div className="conversation-suggestions" data-tour="questions" role="group" aria-label="Suggested replies">
    <div>{shortcuts.map(choice=><button type="button" key={choice.text} disabled={busy} onClick={()=>void send(choice.text)}>{choice.label}<span aria-hidden="true">↗</span></button>)}</div><button type="button" className="more-questions" aria-label="More questions" disabled={busy} onClick={()=>setLibrary('questions')}>＋</button>
   </div>
   <form className="composer glass" data-tour="composer" onSubmit={event=>{event.preventDefault();void send();}}>
    <label className="sr-only" htmlFor="enquiry">Ask Juniper</label><textarea id="enquiry" ref={composer} value={text} maxLength={1200} placeholder="Message Juniper…" rows={1} disabled={busy} onChange={event=>setText(event.target.value)} onCompositionStart={()=>{composing.current=true;}} onCompositionEnd={()=>{composing.current=false;}} onKeyDown={event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.nativeEvent.isComposing&&!composing.current){event.preventDefault();void send();}}}/>
    <Button type="submit" className="composer-send" aria-label="Send message" title="Send message (Enter)" disabled={busy||!text.trim()} busy={busy}><Arrow direction="up"/></Button>
   </form>
  </div>
 </section>{selection&&<div className="chat-companion"><SourceReader selection={selection} onClose={()=>setSelection(null)}/></div>}</div>{library&&<ConversationLibrary kind={library} documents={state.documents} onClose={()=>setLibrary(null)} onQuestion={question=>{setLibrary(null);void send(question);}} onTour={()=>{setLibrary(null);onTour();}}/>}</>;
}
