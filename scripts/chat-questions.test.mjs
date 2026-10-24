import {test} from 'node:test';
import assert from 'node:assert/strict';
import {QUESTION_GROUPS,GUIDE_SHORTCUTS,conversationShortcuts,isTourRequest} from '../apps/frontend/lib/chat-questions.ts';
const state=(fields={})=>({draft:{service:null,bedrooms:null,preferred_at:null},messages:[],quote:null,requests:[],...fields});
const message=(role,text='',suggestions=[])=>({role,text,suggestions});

test('explicit chat tour commands support polite requests and replay',()=>{
 for(const text of ['/tour','Show me the tour','Restart the quick tour.','Can you please show me a tour?','Could I take the guided tour, please?','Give me a tour of the app','  show   me   around  '])assert.equal(isTourRequest(text),true,text);
});

test('tour routing leaves business questions and unrelated free text alone',()=>{
 for(const text of ['', 'Help me choose','What cleaning supplies do you use?','Show me the booking','Do you offer tours?','Show availability for a tour group.','How does the tour work?','/tour tomorrow','tour for my booking',...QUESTION_GROUPS.flatMap(group=>group.questions)])assert.equal(isTourRequest(text),false,text);
});

test('initial suggestions stay bounded while the optional bank retains all 24 distinct questions',()=>{
 assert.equal(new Set(QUESTION_GROUPS.flatMap(group=>group.questions)).size,24);
 const choices=conversationShortcuts(state());assert.equal(choices.length,4);assert.ok(choices.every(choice=>choice.label&&choice.text));
});
test('expected replies advance from service to home size to real availability',()=>{
 const messages=[message('assistant')];
 assert.deepEqual(conversationShortcuts(state({messages})).slice(0,3).map(row=>row.text),['I’d like a regular clean.','I’d like a deep clean.','I’d like a move-out clean.']);
 assert.deepEqual(conversationShortcuts(state({messages,draft:{service:'regular',bedrooms:null}})).slice(0,3).map(row=>row.text),['1 bedroom, please.','2 bedrooms, please.','3 bedrooms, please.']);
 assert.equal(conversationShortcuts(state({messages,draft:{service:'regular',bedrooms:2,preferred_at:null},quote:{}}))[0].text,'When is this service free this week?');
});
test('backend suggestions are retained, deduplicated and skip the recent question',()=>{
 const suggestions=[{label:'Again',text:'  What cleaning supplies do you use?  '},{label:'Policy',text:'How do rescheduling and cancellation work?'},{label:'Duplicate policy',text:'HOW DO RESCHEDULING AND CANCELLATION WORK?'}];
 const choices=conversationShortcuts(state({draft:{service:'regular',bedrooms:2,preferred_at:'2026-10-26'},messages:[message('user','What cleaning supplies do you use?'),message('assistant','',suggestions)]}));
 assert.equal(choices.filter(row=>row.label==='Policy').length,1);assert.equal(choices.some(row=>row.label==='Again'||row.label==='Duplicate policy'),false);assert.ok(choices.length<=4);
});
test('pending/confirmed booking suggestions prefer the actual lifecycle over a reset draft',()=>{
 const messages=[message('assistant')];
 assert.equal(conversationShortcuts(state({messages,requests:[{status:'awaiting_review'}]}))[0].label,'Changes & cancellations');
 const choices=conversationShortcuts(state({messages,requests:[{status:'confirmed'}]}));
 assert.equal(choices[0].label,'Reschedule my booking');assert.match(choices[0].text,/reschedule my appointment/);
 assert.equal(choices[1].label,'Cancel my booking');assert.match(choices[1].text,/cancel my appointment/);
});

test('every conversation state keeps guide discovery beside contextual replies',()=>{
 const guideText=new Set(GUIDE_SHORTCUTS.map(row=>row.text));
 for(const fields of [{},{draft:{service:'regular'}},{draft:{service:'regular',bedrooms:2},quote:{}},
  {requests:[{status:'confirmed'}]},{requests:[{status:'cancelled'}]}]){
  const choices=conversationShortcuts(state({messages:[message('assistant')],...fields}));
  assert.equal(choices.length,4);assert.ok(choices.some(row=>guideText.has(row.text)));
 }
});

test('a source follow-up wins over booking defaults and still leaves two discovery questions',()=>{
 const followups=[{label:'Oven preparation',text:'How do I prepare the oven?'},{label:'Arrange access',text:'How do I arrange access for the cleaner?'}];
 const choices=conversationShortcuts(state({requests:[{status:'confirmed'}],messages:[message('user','What should I do with my pets?'),{...message('assistant','',followups),claims:[{title:'Preparation Guide'}]}]}));
 assert.deepEqual(choices.slice(0,2),followups);assert.equal(choices.length,4);
 assert.ok(choices.every(row=>row.text!=='What should I do with my pets?'));
});
