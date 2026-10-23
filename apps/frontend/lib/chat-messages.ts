import type {SessionState} from './api';

type Message=SessionState['messages'][number];
export type PendingMessage={key:string;text:string;count:number};

/** Only the next accepted user message can replace this local send. */
export function acceptedMessage(messages:Message[],pending:PendingMessage){
 const message=messages[pending.count];
 return message?.role==='user'&&message.text===pending.text?message:undefined;
}

/** Keep optimistic and accepted messages in one keyed list, with one DOM identity. */
export function conversationMessages(messages:Message[],pending:PendingMessage|null,keys:ReadonlyMap<string,string>){
 const accepted=pending&&acceptedMessage(messages,pending);
 const rows=messages.map(message=>({key:pending&&accepted?.id===message.id?pending.key:keys.get(message.id)??message.id,message}));
 if(pending&&!accepted)rows.push({key:pending.key,message:{id:pending.key,role:'user',text:pending.text,claims:[],cards:[],suggestions:[],requested_date:null,revision:0}});
 return rows;
}
