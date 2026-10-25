import type {SessionState} from './api';
type Claim=SessionState['messages'][number]['claims'][number];
export function citationGroups(claims:Claim[]){
 const groups=new Map<string,{key:string;source:Claim;claims:Claim[]}>();
 for(const claim of claims){
  const key=claim.version_id+':'+claim.page;const group=groups.get(key)??{key,source:claim,claims:[]};
  if(!group.claims.some(value=>value.passage_id===claim.passage_id&&value.excerpt===claim.excerpt))group.claims.push(claim);
  groups.set(key,group);
 }
 return [...groups.values()];
}
export function reviewMessage(messages:SessionState['messages']){
 return messages.findLast(message=>message.role==='assistant'&&message.cards.some(card=>['quote','week','reserve','review'].includes(card)))?.id
  ??messages.find(message=>message.role==='assistant')?.id;
}
