// Starter-plan prototype: one native navigation action per reaction; no paid advanced logic.
const page=await figma.getNodeByIdAsync(STATE.entities.pages['02 · Key Screens']);await figma.setCurrentPageAsync(page);
const F={...STATE.entities.frames},H={...STATE.entities.hotspots},wired=[];
const nav=id=>({type:'NODE',destinationId:id,navigation:'NAVIGATE',transition:{type:'DISSOLVE',easing:{type:'EASE_OUT'},duration:.24}});
async function link(node,target,trigger={type:'ON_CLICK'}){const n=typeof node==='string'?await figma.getNodeByIdAsync(node):node;const targetId=typeof target==='string'?target:target.id;let ancestor=n;while(ancestor){if(ancestor.id===targetId)return;ancestor=ancestor.parent;}await n.setReactionsAsync([{trigger,actions:[nav(targetId)]}]);mutatedNodeIds.push(n.id);wired.push({id:n.id,name:n.name,trigger:trigger.type,destination:targetId});}
const moveDraft="I'm moving out of my two-bedroom apartment on Friday 30 October at 09:00. Does that include carpet shampooing? I have two cats. Can you add the oven?";
const weekDraft="I'd like a move-out clean for my two-bedroom apartment, with the oven. When is it free this week?";
function prepareDraft(root,value){const comp=instanceByName(root,'Composer');setText(comp,{Draft:value});const draft=componentText(comp,'Draft'),hint=componentText(comp,'Empty draft hint');draft.setBoundVariable('visible',null);draft.visible=true;hint.setBoundVariable('visible',null);hint.visible=false;comp.layoutSizingVertical='HUG';mutatedNodeIds.push(comp.id,draft.id,hint.id);}
function resetComposer(root){const comp=instanceByName(root,'Composer');if(comp){comp.layoutSizingVertical='HUG';mutatedNodeIds.push(comp.id);}}
function frameText(root,name,value){const t=componentText(root,name);if(t){t.characters=value;mutatedNodeIds.push(t.id);}}
// Keep one canonical service/quote through both discovery paths; the real app still supports the full catalogue.
const open=await figma.getNodeByIdAsync(F['D06 · Scheduling · Open week']);
setText(instanceByName(open,'Your message'),{Body:weekDraft});setText(instanceByName(open,'Assistant reply'),{Body:'Here’s the week for your 4 hr 30 min move-out clean with the oven. Choose a free time; I’ll keep the quote and your request together.'});
const openWeek=instanceByName(open,'Interactive week');setText(openWeek,{Context:'Move-out + oven · 4 hr 30 min · Your local time',Alternative:'Saturday 09:00 fits your whole clean.'});
for(const[d,date,state,time]of [['MON','26','Available','09:00\n13:30'],['TUE','27','Available','10:00\n14:30'],['THU','29','Available','09:00\n13:30'],['SAT','31','Selected','09:00\n13:30']]){const day=instanceByName(openWeek,'Day/'+d);day.swapComponent(C['Calendar/Day'].children.find(c=>c.name==='State='+state));setText(day,{Day:d,Date:date,Status:state==='Selected'?'Suggested':'Free',Time:time});}
setText(instanceByName(openWeek,'Day/FRI'),{Status:'Booked'});setText(instanceByName(openWeek,'Use time'),{Label:'Use Saturday 09:00'});
setText(instanceByName(open,'Request summary'),{Service:'Move-out · 2 bedrooms',Details:'Oven add-on · 4 hr 30 min',Total:'$185',Date:'Choose a day from this week',Time:'Your local time',Note:'Every offered time fits the whole service.'});mutatedNodeIds.push(open.id);
const start=await figma.getNodeByIdAsync(F['D03 · Visual chat · Start']);prepareDraft(start,moveDraft);setText(instanceByName(start,'Starter · open week'),{Title:'A move-out clean · what’s free this week?',Body:'Two bedrooms and the oven. Explore the week directly.'});
bindStroke(instanceByName(start,'Starter · busy first choice'),'Color/Action/Primary');
const openStart=track(start.clone());page.appendChild(openStart);openStart.name='D03A · Visual chat · Open-week draft';openStart.x=1600;openStart.y=4640;F[openStart.name]=openStart.id;frames[openStart.name]=openStart.id;prepareDraft(openStart,weekDraft);bindStroke(instanceByName(openStart,'Starter · busy first choice'));bindStroke(instanceByName(openStart,'Starter · open week'),'Color/Action/Primary');allCreatedUnder(openStart);

