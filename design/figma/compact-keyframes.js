// Inject STATE. Fold conversation states into one reusable component and retire routing copies.
figma.skipInvisibleInstanceChildren=false;const page=await figma.getNodeByIdAsync('15:3');await figma.setCurrentPageAsync(page);
if(page.findAllWithCriteria({types:['COMPONENT_SET']}).some(n=>n.name==='Workspace/CustomerState'))throw new Error('Inspect existing compact run before retrying');
const texts=page.findAllWithCriteria({types:['TEXT']});const fonts=new Map();for(const n of texts)for(const s of n.getStyledTextSegments(['fontName']))fonts.set(JSON.stringify(s.fontName),s.fontName);await Promise.all([...fonts.values()].map(f=>figma.loadFontAsync(f)));
const F=STATE.entities.frames,created=[],mutated=[],removed=[],states={},links=[];
const defs=[['Start','D03 · Visual chat · Start'],['OpenDraft','D03A · Visual chat · Open-week draft'],['Source','D04 · Visual chat · Sources'],['BusyWeek','D05 · Scheduling · Busy first choice'],['OpenWeek','D06 · Scheduling · Open week'],['Quote','D07 · Quote review']];
for(const[name,key]of defs){const root=await figma.getNodeByIdAsync(F[key]);const body=root.children.find(n=>n.name==='Workspace');if(!body)throw new Error('Workspace missing: '+key);const clone=body.clone();page.appendChild(clone);clone.x=11000;clone.y=80;const c=figma.createComponentFromNode(clone);c.name='State='+name;c.description='Customer conversation state. Shared controls, cards and text styles remain linked.';states[name]=c;created.push(c.id,...c.findAll(()=>true).map(n=>n.id));for(const n of [c,...c.findAll(()=>true)])if('reactions'in n&&n.reactions.length){await n.setReactionsAsync([]);mutated.push(n.id);}}
const set=figma.combineAsVariants(Object.values(states),page);set.name='Workspace/CustomerState';set.description='Six conversation states for the two scheduling routes. One key-frame instance; basic native Change to interactions.';set.layoutMode='NONE';set.resize(3008,2928);set.x=11000;set.y=80;Object.values(states).forEach((c,i)=>{c.x=32+(i%2)*1504;c.y=32+Math.floor(i/2)*976;});created.push(set.id);
const key=await figma.getNodeByIdAsync(F['D03 · Visual chat · Start']);const oldBody=key.children.find(n=>n.name==='Workspace');removed.push(oldBody.id);oldBody.remove();const instance=states.Start.createInstance();key.appendChild(instance);instance.name='Conversation';instance.resize(1440,912);created.push(instance.id,...instance.findAll(()=>true).map(n=>n.id));mutated.push(key.id);
const nav=(target,change=false)=>({type:'NODE',destinationId:typeof target==='string'?target:target.id,navigation:change?'CHANGE_TO':'NAVIGATE',transition:{type:'DISSOLVE',easing:{type:'EASE_OUT'},duration:.2}});
async function link(node,target,change=false){if(!node)throw new Error('Missing prototype control');await node.setReactionsAsync([{trigger:{type:'ON_CLICK'},actions:[nav(target,change)]}]);mutated.push(node.id);links.push({source:node.id,target:typeof target==='string'?target:target.id,kind:change?'CHANGE_TO':'NAVIGATE'});}
const by=(root,name)=>root.findAllWithCriteria({types:['INSTANCE']}).find(n=>n.name===name);
await link(by(states.Start,'Starter · open week'),states.OpenDraft,true);await link(by(states.Start,'Quick week'),states.OpenDraft,true);
await link(by(states.OpenDraft,'Starter · busy first choice'),states.Start,true);
await link(by(states.Start,'Send'),states.Source,true);await link(by(states.OpenDraft,'Send'),states.OpenWeek,true);
await link(by(states.Source,'Show the week'),states.BusyWeek,true);await link(by(states.Source,'When is it free this week?'),states.OpenWeek,true);
for(const s of [states.BusyWeek,states.OpenWeek]){await link(by(s,'Use time'),states.Quote,true);await link(by(s,'Day/SAT'),states.Quote,true);}
await link(by(states.Quote,'Send request'),F['D09 · Business approval']);
for(const[name,s]of Object.entries(states))if(name!=='Start')await link(by(s,'Questions to try'),states.Start,true);
const keepKeys=['D01 · Landing','D02 · Demo entry','D03 · Visual chat · Start','D09 · Business approval','D10 · Booking · HubSpot connected','D11 · Booking · No CRM','M01 · Landing'];
const keep=new Set(keepKeys.map(k=>F[k]));
for(const[name,id]of Object.entries(F)){if(keep.has(id)||!/^D\d|^P · Connected/.test(name))continue;const n=await figma.getNodeByIdAsync(id);if(n&&!n.removed){removed.push(n.id,...n.findAll(()=>true).map(c=>c.id));n.remove();}}
const section=await figma.getNodeByIdAsync(F.ConnectedRoutingSection);if(section&&!section.removed){removed.push(section.id);section.remove();}
const entry=await figma.getNodeByIdAsync(F['D02 · Demo entry']);await link(by(entry,'Continue without CRM'),key);
await by(entry,'Connect HubSpot').setReactionsAsync([]);mutated.push(by(entry,'Connect HubSpot').id);
const business=await figma.getNodeByIdAsync(F['D09 · Business approval']);await link(by(business,'Confirm booking'),F['D11 · Booking · No CRM']);
for(const k of ['D10 · Booking · HubSpot connected','D11 · Booking · No CRM']){const root=await figma.getNodeByIdAsync(F[k]);await link(by(root,'Finish demo'),entry);await link(by(root,'Back to customer'),key);}
for(const k of keepKeys){const root=await figma.getNodeByIdAsync(F[k]);const switcher=by(root,'Switch perspective');if(switcher&&switcher.visible&&root.id!==business.id)await link(switcher,business);}
const names=['K01 · Landing','K02 · Demo entry','K03 · Customer workspace','K04 · Business review','K06 · Booking · HubSpot','K05 · Booking · No CRM','M01 · Landing'];const keyFrames={};
for(let i=0;i<keepKeys.length;i++){const root=await figma.getNodeByIdAsync(F[keepKeys[i]]);root.name=names[i];root.x=80+(i<6?i%3:0)*1520;root.y=80+(i<6?Math.floor(i/3):2)*1120;keyFrames[root.name]=root.id;mutated.push(root.id);}
page.flowStartingPoints=[{nodeId:F['D01 · Landing'],name:'Booking demo · Two scheduling paths'},{nodeId:F['D10 · Booking · HubSpot connected'],name:'Connected HubSpot outcome'}];mutated.push(page.id);
return {createdNodeIds:[...new Set(created)],mutatedNodeIds:[...new Set(mutated)],removedNodeIds:[...new Set(removed)],entityDelta:{keyFrames,customerStateSet:set.id,customerStates:Object.fromEntries(Object.entries(states).map(([n,c])=>[n,c.id])),customerInstance:instance.id},prototypeLinks:links,stats:{desktopKeyFrames:6,mobileLandingFrames:1,conversationStates:6,routingCopies:0}};
