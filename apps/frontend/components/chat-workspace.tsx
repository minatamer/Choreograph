'use client';
import {useEffect,useRef,useState,type Dispatch,type SetStateAction} from 'react';
import {money,duration,type SessionState,type Mutation} from '@/lib/api';
import {Button,Badge,Arrow} from './ui';
import {WeekCalendar} from './week-calendar';
import {RequestPlanner} from './request-planner';
import {BookingOutcome} from './booking-outcome';
import {SourceReader,type SourceSelection} from './source-reader';

const QUESTION_GROUPS=[
  {name:'What’s included',questions:["What’s included in move-out cleaning?",'Do you offer carpet shampooing?','Can I add oven cleaning?','Can you move heavy furniture?']},
  {name:'Getting ready',questions:['What should I do with my pets?','How should I prepare the apartment?','How do I arrange access for the cleaner?','How do I prepare the oven?']},
  {name:'Supplies and methods',questions:['What cleaning supplies do you use?','How do you clean a kitchen?','Do I need to provide equipment?','Can I request fragrance-free products?']},
  {name:'A quote and a time',questions:['Show a quote for a two-bedroom move-out with the oven.','What morning appointments are available?','I need a clean tomorrow.','When is this service free this week?']},
  {name:'Changes and limits',questions:['How do rescheduling and cancellation work?','Can you guarantee I get my deposit back?','What if my preferred time is unavailable?','Do you remove mould or pests?']},
  {name:'Try a correction',questions:['Remove the oven.','Make that a deep clean instead.','Three bedrooms instead.','What is your service area?']},
];
type Props={state:SessionState;pending:boolean;text:string;setText:Dispatch<SetStateAction<string>>;onSend:(text:string)=>Promise<Mutation|SessionState|null>;onEdit:(fields:Record<string,unknown>)=>void;onSubmit:()=>void;onBusiness:()=>void};

