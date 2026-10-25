'use client';
import {Fragment,useLayoutEffect,useRef,useState,type Dispatch,type SetStateAction} from 'react';
import {money,duration,type SessionState,type Mutation,type RequestRecord} from '@/lib/api';
import {conversationShortcuts,isTourRequest,RESERVATION_SHORTCUT} from '@/lib/chat-questions';
import {acceptedMessage,bookingMessageAnchors,conversationMessages,type PendingMessage} from '@/lib/chat-messages';
import {Button,Badge,Arrow,Mark,Spinner} from './ui';
import {WeekCalendar} from './week-calendar';
import {BookingOutcome} from './booking-outcome';
import {ChatSources} from './chat-sources';
import {reviewMessage} from '@/lib/chat-sources';
import {ConversationLibrary} from './conversation-library';
import {useChatScroll} from './use-chat-scroll';
import {ReplyText} from './reply-text';
import {ChatReview,type TimeSelection} from './chat-review';
import {ChatBookingManagement,type BookingAction} from './chat-booking-management';

type Props={state:SessionState;pending:boolean;text:string;setText:Dispatch<SetStateAction<string>>;onSend:(text:string)=>Promise<Mutation|SessionState|null>;onEdit:(fields:Record<string,unknown>)=>Promise<Mutation|SessionState|null>;onSubmit:(request?:RequestRecord)=>void;onBookingAction:BookingAction;onBusiness:()=>void;onTour:()=>void};

