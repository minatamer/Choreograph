const page=await figma.getNodeByIdAsync(STATE.entities.pages['02 · Key Screens']);await figma.setCurrentPageAsync(page);
const roots=Object.entries(STATE.entities.frames).filter(([name])=>/^D\d|^M\d|^P · Connected/.test(name));
const screenStats=[],edges=[],issues=[];
function ownerFrame(n){let p=n;while(p&&p.parent){if(p.type==='FRAME'&&(p.parent.type==='PAGE'||p.parent.type==='SECTION'))return p;p=p.parent;}return null;}
for(const[name,id]of roots){const frame=await figma.getNodeByIdAsync(id);const nodes=frame.findAll(()=>true);const types={};for(const n of nodes)types[n.type]=(types[n.type]||0)+1;
  const images=nodes.filter(n=>'fills'in n&&Array.isArray(n.fills)&&n.fills.some(p=>p.type==='IMAGE')).map(n=>({id:n.id,name:n.name,width:n.width,height:n.height}));
  const texts=nodes.filter(n=>n.type==='TEXT');const fonts=[...new Set(texts.map(n=>n.fontName.family))];const unstyled=texts.filter(n=>!n.textStyleId).map(n=>({id:n.id,name:n.name}));
  if(images.length||unstyled.length||fonts.some(f=>!['Bricolage Grotesque','Albert Sans'].includes(f)))issues.push({frame:name,images,unstyled,fonts});
  for(const n of [frame,...nodes])if('reactions'in n&&n.reactions.length)for(const reaction of n.reactions)for(const action of reaction.actions||[]){if(action.type==='NODE'){const target=await figma.getNodeByIdAsync(action.destinationId);if(!target)issues.push({missingTarget:action.destinationId});edges.push({source:ownerFrame(n)?.id,hotspot:n.id,name:n.name,target:action.destinationId,trigger:reaction.trigger.type});}else issues.push({unexpectedAction:action.type});}
  const overflow=[];
  for(const n of nodes){if(!n.visible||!('children'in n)||n.type==='SECTION')continue;if(n.overflowDirection==='VERTICAL'||n.name.includes('complete scroll content'))continue;for(const c of n.children){if(!c.visible)continue;if(c.x< -3||c.y< -3||c.x+c.width>n.width+3||c.y+c.height>n.height+3)overflow.push({parent:n.id,parentName:n.name,child:c.id,childName:c.name,parentBounds:[n.width,n.height],childBounds:[c.x,c.y,c.width,c.height]});}}
  screenStats.push({name,id,width:frame.width,height:frame.height,nodes:nodes.length,types,fonts,unstyledText:unstyled.length,imageNodes:images,overflow});
}
const vars=await figma.variables.getLocalVariablesAsync();const aliasColors=vars.filter(v=>v.name.startsWith('Color/')).every(v=>Object.values(v.valuesByMode).every(x=>x.type==='VARIABLE_ALIAS'));
const scoped=vars.filter(v=>v.resolvedType!=='BOOLEAN').every(v=>v.scopes.length&&!v.scopes.includes('ALL_SCOPES'));
const instances=page.findAllWithCriteria({types:['INSTANCE']});const missingMain=instances.filter(n=>!n.mainComponent).map(n=>n.id);
return {createdNodeIds:[],mutatedNodeIds:[],audit:{screenStats,edges,issues,variableCount:vars.length,semanticColourAliases:aliasColors,nonBooleanScopesSpecific:scoped,instanceCount:instances.length,instancesWithoutMain:missingMain,startingPoints:page.flowStartingPoints,desktopStates:roots.filter(([n])=>!n.startsWith('M')).length,mobileStates:roots.filter(([n])=>n.startsWith('M')).length}};
