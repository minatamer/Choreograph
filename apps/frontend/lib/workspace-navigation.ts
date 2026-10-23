export const businessPages=[
 {id:'overview',label:'Overview',description:'Your day, at a glance.'},
 {id:'requests',label:'Requests',description:'Review, assign and arrange.'},
 {id:'calendar',label:'Calendar',description:'A little room for the whole week.'},
 {id:'guides',label:'Documents',description:'The knowledge behind the conversation.'},
 {id:'connections',label:'Connections',description:'Your tools, working together.'},
] as const;
export type BusinessPage=typeof businessPages[number]['id'];
export function workspaceLocation(search:string){
 const params=new URLSearchParams(search),candidate=params.get('section');
 return {business:params.get('view')==='business',page:businessPages.some(item=>item.id===candidate)?candidate as BusinessPage:'overview' as BusinessPage};
}
export function workspaceSearch(search:string,business:boolean,page:BusinessPage){
 const params=new URLSearchParams(search);params.set('view',business?'business':'customer');
 if(page==='overview')params.delete('section');else params.set('section',page);
 return '?'+params.toString();
}
