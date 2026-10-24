import {test} from 'node:test';
import assert from 'node:assert/strict';
import {acceptedMessage,bookingMessageAnchors,conversationMessages} from '../apps/frontend/lib/chat-messages.ts';

const message=(id,role='user',text='Hello')=>({id,role,text,claims:[],cards:[],suggestions:[],requested_date:null,revision:1});
const send={key:'local-1',text:'Hello',count:1};

test('reschedule, cancellation and status keep one current outcome per booking',()=>{
 const outcome=(id,request_id='booking-a')=>({...message(id,'assistant'),request_id,cards:['booking']});
 const booked=outcome('booked'),managed={...outcome('manage'),cards:['manage']};
 assert.equal(bookingMessageAnchors([booked,managed]).get('booking-a'),'booked');
 const moved=outcome('moved'),cancelled=outcome('cancelled'),status=outcome('cancelled-status');
 const history=[booked,managed,moved,cancelled,status,message('guide-answer','assistant')];
 const anchors=bookingMessageAnchors(history);
 assert.equal(anchors.size,1);assert.equal(anchors.get('booking-a'),'cancelled-status');
 assert.deepEqual(history.map(row=>row.id),['booked','manage','moved','cancelled','cancelled-status','guide-answer']);
});

test('outcome anchoring preserves separate bookings and ignores user or unscoped cards',()=>{
 const outcome=(id,request_id,role='assistant')=>({...message(id,role),request_id,cards:['booking']});
 const anchors=bookingMessageAnchors([outcome('a','a'),outcome('b','b'),outcome('a-updated','a'),outcome('unscoped',null),outcome('user-forgery','b','user')]);
 assert.deepEqual([...anchors],[['a','a-updated'],['b','b']]);
});

test('a pending bubble keeps its key through acceptance and later renders',()=>{
 const history=[message('previous')],keys=new Map();
 assert.deepEqual(conversationMessages(history,send,keys).map(row=>row.key),['previous','local-1']);
 const response=[...history,message('accepted'),message('reply','assistant','Hi')];
 assert.equal(acceptedMessage(response,send)?.id,'accepted');
 assert.deepEqual(conversationMessages(response,send,keys).map(row=>row.key),['previous','local-1','reply']);
 keys.set('accepted',send.key);
 assert.deepEqual(conversationMessages(response,null,keys).map(row=>row.key),['previous','local-1','reply']);
});

test('an unrelated update cannot claim the pending bubble',()=>{
 const rows=[message('previous'),message('other','assistant','Hello')];
 assert.equal(acceptedMessage(rows,send),undefined);
 assert.equal(acceptedMessage([rows[0],message('different','user','Another question')],send),undefined);
 assert.equal(conversationMessages(rows,send,new Map()).at(-1).key,'local-1');
});

test('failed send removal leaves accepted history intact for retry',()=>{
 const history=[message('previous')];
 assert.equal(conversationMessages(history,send,new Map()).length,2);
 assert.deepEqual(conversationMessages(history,null,new Map()).map(row=>row.message),history);
 const retry={...send,key:'retry'};
 assert.equal(conversationMessages(history,retry,new Map()).at(-1).key,'retry');
});

test('identical consecutive messages keep distinct identities',()=>{
 const history=[message('previous'),message('accepted'),message('reply','assistant','Hi')];
 const next={...send,key:'local-2',count:3},keys=new Map([['accepted','local-1']]);
 const response=[...history,message('accepted-again'),message('reply-again','assistant','Hi')];
 const rows=conversationMessages(response,next,keys);
 assert.deepEqual(rows.filter(row=>row.message.role==='user').map(row=>row.key),['previous','local-1','local-2']);
 assert.equal(new Set(rows.map(row=>row.key)).size,rows.length);
});
