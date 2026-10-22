// Inject ROOTS and PAGE_ID. Read-only current key-frame/component-state audit.
figma.skipInvisibleInstanceChildren=false;const page=await figma.getNodeByIdAsync(PAGE_ID);await figma.setCurrentPageAsync(page);
const stats=[],edges=[],issues=[];
for(const[name,id]of Object.entries(ROOTS)){const root=await figma.getNodeByIdAsync(id);if(!root){issues.push({name,missing:id});continue;}const nodes=root.findAll(()=>true),texts=nodes.filter(n=>n.type==='TEXT');
 const fonts=[...new Set(texts.map(n=>n.fontName.family))],unstyled=texts.filter(n=>!n.textStyleId).map(n=>n.id),images=nodes.filter(n=>'fills'in n&&Array.isArray(n.fills)&&n.fills.some(p=>p.type==='IMAGE')).map(n=>n.id),overflow=[];
 for(const n of [root,...nodes]){if('reactions'in n)for(const r of n.reactions||[])for(const a of r.actions||[]){if(a.type==='NODE'){const target=await figma.getNodeByIdAsync(a.destinationId);if(!target)issues.push({missingTarget:a.destinationId});edges.push({source:id,hotspot:n.id,name:n.name,target:a.destinationId,navigation:a.navigation});}else issues.push({unexpectedAction:a.type});}
  if(!n.visible||!('children'in n)||n.overflowDirection==='VERTICAL'||n.name.includes('complete scroll content'))continue;
  for(const c of n.children){if(!c.visible)continue;if(c.x< -3||c.y< -3||c.x+c.width>n.width+3||c.y+c.height>n.height+3)overflow.push({parent:n.id,parentName:n.name,child:c.id,childName:c.name,parentBounds:[n.width,n.height],bounds:[c.x,c.y,c.width,c.height]});}
 }
 if(fonts.some(f=>f!=='Google Sans Flex')||unstyled.length||images.length)issues.push({name,fonts,unstyled,images});
 stats.push({name,id,width:root.width,height:root.height,fonts,unstyledText:unstyled.length,images,overflow});
}
const instances=page.findAllWithCriteria({types:['INSTANCE']});const missingMain=instances.filter(n=>!n.mainComponent).map(n=>n.id);
const vars=await figma.variables.getLocalVariablesAsync();const colours=vars.filter(v=>v.name.startsWith('Color/'));const allAliases=colours.every(v=>Object.values(v.valuesByMode).every(x=>x.type==='VARIABLE_ALIAS'));
return {createdNodeIds:[],mutatedNodeIds:[],audit:{stats,edges,issues,instances:instances.length,missingMain,variableCount:vars.length,semanticColoursAliased:allAliases,scopesSpecific:vars.every(v=>v.scopes.length&&!v.scopes.includes('ALL_SCOPES')),startingPoints:page.flowStartingPoints,visibleTopLevel:page.children.map(n=>({id:n.id,name:n.name,type:n.type})),forbiddenCopy:page.findAllWithCriteria({types:['TEXT']}).filter(n=>/here[’']s|beautifully|real product decisions|designed for exploration|PROTOTYPE \/ BASIC/i.test(n.characters)).map(n=>({id:n.id,text:n.characters}))}};
