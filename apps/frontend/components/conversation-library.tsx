'use client';
import {useRef} from 'react';
import {createPortal} from 'react-dom';
import type {KnowledgeDocument} from '@/lib/api';
import {DOCUMENT_QUESTIONS,QUESTION_GROUPS} from '@/lib/chat-questions';
import {GuestGuideShelf} from './guide-papers';
import {useDialogFocus} from './use-dialog-focus';
import {Button} from './ui';

export function ConversationLibrary({kind,documents,onClose,onQuestion,onTour}:{kind:'questions'|'guides';documents:KnowledgeDocument[];onClose:()=>void;onQuestion:(text:string)=>void;onTour:()=>void}){
 const panel=useRef<HTMLElement>(null);useDialogFocus(panel,onClose);
 return createPortal(<div className="conversation-library-layer"><section className="conversation-library" role="dialog" aria-modal="true" aria-labelledby="conversation-library-title" ref={panel}><header><h2 id="conversation-library-title">{kind==='guides'?'Juniper’s documents':'More questions'}</h2><Button kind="quiet" onClick={onClose} aria-label="Close conversation library">Close</Button></header>{kind==='guides'?<GuestGuideShelf documents={documents}/>:<><Button kind="secondary" className="question-library-tour" onClick={onTour}>Take a quick tour <span aria-hidden="true">↗</span></Button><section className="document-question-examples"><h3>Ask Juniper’s documents</h3><div>{DOCUMENT_QUESTIONS.map(question=><button type="button" key={question.document} onClick={()=>onQuestion(question.text)}><small>{question.document}</small><span>{question.text}</span><span aria-hidden="true">↗</span></button>)}</div></section><div className="question-library-groups">{QUESTION_GROUPS.map(group=><section key={group.name}><h3>{group.name}</h3>{group.questions.filter(question=>!DOCUMENT_QUESTIONS.some(example=>example.text===question)).map(question=><button type="button" key={question} onClick={()=>onQuestion(question)}>{question}<span aria-hidden="true">↗</span></button>)}</section>)}</div></>}</section></div>,document.body);
}
