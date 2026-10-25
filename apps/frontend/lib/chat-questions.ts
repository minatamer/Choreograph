import type {SessionState} from './api';

export const QUESTION_GROUPS=[
 {name:'Services',questions:["What’s included in move-out cleaning?",'Do you offer carpet shampooing?','Can I add oven cleaning?','Can you move heavy furniture?']},
 {name:'Getting ready',questions:['What should I do with my pets?','How should I prepare the apartment?','How do I arrange access for the cleaner?','How do I prepare the oven?']},
 {name:'Supplies',questions:['What cleaning supplies do you use?','How do you clean a kitchen?','Do I need to provide equipment?','Can I request fragrance-free products?']},
 {name:'Quote & time',questions:['Show a quote for a two-bedroom move-out with the oven.','What morning appointments are available?','I need a clean tomorrow.','When is this service free this week?']},
 {name:'Changes & limits',questions:['How do rescheduling and cancellation work?','Can you guarantee I get my deposit back?','What if my preferred time is unavailable?','Do you remove mould or pests?']},
 {name:'Make a change',questions:['Remove the oven.','Make that a deep clean instead.','Three bedrooms instead.','What is your service area?']},
] as const;

export type ChatShortcut={label:string;text:string};
export const RESERVATION_SHORTCUT:ChatShortcut={label:'Reserve an appointment',text:'Reserve an appointment.'};
export const DOCUMENT_QUESTIONS=[
 {document:'Service Guide',text:QUESTION_GROUPS[0].questions[1]},
 {document:'Preparation Guide',text:QUESTION_GROUPS[1].questions[0]},
 {document:'Access and Arrival',text:QUESTION_GROUPS[1].questions[2]},
 {document:'Changes and Cancellations',text:QUESTION_GROUPS[4].questions[0]},
 {document:'Safety and Exclusions',text:QUESTION_GROUPS[4].questions[3]},
 {document:'Service Questions',text:QUESTION_GROUPS[5].questions[3]},
] as const;
export function isTourRequest(text:string):boolean{
 const command=text.trim().toLowerCase().replace(/[.!?]+$/,'').replace(/\s+/g,' ')
  .replace(/^(?:(?:can|could|would) you |(?:can|could|may) i |please )/,'')
  .replace(/^please /,'').replace(/,? please$/,'');
 return /^(?:\/tour|(?:a |the )?(?:quick |guided )?tour|(?:show(?: me)?|start|restart|replay|open|take|give me)(?: (?:a|the))? (?:quick |guided )?tour|show me around)(?: of (?:the )?(?:app|website|workspace))?$/.test(command);
}
const initialQuestions:ChatShortcut[]=[
 {label:'What’s included?',text:QUESTION_GROUPS[0].questions[0]},
 {label:'Supplies & equipment',text:QUESTION_GROUPS[2].questions[0]},
 {label:'Pets at home',text:QUESTION_GROUPS[1].questions[0]},
 {label:'Find a time',text:QUESTION_GROUPS[3].questions[3]},
];
export const GUIDE_SHORTCUTS:ChatShortcut[]=[
 {label:'What’s included?',text:QUESTION_GROUPS[0].questions[0]},
 {label:'Pets at home',text:QUESTION_GROUPS[1].questions[0]},
 {label:'Supplies & equipment',text:QUESTION_GROUPS[2].questions[2]},
 {label:'Cleaning methods',text:QUESTION_GROUPS[2].questions[1]},
 {label:'Arrange access',text:QUESTION_GROUPS[1].questions[2]},
 {label:'Changes & cancellations',text:QUESTION_GROUPS[4].questions[0]},
 {label:'Unscented products',text:QUESTION_GROUPS[2].questions[3]},
 {label:'Service area',text:QUESTION_GROUPS[5].questions[3]},
 {label:'Deposit guarantee?',text:QUESTION_GROUPS[4].questions[1]},
 {label:'Safety & exclusions',text:QUESTION_GROUPS[4].questions[3]},
 {label:'Prepare the oven',text:QUESTION_GROUPS[1].questions[3]},
];
export function conversationShortcuts(state:Pick<SessionState,'messages'|'draft'|'quote'|'requests'>):ChatShortcut[]{
 if(!state.messages.length)return initialQuestions;
 const latest=state.messages.findLast(message=>message.role==='assistant');
 const request=state.requests.at(-1);
 let expected:ChatShortcut[]=[];
 if(request?.status==='awaiting_review')expected=[{label:'Changes & cancellations',text:QUESTION_GROUPS[4].questions[0]},{label:'Get ready for the clean',text:QUESTION_GROUPS[1].questions[1]}];
 else if(request?.status==='confirmed')expected=[{label:'Reschedule my booking',text:'I’d like to reschedule my appointment.'},{label:'Cancel my booking',text:'I’d like to cancel my appointment.'}];
 else if(!state.draft.service)expected=['Regular','Deep','Move-out'].map(service=>({label:service+' clean',text:`I’d like a ${service.toLowerCase()} clean.`}));
 else if(!state.draft.bedrooms)expected=[1,2,3].map(count=>({label:`${count} bedroom${count>1?'s':''}`,text:`${count} bedroom${count>1?'s':''}, please.`}));
 else if(state.quote&&!state.draft.preferred_at)expected=[{label:'Find a time',text:QUESTION_GROUPS[3].questions[3]},{label:'Morning appointments',text:QUESTION_GROUPS[3].questions[1]}];
 else expected=[{label:'Review my booking',text:'Book it, please.'},{label:'Getting ready',text:QUESTION_GROUPS[1].questions[1]}];
 const normalize=(value:string)=>value.trim().toLocaleLowerCase().replace(/[.!?]+$/,'');
 const seen=new Set(state.messages.slice(-8).filter(message=>message.role==='user').map(message=>normalize(message.text)));
 const choices:ChatShortcut[]=[];
 const choosingDetails=!request&&(!state.draft.service||!state.draft.bedrooms)&&!latest?.claims?.length;
 const add=(choice:ChatShortcut)=>{const key=normalize(choice.text);if(!key||seen.has(key))return;seen.add(key);choices.push(choice);};
 const contextual=choosingDetails||request&&!latest?.claims?.length?expected:[...(latest?.suggestions??[]),...expected];
 for(const choice of contextual){add(choice);if(choices.length===(choosingDetails?3:2))break;}
 // Reserve room for discovery even when all three home-size replies are useful.
 // Rotate through real guide topics; never treat these samples as retrieved evidence.
 const turn=state.messages.filter(message=>message.role==='user').length;
 const offset=turn%GUIDE_SHORTCUTS.length;
 const guides=[...GUIDE_SHORTCUTS.slice(offset),...GUIDE_SHORTCUTS.slice(0,offset)];
 for(const choice of [...guides,...contextual,...initialQuestions]){add(choice);if(choices.length===4)break;}
 return choices;
}
