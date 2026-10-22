// Uses helpers.js and the provided createComponentWithVariants helper (page switch removed).
const page=await figma.getNodeByIdAsync(STATE.entities.pages['01 · Design System']);
await figma.setCurrentPageAsync(page);
let mainY=80;
function locate(n){page.appendChild(n);n.x=2040;n.y=mainY;mainY+=n.height+64;return n;}
const iconPaths={
  'ArrowRight':'<path d="M4 12h15m-6-6 6 6-6 6"/>',
  'Chevron':'<path d="m9 5 7 7-7 7"/>',
  'Calendar':'<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M7 3v4m10-4v4M3 10h18m-13 5h2m4 0h2"/>',
  'Document':'<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Z"/><path d="M14 3v6h6M8 13h8m-8 4h6"/>',
  'Check':'<path d="m5 12 4 4L19 6"/>',
  'Plus':'<path d="M12 5v14M5 12h14"/>',
  'Spark':'<path d="m12 3 2.7 6.3L21 12l-6.3 2.7L12 21l-2.7-6.3L3 12l6.3-2.7Z"/>',
  'Mark':'<path d="M4 6h10m-7 6h13M4 18h10"/>',
  'Back':'<path d="M20 12H5m6-6-6 6 6 6"/>'
};
for(const [name,path] of Object.entries(iconPaths)){
  const comp=ownComponent('Icon/'+name,24,'HORIZONTAL',0,0,null,0);fixed(comp,24,24);
  const vector=track(figma.createNodeFromSvg(`<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#29252D" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">${path}</svg>`));
  append(comp,vector);for(const n of vector.findAll(()=>true)){createdNodeIds.push(n.id);if('strokes' in n && Array.isArray(n.strokes) && n.strokes.length)bindStroke(n,'Color/Text/Primary');}
  C['Icon/'+name]=comp;locate(comp);
}
const brand=ownComponent('Brand/Wordmark',228,'HORIZONTAL',8,0,null,0);brand.counterAxisAlignItems='CENTER';
inst(brand,'Brand mark',C['Icon/Mark']);oneLine(brand,'Wordmark','choreograph','Type/Title/M');C['Brand/Wordmark']=brand;locate(brand);

const buttonSet=await createComponentWithVariants({name:'Control/Button',variantAxes:{Type:['Primary','Secondary','Quiet'],State:['Default','Hover','Disabled']},baseProps:{width:188,height:48,layoutMode:'HORIZONTAL',padding:{top:12,bottom:12,left:20,right:20},itemSpacing:8},page});
const labelKey=buttonSet.componentSet.addComponentProperty('Label','TEXT','Continue');
const iconKey=buttonSet.componentSet.addComponentProperty('Icon','INSTANCE_SWAP',C['Icon/ArrowRight'].id);
const showKey=buttonSet.componentSet.addComponentProperty('Show icon','BOOLEAN',true);
for(const comp of buttonSet.variants){
  const primary=comp.name.includes('Type=Primary'),secondary=comp.name.includes('Type=Secondary'),disabled=comp.name.includes('State=Disabled'),hover=comp.name.includes('State=Hover');
  comp.fills=[];padding(comp,16);gap(comp,8);radius(comp,8);comp.primaryAxisSizingMode='AUTO';comp.counterAxisSizingMode='FIXED';comp.layoutSizingHorizontal='HUG';comp.layoutSizingVertical='FIXED';
  if(primary)bindFill(comp,hover?'Color/Action/Hover':'Color/Action/Primary');if(secondary){bindFill(comp,'Color/Background/Surface');bindStroke(comp);}if(!primary&&!secondary&&hover)bindFill(comp,'Color/Action/Subtle');if(disabled)comp.opacity=.4;
  const label=oneLine(comp,'Label','Continue','Type/Label/M',primary?'Color/Text/OnDark':'Color/Text/Primary');label.componentPropertyReferences={characters:labelKey};
  const icon=inst(comp,'Icon',C['Icon/ArrowRight']);icon.componentPropertyReferences={mainComponent:iconKey,visible:showKey};
  for(const n of icon.findAllWithCriteria({types:['VECTOR']})){if(n.strokes.length)bindStroke(n,primary?'Color/Text/OnDark':'Color/Text/Primary');}
}
buttonSet.componentSet.description='Primary, Secondary and Quiet actions; default/hover/disabled. Label, icon swap and icon visibility are exposed. Change Color/Action/Primary once to recolour linked buttons throughout the file.';
components['Control/Button']=buttonSet.componentSet.id;C['Control/Button']=buttonSet.componentSet;locate(buttonSet.componentSet);allCreatedUnder(buttonSet.componentSet);