export function ChatWorkspace({state,pending,text,setText,onSend,onEdit,onSubmit,onBookingAction,onBusiness,onTour}:Props){
 const [library,setLibrary]=useState<'questions'|'guides'|null>(null);
 const [sending,setSending]=useState<PendingMessage|null>(null);const sendingLock=useRef(false);
 const [selection,setSelection]=useState<TimeSelection|null>(null),[reviewRequest,setReviewRequest]=useState(0);
 const selectionLock=useRef(false),selectionSequence=useRef(0),reviewTarget=useRef<HTMLElement>(null);
 const messageKeys=useRef(new Map<string,string>());
 const composer=useRef<HTMLTextAreaElement>(null);const composing=useRef(false);
 const initialMessages=useRef(new Set(state.messages.map(message=>message.id)));
 const latestMessage=state.messages.at(-1);const reviewAnchor=reviewMessage(state.messages);
 const {pane,content,reveal}=useChatScroll(`${latestMessage?.id??''}:${sending?.key??''}`);
 useLayoutEffect(()=>{if(reviewRequest&&reviewTarget.current)reveal.current(reviewTarget.current);},[reviewRequest,reveal]);
 useLayoutEffect(()=>()=>{selectionSequence.current++;},[]);
 useLayoutEffect(()=>{const node=composer.current;if(!node)return;let width=0;const size=()=>{node.style.height='auto';node.style.height=Math.min(96,Math.max(44,node.scrollHeight))+'px';};size();const observer=new ResizeObserver(entries=>{const next=entries[0].contentRect.width;if(Math.abs(next-width)>.5){width=next;size();}});observer.observe(node);return()=>observer.disconnect();},[text]);
 const starters=[
  {title:'Moving out, with pets',text:`I’m moving out of my two-bedroom apartment on ${state.scenario.busy_date} at 09:00. Does that include carpet shampooing? I have two cats. Can you do the oven too?`,icon:'↗',detail:'A question, a quote, a busy day'},
  {title:'Find a regular clean',text:'I’d like a regular clean for my one-bedroom apartment. When is it free this week?',icon:'▦',detail:'Explore this week’s available times'},
  {title:'Help me choose',text:'Can you help me clean my place next Friday?',icon:'＋',detail:'A little guidance to get started'},
 ];
 async function send(value=text){
  const sent=value.trim();if(pending||sendingLock.current||!sent)return;
  if(selectionLock.current)return;
  if(selection?.status==='error')setSelection(null);
  if(isTourRequest(sent)){setText(current=>current.trim()===sent?'':current);onTour();return;}
  const submission={key:crypto.randomUUID(),text:sent,count:state.messages.length};
  sendingLock.current=true;setSending(submission);
  try{const result=await onSend(sent);if(result){const accepted=acceptedMessage(('state'in result?result.state:result).messages,submission);if(accepted)messageKeys.current.set(accepted.id,submission.key);setText(current=>current.trim()===sent?'':current);}else setText(current=>current||sent);}
  finally{sendingLock.current=false;setSending(null);composer.current?.focus({preventScroll:true});}
 }
 async function selectTime(start:string){
  if(pending||sendingLock.current||selectionLock.current)return;
  const id=++selectionSequence.current;selectionLock.current=true;
  setSelection({start,status:'saving'});setReviewRequest(id);
  try{
   const result=await onEdit({preferred_at:start});
   if(id!==selectionSequence.current)return;
   const next=result?('state'in result?result.state:result):null;
   setSelection(next?.draft.preferred_at&&Date.parse(next.draft.preferred_at)===Date.parse(start)?null:{start,status:'error'});
  }catch{if(id===selectionSequence.current)setSelection({start,status:'error'});}
  finally{if(id===selectionSequence.current)selectionLock.current=false;}
 }
 const busy=pending||!!sending||selection?.status==='saving';
 const bookingReview=<ChatReview state={state} pending={busy} onSubmit={onSubmit} selection={selection} anchor={reviewTarget}/>;
 const hasCalendar=latestMessage?.cards.includes('reserve')||latestMessage?.cards.includes('week')&&state.quote||latestMessage?.cards.includes('clarify')&&!state.quote&&!!state.scenario.requested_date;
 const shortcuts=conversationShortcuts(state);
 const bookingAnchors=bookingMessageAnchors(state.messages);
 const managementAnchors=new Map<string,string>();
 for(const message of state.messages)if(message.request_id&&(message.cards.includes('manage')||message.cards.includes('booking')))managementAnchors.set(message.request_id,message.id);
 return <><div className={`chat-layout customer-conversation ${state.messages.length?'has-messages':''}`}><section className="chat-column" aria-label="Juniper conversation">
  <header className="conversation-intro" data-tour="assistant"><span className="assistant-orb" aria-hidden="true"><Mark/></span><div><h1>Juniper’s front desk</h1><p>Questions, quotes & bookings</p></div><button type="button" className="guide-shelf-toggle" onClick={()=>setLibrary('guides')}>{state.documents.length} documents <span aria-hidden="true">↗</span></button></header>
  <div ref={pane} className="conversation-scroll" role="region" aria-label="Conversation history" tabIndex={0}><div ref={content} className="conversation-content">
  {!state.messages.length&&<div className="conversation-empty"><h2>Let’s make room for your day.</h2><p>Choose a starting point, or ask below.</p><div className="chat-starters">{starters.map(start=><button key={start.title} disabled={busy} onClick={()=>void send(start.text)}><span aria-hidden="true">{start.icon}</span><strong>{start.title}</strong><small>{start.detail}</small></button>)}</div></div>}
  <div className="chat-messages" aria-live="polite" aria-relevant="additions">
   {conversationMessages(state.messages,sending,messageKeys.current).map(({key,message})=>{const booking=message.request_id?state.requests.find(record=>record.id===message.request_id):undefined;return <Fragment key={key}><article className={`chat-message ${message.role} ${initialMessages.current.has(message.id)?'history-message':'new-message'}`} aria-label={message.role==='user'?'Your message':'Juniper reply'}>
    {message.role==='assistant'&&<span className="assistant-orb" aria-hidden="true"><Mark/></span>}
    <div className="message-body"><p className="message-text">{message.role==='assistant'?<ReplyText text={message.text} animate={!initialMessages.current.has(message.id)}/>:message.text}</p>
     {!!message.claims.length&&<ChatSources claims={message.claims} animate={!initialMessages.current.has(message.id)}/>}
     {message.id===latestMessage?.id&&message.role==='assistant'&&<>
      {message.cards.includes('quote')&&state.quote&&<div className="chat-quote"><div><small>Your quote</small><strong>{money(state.quote.cents)}</strong></div><Badge tone="blue">{duration(state.quote.minutes)}</Badge><span>{state.quote.items.map(item=>item.name).join(' + ')}</span>{!hasCalendar&&<Button kind="secondary" disabled={busy} onClick={()=>void send('When is this service free this week?')}>Find a time</Button>}</div>}
     </>}
    </div>
   </article>{booking&&message.cards.includes('manage')&&managementAnchors.get(booking.id)===message.id&&<ChatBookingManagement state={state} record={booking} pending={busy} onAction={onBookingAction}/>} {message.id===latestMessage?.id&&hasCalendar&&<div className="chat-calendar"><WeekCalendar key={message.id} rolling state={state} pending={busy} initialDate={message.requested_date??state.scenario.requested_date??undefined} initialPeriod={message.requested_period??undefined} onSelect={start=>void selectTime(start)} onReply={reply=>void send(reply)}/></div>}{message.id===reviewAnchor&&bookingReview}
   {booking?.booking&&bookingAnchors.get(booking.id)===message.id&&<div className="chat-booking-result"><BookingOutcome request={booking} zone={state.timezone}/>{managementAnchors.get(booking.id)===message.id&&<ChatBookingManagement compact state={state} record={booking} pending={busy} onAction={onBookingAction}/>}<aside className="business-booking-nudge" aria-label="Explore the business view"><p>Take a look from the business side.</p><button type="button" aria-label="View booking in Business view" onClick={onBusiness}>Business view <span aria-hidden="true">↗</span></button></aside></div>}
   </Fragment>;})}
   {sending&&<div className="assistant-working" role="status"><span className="assistant-orb" aria-hidden="true"><Mark/></span><Spinner/><span>Juniper is working on it</span></div>}
   {!reviewAnchor&&bookingReview}
  </div></div></div>
  <div className="chat-compose-area">
   <div className="conversation-suggestions" data-tour="questions" role="group" aria-label="Suggested replies">
    <button type="button" className="reservation-shortcut" disabled={busy} onClick={()=>void send(RESERVATION_SHORTCUT.text)}>{RESERVATION_SHORTCUT.label}<span aria-hidden="true">↗</span></button><div>{shortcuts.map(choice=><button type="button" key={choice.text} disabled={busy} onClick={()=>void send(choice.text)}>{choice.label}<span aria-hidden="true">↗</span></button>)}</div><button type="button" className="more-questions" aria-label="More questions" disabled={busy} onClick={()=>setLibrary('questions')}>＋</button>
   </div>
   <form className="composer glass" data-tour="composer" onSubmit={event=>{event.preventDefault();void send();}}>
    <label className="sr-only" htmlFor="enquiry">Ask Juniper</label><textarea id="enquiry" ref={composer} value={text} maxLength={1200} placeholder="Message Juniper…" rows={1} disabled={busy} onChange={event=>setText(event.target.value)} onCompositionStart={()=>{composing.current=true;}} onCompositionEnd={()=>{composing.current=false;}} onKeyDown={event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.nativeEvent.isComposing&&!composing.current){event.preventDefault();void send();}}}/>
    <Button type="submit" className="composer-send" aria-label="Send message" title="Send message (Enter)" disabled={busy||!text.trim()} busy={busy}><Arrow direction="up"/></Button>
   </form>
  </div>
 </section></div>{library&&<ConversationLibrary kind={library} documents={state.documents} onClose={()=>setLibrary(null)} onQuestion={question=>{setLibrary(null);void send(question);}} onTour={()=>{setLibrary(null);onTour();}}/>}</>;
}