const connectedSection=track(figma.createSection());connectedSection.name='Prototype routing · HubSpot connected · linked instances';connectedSection.x=4800;connectedSection.y=80;connectedSection.resizeWithoutConstraints(4560,3440);frames.ConnectedRoutingSection=connectedSection.id;
const baseNames=['D03 · Visual chat · Start','D03A · Visual chat · Open-week draft','D04 · Visual chat · Sources','D05 · Scheduling · Busy first choice','D06 · Scheduling · Open week','D07 · Quote review','D08 · Awaiting review','D09 · Business approval'];
const connected={};
for(let i=0;i<baseNames.length;i++){
  const original=await figma.getNodeByIdAsync(F[baseNames[i]]);const clone=track(original.clone());connectedSection.appendChild(clone);clone.name='P · Connected / '+baseNames[i];clone.x=40+(i%3)*1520;clone.y=40+Math.floor(i/3)*1120;connected[baseNames[i]]=clone;frames[clone.name]=clone.id;allCreatedUnder(clone);
  const header=instanceByName(clone,'App header');if(header)frameText(header,'Business','Juniper Cleaning · HubSpot connected');
  if(baseNames[i]==='D07 · Quote review'){const exportBlock=clone.findOne(n=>n.name==='Connected export consent');exportBlock.setBoundVariable('visible',null);exportBlock.visible=true;mutatedNodeIds.push(exportBlock.id);}
}
async function wireRoute(map,connectedCRM){
  const get=name=>map[name];
  const busyStart=get('D03 · Visual chat · Start'),weekStart=get('D03A · Visual chat · Open-week draft');
  for(const s of [busyStart,weekStart]){await link(instanceByName(s,'Starter · busy first choice'),busyStart);await link(instanceByName(s,'Starter · open week'),weekStart);const quick=s.findOne(n=>n.type==='INSTANCE'&&n.name==='Quick week');if(quick)await link(quick,weekStart);}
  await link(instanceByName(instanceByName(busyStart,'Composer'),'Send'),get('D04 · Visual chat · Sources'));
  await link(instanceByName(instanceByName(weekStart,'Composer'),'Send'),get('D06 · Scheduling · Open week'));
  const source=get('D04 · Visual chat · Sources'),answer=instanceByName(source,'Grounded answer');await link(instanceByName(answer,'Show the week'),get('D05 · Scheduling · Busy first choice'));
  const direct=source.findOne(n=>n.type==='INSTANCE'&&n.name==='When is it free this week?');if(direct)await link(direct,get('D06 · Scheduling · Open week'));
  for(const name of ['D05 · Scheduling · Busy first choice','D06 · Scheduling · Open week']){const w=instanceByName(get(name),'Interactive week');await link(instanceByName(w,'Use time'),get('D07 · Quote review'));await link(instanceByName(w,'Day/SAT'),get('D07 · Quote review'));}
  await link(instanceByName(instanceByName(get('D07 · Quote review'),'Quote review'),'Send request'),get('D08 · Awaiting review'));
  const awaiting=get('D08 · Awaiting review');const review=awaiting.findOne(n=>n.type==='INSTANCE'&&n.name==='Review as business');await link(review,get('D09 · Business approval'));
  const approve=get('D09 · Business approval').findOne(n=>n.type==='INSTANCE'&&n.name==='Confirm booking');await link(approve,connectedCRM?F['D10A · Booking · CRM pending']:F['D11 · Booking · No CRM']);
  for(const name of baseNames){const f=get(name);resetComposer(f);const comp=instanceByName(f,'Composer');if(comp)await link(instanceByName(comp,'Questions to try'),busyStart);const header=instanceByName(f,'App header');if(header&&name==='D08 · Awaiting review')await link(instanceByName(header,'Switch perspective'),get('D09 · Business approval'));}
}
const base={};for(const name of baseNames)base[name]=await figma.getNodeByIdAsync(F[name]);await wireRoute(base,false);await wireRoute(connected,true);
for(const name of ['landing-try','landing-footer-try','mobile-try','mobile-footer-try'])await link(H[name],F['D02 · Demo entry']);
await link(H['entry-connect'],connected['D03 · Visual chat · Start']);await link(H['entry-skip'],base['D03 · Visual chat · Start']);
await link(F['D10A · Booking · CRM pending'],F['D10 · Booking · HubSpot connected'],{type:'AFTER_TIMEOUT',timeout:1});
for(const[prefix,back]of [['connected',connected['D04 · Visual chat · Sources']],['skipped',base['D04 · Visual chat · Sources']]]){
  const finish=await figma.getNodeByIdAsync(H[prefix+'-finish']);if(prefix==='connected')setText(finish,{Label:'Finish & disconnect'});await link(finish,F['D02 · Demo entry']);await link(H[prefix+'-back'],back);
}
const landing=await figma.getNodeByIdAsync(F['D01 · Landing']);const rail=instanceByName(landing,'Indexed navigation');await link(rail.findOne(n=>n.name==='Rail · Try demo'),F['D02 · Demo entry']);
page.flowStartingPoints=[{nodeId:F['D01 · Landing'],name:'Choreograph · Visual front desk'}];mutatedNodeIds.push(page.id);
const note=txt(page,'Prototype route note','PROTOTYPE / BASIC NATIVE LINKS\nMain frames: no-CRM route. Separate routing group: connected route.\nBoth scheduling paths use the canonical $185 / 4½-hour clean and Saturday alternative.\nChoose a starter, then Send. Other free-text/question states are design examples; external OAuth/HubSpot actions are not executed.','Type/Body/M',1350,'Color/Text/Secondary');note.x=80;note.y=-120;
return {createdNodeIds:[...new Set(createdNodeIds)],mutatedNodeIds:[...new Set(mutatedNodeIds)],entityDelta:{frames},prototype:{wired,startingPoints:page.flowStartingPoints,plan:'Starter; single-action native links',connectedBranch:Object.fromEntries(Object.entries(connected).map(([k,n])=>[k,n.id]))},stats:{hotspots:wired.length,schedulingPaths:2,crmOutcomes:2,distinctScreenFamilies:5,routingCopies:baseNames.length,advancedPrototypeActions:0}};
