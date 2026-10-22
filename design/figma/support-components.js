const page=await figma.getNodeByIdAsync(STATE.entities.pages['01 · Design System']);await figma.setCurrentPageAsync(page);
const variableDelta={};const semantic=await figma.variables.getVariableCollectionByIdAsync(STATE.entities.collections.semantic.id);
const prototypeValues={
  Draft:"I'm moving out of my two-bedroom apartment on Friday 30 October at 09:00. Does that include carpet shampooing? I have two cats. Can you add the oven?",
  PathOpenWeek:false,
  Service:'Move-out · 2 bedrooms',Details:'Oven add-on · 4 hr 30 min',BasePrice:'$160',AddonLabel:'Oven cleaning',AddonPrice:'$25',Total:'$185',Duration:'4 hr 30 min',
  CalendarContext:'Move-out + oven · 4 hr 30 min · Your local time',
  Slot:'Saturday 31 October · 09:00–13:30 · Your local time',Time:'09:00–13:30 · Your local time',
  ReceiptSummary:'Move-out · 2 bedrooms · oven\nSaturday 31 October, 09:00–13:30\nYour local time · Ada · $185'
};
for(const [name,value] of Object.entries(prototypeValues)){
  let v=V['Prototype/'+name];if(!v){v=figma.variables.createVariable('Prototype/'+name,semantic,typeof value==='boolean'?'BOOLEAN':'STRING');v.setValueForMode(semantic.modes[0].modeId,value);v.scopes=typeof value==='boolean'?['ALL_SCOPES']:['TEXT_CONTENT'];v.setVariableCodeSyntax('WEB','var(--prototype-'+name.toLowerCase()+')');}variableDelta[v.name]=v.id;
}
let y=STATE.showcaseStats?Math.max(...Object.values(C).map(n=>n.y+n.height))+120:12000;
function locate(n){n.x=2040;n.y=y;y+=n.height+64;C[n.name]=n;return n;}
function textProp(c,name,value,style='Type/Body/M',width=c.width-40,color='Color/Text/Primary'){const n=txt(c,name,value,style,width,color);n.layoutSizingHorizontal='FILL';prop(c,n,name,value);return n;}
const step=ownComponent('Landing/Step',416,'VERTICAL',16,24,'Color/Background/Surface',12);bindStroke(step);textProp(step,'Index','01','Type/Display/M',368,'Color/Text/Brand');textProp(step,'Title','A helpful conversation.','Type/Title/M',368);textProp(step,'Body','Ask about the service, supplies and preparation. See the guidance behind each answer.','Type/Body/M',368,'Color/Text/Secondary');locate(step);
const user=ownComponent('Chat/UserMessage',736,'VERTICAL',8,16,'Color/Background/Subtle',12);textProp(user,'Label','You','Type/Label/S',704,'Color/Text/Brand');textProp(user,'Body','Can I book Friday morning?','Type/Body/M',704);locate(user);
const assistant=ownComponent('Chat/AssistantText',736,'VERTICAL',8,16,null,0);const ai=auto(assistant,'Identity',704,'HORIZONTAL',8);inst(ai,'Assistant icon',C['Icon/Spark']);oneLine(ai,'Name','Juniper assistant','Type/Label/S','Color/Text/Brand');textProp(assistant,'Body','Let’s find a time that fits your whole clean.','Type/Body/M',704);locate(assistant);
const choice=ownComponent('Chat/StartChoice',736,'HORIZONTAL',16,20,'Color/Background/Surface',12);bindStroke(choice);choice.counterAxisAlignItems='CENTER';const cc=auto(choice,'Copy',632,'VERTICAL',4);const title=txt(cc,'Title','Moving out + a preferred day','Type/Title/S',632);prop(choice,title,'Title','Moving out + a preferred day');const body=txt(cc,'Body','Carpets, pets, an oven and a morning appointment.','Type/Body/S',632,'Color/Text/Secondary');prop(choice,body,'Body','Carpets, pets, an oven and a morning appointment.');inst(choice,'Chevron',C['Icon/Chevron']);locate(choice);
const sidebar=ownComponent('Navigation/DemoSidebar',208,'VERTICAL',24,0,null,0);txt(sidebar,'Workspace label','YOUR DEMO','Type/Label/S',208,'Color/Text/Secondary');txt(sidebar,'Company','Juniper\nCleaning','Type/Title/M',208);badge(sidebar,'Customer','Neutral');for(const [label,tone]of [['Your request','Selected'],['Questions to try','Default'],['Services','Default'],['Sources','Default']])chip(sidebar,label,tone,label);txt(sidebar,'Local zone','Your local time','Type/Body/S',208,'Color/Text/Secondary');txt(sidebar,'Scenario context','Fictional company.\nA private workspace, just for you.','Type/Caption',208,'Color/Text/Secondary');locate(sidebar);
const quote=C['Quote/Review'];for(const name of ['Base','Addon']){const r=quote.children.find(n=>n.name===name);const n=r.children.find(n=>n.type==='TEXT'&&n.name==='Label');const key=quote.addComponentProperty(name==='Base'?'Service':'AddonLabel','TEXT',n.characters);n.componentPropertyReferences={characters:key};mutatedNodeIds.push(n.id);}mutatedNodeIds.push(quote.id);
for(const n of C['Service/Card'].children)if(n.type==='TEXT'){n.layoutSizingHorizontal='FILL';mutatedNodeIds.push(n.id);}
const swatch=page.findOne(n=>n.name==='Swatch · Surface');if(swatch){const block=swatch.children.find(n=>n.name==='Bound colour');bindStroke(block);mutatedNodeIds.push(block.id);}
return {createdNodeIds:[...new Set(createdNodeIds)],mutatedNodeIds,entityDelta:{components,variables:variableDelta},stats:{supportComponents:Object.keys(components).length,prototypeVariables:Object.keys(variableDelta).length}};
