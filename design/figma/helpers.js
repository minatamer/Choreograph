// Shared native-Figma construction helpers. Inject CONFIG and STATE before use.
figma.skipInvisibleInstanceChildren=false;
const createdNodeIds=[],mutatedNodeIds=[],components={},frames={},hotspots={};
const V=Object.fromEntries((await figma.variables.getLocalVariablesAsync()).map(v=>[v.name,v]));
const TS=Object.fromEntries((await figma.getLocalTextStylesAsync()).map(s=>[s.name,s]));
await Promise.all([...new Map(Object.values(CONFIG.type).map(t=>[t.family+'/'+t.style,{family:t.family,style:t.style}])).values(),{family:'Inter',style:'Regular'}].map(f=>figma.loadFontAsync(f)));
function track(n){createdNodeIds.push(n.id);return n;}
function bindFill(n,name){n.fills=[figma.variables.setBoundVariableForPaint({type:'SOLID',color:{r:0,g:0,b:0}},'color',V[name])];return n;}
function bindStroke(n,name='Color/Border/Default'){n.strokes=[figma.variables.setBoundVariableForPaint({type:'SOLID',color:{r:0,g:0,b:0}},'color',V[name])];n.strokeWeight=1;return n;}
function radius(n,value=12){for(const p of ['topLeftRadius','topRightRadius','bottomLeftRadius','bottomRightRadius'])n.setBoundVariable(p,V['Radius/'+value]);}
function padding(n,value=16){for(const p of ['paddingTop','paddingRight','paddingBottom','paddingLeft'])n.setBoundVariable(p,V['Space/'+value]);}
function gap(n,value=12){n.setBoundVariable('itemSpacing',V['Space/'+value]);}
function append(p,n,fill=false){p.appendChild(n);if(fill)n.layoutSizingHorizontal='FILL';return n;}
function auto(p,name,width,dir='VERTICAL',space=12,pad=0,bg=null,r=0){
  const n=track(figma.createAutoLayout(dir));n.name=name;n.resize(width,10);n.primaryAxisSizingMode='AUTO';n.counterAxisSizingMode='FIXED';n.layoutSizingHorizontal='FIXED';n.layoutSizingVertical='HUG';gap(n,space);padding(n,pad);radius(n,r);n.fills=[];if(bg)bindFill(n,bg);if(p)append(p,n);return n;
}
function fixed(n,width,height){n.resize(width,height);n.primaryAxisSizingMode='FIXED';n.layoutSizingHorizontal='FIXED';n.layoutSizingVertical='FIXED';return n;}
function txt(p,name,content,style='Type/Body/M',width=300,color='Color/Text/Primary'){
  const n=track(figma.createText());n.name=name;n.textStyleId=TS[style].id;n.characters=content;n.textAutoResize='HEIGHT';n.resize(width,n.height);bindFill(n,color);if(p)append(p,n);return n;
}
function oneLine(p,name,content,style='Type/Label/M',color='Color/Text/Primary'){
  const n=txt(p,name,content,style,300,color);n.textAutoResize='WIDTH_AND_HEIGHT';return n;
}
function prop(c,node,name,defaultValue){const key=c.addComponentProperty(name,'TEXT',defaultValue);node.componentPropertyReferences={...(node.componentPropertyReferences||{}),characters:key};return key;}
function setText(i,values){const props=i.componentProperties;const updates={};for(const [name,value] of Object.entries(values)){const key=Object.keys(props).find(k=>k.split('#')[0]===name);if(key)updates[key]=String(value);}if(Object.keys(updates).length)i.setProperties(updates);return i;}
function inst(p,name,main,values={},fill=false){const n=track(main.createInstance());n.name=name;createdNodeIds.push(...n.findAll(()=>true).map(c=>c.id));if(p)append(p,n,fill);setText(n,values);return n;}
function ownComponent(name,width,dir='VERTICAL',space=12,pad=16,bg='Color/Background/Surface',r=12){
  const n=track(figma.createComponent());n.name=name;n.resize(width,10);n.layoutMode=dir;n.primaryAxisSizingMode='AUTO';n.counterAxisSizingMode='FIXED';n.layoutSizingHorizontal='FIXED';n.layoutSizingVertical='HUG';gap(n,space);padding(n,pad);radius(n,r);n.fills=[];if(bg)bindFill(n,bg);n.description='Choreograph local reusable component. Change shared variables/text styles or this main component; screens use linked instances.';components[name]=n.id;return n;
}
function instanceByName(root,name){return root.findAllWithCriteria({types:['INSTANCE']}).find(n=>n.name===name);}
function componentText(root,name){return root.findAllWithCriteria({types:['TEXT']}).find(n=>n.name===name);}
function spare(p){const n=auto(p,'Flexible space',4,'HORIZONTAL',0);n.layoutSizingHorizontal='FILL';return n;}
function line(p,width=300){const n=track(figma.createRectangle());n.name='Divider';n.resize(width,1);bindFill(n,'Color/Border/Default');append(p,n);return n;}
const C={};
for(const [name,id] of Object.entries(STATE.entities.components||{})){const n=await figma.getNodeByIdAsync(id);if(n)C[name]=n;}
function button(p,label,type='Primary',name=label,fill=false){const set=C['Control/Button'];const main=set.children.find(n=>n.name===`Type=${type}, State=Default`);return inst(p,name,main,{Label:label},fill);}
function chip(p,label,type='Default',name=label){const set=C['Control/Chip'];return inst(p,name,set.children.find(n=>n.name===`Tone=${type}`),{Label:label});}
function badge(p,label,tone='Neutral'){const set=C['Status/Badge'];return inst(p,'Status · '+label,set.children.find(n=>n.name===`Tone=${tone}`),{Label:label});}
function allCreatedUnder(node){createdNodeIds.push(node.id,...node.findAll(()=>true).map(n=>n.id));}
function rootFrame(page,name,width,height,x,y,bg='Color/Background/Page'){
  const existing=page.children.find(n=>n.name===name);if(existing)throw Error('Frame already exists; inspect and update its exact ID: '+existing.id);
  const f=auto(page,name,width,'VERTICAL',0,0,bg);fixed(f,width,height);f.x=x;f.y=y;f.clipsContent=true;frames[name]=f.id;return f;
}