export function ChatWorkspace({state,pending,text,setText,onSend,onEdit,onSubmit,onBusiness}:Props){
  const [selection,setSelection]=useState<SourceSelection|null>(null);const [questions,setQuestions]=useState(false);
  const composer=useRef<HTMLTextAreaElement>(null);const composing=useRef(false);const end=useRef<HTMLDivElement>(null);
  const latestMessage=state.messages.at(-1);const latest=state.requests.at(-1);
  const outcome=useRef<HTMLDivElement>(null);
  useEffect(()=>{if(latest?.booking||latest?.status==='awaiting_review')outcome.current?.scrollIntoView({behavior:'smooth',block:'center'});},[latest?.id,latest?.status]);
  const observed=useRef(latestMessage?.id);
  useEffect(()=>{if(observed.current===latestMessage?.id)return;observed.current=latestMessage?.id;const claim=latestMessage?.claims[0];setSelection(claim?{version_id:claim.version_id,passage_id:claim.passage_id,page:claim.page,excerpt:claim.excerpt}:null);
    if(latestMessage)end.current?.scrollIntoView({behavior:'smooth',block:'nearest'});
  },[latestMessage?.id]);
  const starters=[
    {title:'Moving out, with pets',text:`I’m moving out of my two-bedroom apartment on ${state.scenario.busy_date} at 09:00. Does that include carpet shampooing? I have two cats. Can you do the oven too?`,icon:'↗'},
    {title:'Find a regular clean',text:'I’d like a regular clean for my one-bedroom apartment. When is it free this week?',icon:'▦'},
    {title:'Help me choose',text:'Can you help me clean my place next Friday?',icon:'＋'},
  ];
  function choose(value:string){setText(value);setQuestions(false);composer.current?.focus();composer.current?.scrollIntoView({behavior:'smooth',block:'nearest'});}
  async function send(){if(pending||!text.trim())return;const sent=text.trim();const result=await onSend(sent);if(result){setText(current=>current.trim()===sent?'':current);composer.current?.focus();}}
  const hasCalendar=latestMessage?.cards.includes('week')&&state.quote;
  return <div className={`chat-layout ${selection?'source-open':''}`}><section className="chat-column" aria-label="Juniper conversation">
    <div className="chat-starters">{starters.map(start=><button key={start.title} disabled={pending} onClick={()=>choose(start.text)}><span aria-hidden="true">{start.icon}</span><strong>{start.title}</strong><small>{start.title==='Moving out, with pets'?'A clean, a question, a busy day':start.title==='Find a regular clean'?'See what’s free this week':'Start with a few details'}</small></button>)}</div>
    <div className="chat-messages" aria-live="polite" aria-relevant="additions text">
      {!state.messages.length&&<div className="welcome-bubble"><span className="assistant-orb" aria-hidden="true">✳</span><div><h2>Let’s find a time that works.</h2><p>Choose an example above, or ask a question below.</p></div></div>}
      {state.messages.map(message=><article key={message.id} className={`chat-message ${message.role}`} aria-label={message.role==='user'?'Your message':'Juniper reply'}>
        {message.role==='assistant'&&<span className="assistant-orb" aria-hidden="true">✳</span>}
        <div className="message-body"><p className="message-text">{message.text}</p>
          {message.claims.length>0&&<div className="answer-passages">{message.claims.map(claim=><div className="answer-passage" key={claim.passage_id}><p>{claim.excerpt}</p><button className={selection?.passage_id===claim.passage_id?'selected-source':''} onClick={()=>setSelection({version_id:claim.version_id,passage_id:claim.passage_id,page:claim.page,excerpt:claim.excerpt})}><span aria-hidden="true">↗</span>{claim.title} <small>v{claim.version} · {claim.media_type==='application/pdf'?`p. ${claim.page}`:claim.section}</small></button></div>)}</div>}
          {message.id===latestMessage?.id&&message.role==='assistant'&&<>
            {(message.cards.includes('services')||message.cards.includes('clarify'))&&<div className="clarification-card"><strong>{!state.draft.service?'Choose a cleaning':'Home size'}</strong><div>{!state.draft.service?['Regular','Deep','Move-out'].map(service=><Button key={service} kind="secondary" disabled={pending} onClick={()=>choose(`I’d like a ${service.toLowerCase()} clean.`)}>{service}</Button>):[1,2,3].map(n=><Button key={n} kind="secondary" disabled={pending} onClick={()=>choose(`${n} bedroom${n>1?'s':''}, please.`)}>{n} bedroom{n>1?'s':''}</Button>)}</div></div>}
            {message.cards.includes('quote')&&state.quote&&<div className="chat-quote"><div><small>Current quote</small><strong>{money(state.quote.cents)}</strong></div><Badge tone="blue">{duration(state.quote.minutes)}</Badge><span>{state.quote.items.map(item=>item.name).join(' + ')}</span></div>}
          </>}
        </div>
      </article>)}
      {hasCalendar&&latestMessage&&<div className="chat-calendar"><WeekCalendar key={latestMessage.id} state={state} pending={pending} initialDate={latestMessage.requested_date??undefined} onSelect={preferred_at=>onEdit({preferred_at})}/></div>}
      <div ref={outcome}>{latest?.status==='awaiting_review'&&<div className="request-sent"><Badge tone="amber">Awaiting review</Badge><p>Your request has been sent to Juniper.</p><Button kind="secondary" onClick={onBusiness}>Review in Business view</Button></div>}
      {latest?.booking&&<BookingOutcome request={latest} zone={state.timezone} onReview={onBusiness}/>}</div>
      <div ref={end}/>
    </div>
    <div className="chat-compose-area">
      {!!latestMessage?.suggestions.length&&<div className="follow-up-questions">{latestMessage.suggestions.map(choice=><button key={choice.label} disabled={pending} onClick={()=>choose(choice.text)}>{choice.label} <span aria-hidden="true">↗</span></button>)}</div>}
      <div className="question-menu"><button className="questions-toggle" aria-expanded={questions} onClick={()=>setQuestions(value=>!value)}>Questions to try <span aria-hidden="true">{questions?'−':'＋'}</span></button>{questions&&<div className="question-bank">{QUESTION_GROUPS.map(group=><section key={group.name}><h3>{group.name}</h3>{group.questions.map(question=><button key={question} onClick={()=>choose(question)}>{question}<span aria-hidden="true">↗</span></button>)}</section>)}</div>}</div>
      <form className="composer glass" onSubmit={event=>{event.preventDefault();void send();}}>
        <label className="sr-only" htmlFor="enquiry">Ask Juniper</label><textarea id="enquiry" ref={composer} value={text} maxLength={1200} placeholder="Ask about a clean, a guide or a time…" rows={2} disabled={pending}
          onChange={event=>setText(event.target.value)} onCompositionStart={()=>{composing.current=true;}} onCompositionEnd={()=>{composing.current=false;}}
          onKeyDown={event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.nativeEvent.isComposing&&!composing.current){event.preventDefault();void send();}}}/>
        <Button type="submit" aria-label="Send message" disabled={pending||!text.trim()}>{pending?'Working…':'Send'}<Arrow direction="up"/></Button>
      </form><small className="composer-hint">Use fictional details. Enter to send · Shift+Enter for a new line.</small>
    </div>
  </section><div className="chat-companion">{selection?<SourceReader selection={selection} onClose={()=>setSelection(null)}/>:<><RequestPlanner state={state} pending={pending} onEdit={onEdit} onSubmit={onSubmit}/>{state.quote&&!hasCalendar&&<Button className="find-time-button" kind="secondary" disabled={pending} onClick={()=>choose('When is this service free this week?')}>Find a time</Button>}</>}</div></div>;
}