for(const [name,tones,height] of [['Control/Chip',['Default','Selected','Source','Occupied'],36],['Status/Badge',['Neutral','Confirmed','Pending','Occupied'],28]]){
  const result=await createComponentWithVariants({name,variantAxes:{Tone:tones},baseProps:{width:160,height,layoutMode:'HORIZONTAL',padding:{top:4,bottom:4,left:12,right:12},itemSpacing:4},page});
  const key=result.componentSet.addComponentProperty('Label','TEXT',name.includes('Chip')?'Show the week':'Awaiting review');
  for(const comp of result.variants){
    const tone=comp.name.slice(5);padding(comp,name.includes('Chip')?8:4);gap(comp,4);radius(comp,name.includes('Chip')?8:'Full');comp.primaryAxisSizingMode='AUTO';comp.layoutSizingHorizontal='HUG';
    const occupied=tone==='Occupied',active=tone==='Selected',confirmed=tone==='Confirmed';
    bindFill(comp,occupied?'Color/Status/OccupiedSurface':active?'Color/Action/Primary':confirmed?'Color/Status/ConfirmedSurface':tone==='Pending'?'Color/Brand/Soft':'Color/Background/Subtle');
    const label=oneLine(comp,'Label',name.includes('Chip')?'Show the week':'Awaiting review','Type/Label/S',occupied?'Color/Status/Occupied':active?'Color/Text/OnDark':confirmed?'Color/Status/Confirmed':'Color/Text/Brand');label.componentPropertyReferences={characters:key};
  }
  result.componentSet.description='Reusable labelled '+name+'. Tone is semantic, and label content is exposed as a text property.';
  components[name]=result.componentSet.id;C[name]=result.componentSet;locate(result.componentSet);allCreatedUnder(result.componentSet);
}

const rail=ownComponent('Navigation/LandingRail',104,'VERTICAL',32,24,'Color/Background/Surface',0);fixed(rail,104,900);rail.counterAxisAlignItems='CENTER';inst(rail,'Mark',C['Icon/Mark']);
for(const [number,label] of [['01','The idea'],['02','The flow'],['03','Try demo']]){const group=auto(rail,'Rail · '+label,56,'VERTICAL',4);oneLine(group,'Index',number,'Type/Title/M','Color/Text/Brand');txt(group,'Label',label,'Type/Caption',56);}
const railEnd=txt(rail,'Rail footer','A little less\nback & forth.','Type/Caption',56,'Color/Text/Secondary');C[rail.name]=rail;locate(rail);

const header=ownComponent('Navigation/AppHeader',1440,'HORIZONTAL',24,24,'Color/Background/Surface',0);fixed(header,1440,88);header.counterAxisAlignItems='CENTER';inst(header,'Wordmark',brand);spare(header);oneLine(header,'Business','Juniper Cleaning','Type/Label/M');badge(header,'Fictional company');const perspective=button(header,'Business view','Secondary','Switch perspective');C[header.name]=header;locate(header);

const composer=ownComponent('Chat/Composer',728,'VERTICAL',12,16,'Color/Background/Surface',12);bindStroke(composer);
const draft=txt(composer,'Draft','Ask a question or describe your cleaning job…','Type/Body/M',690,'Color/Text/Secondary');prop(composer,draft,'Draft','Ask a question or describe your cleaning job…');
const composerRow=auto(composer,'Composer actions',696,'HORIZONTAL',12);composerRow.counterAxisAlignItems='CENTER';chip(composerRow,'Questions to try · 18','Default','Questions to try');spare(composerRow);button(composerRow,'Send','Primary','Send');
C[composer.name]=composer;locate(composer);

for(const [name,id] of Object.entries(components))C[name]=await figma.getNodeByIdAsync(id);
return {createdNodeIds:[...new Set(createdNodeIds)],mutatedNodeIds,entityDelta:{components},stats:{components:Object.keys(components).length,buttonVariants:buttonSet.variants.length,fonts:[...new Set(page.findAllWithCriteria({types:['TEXT']}).map(n=>n.fontName.family))],mainComponentsX:2040}};
