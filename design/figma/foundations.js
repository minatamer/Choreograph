// Execute through use_figma with CONFIG and the supplied variable helpers embedded.
const createdNodeIds=[], mutatedNodeIds=[], variables={}, styles={}, pages={}, collections={};
const original=await figma.getNodeByIdAsync('0:1');
if(original && original.name==='Welcome'){original.name='99 · Archive';mutatedNodeIds.push(original.id);}
for(const name of ['01 · Design System','02 · Key Screens']){
  let p=figma.root.children.find(n=>n.name===name);
  if(!p){p=figma.createPage();p.name=name;createdNodeIds.push(p.id);}
  pages[name]=p.id;
}
const ds=await figma.getNodeByIdAsync(pages['01 · Design System']);
await figma.setCurrentPageAsync(ds);
const localCollections=await figma.variables.getLocalVariableCollectionsAsync();
async function ensureCollection(name){
  const existing=localCollections.find(c=>c.name===name);
  if(existing)return existing;
  return (await createVariableCollection(name,['Value'])).collection;
}
const primitive=await ensureCollection('Choreograph · Primitives');
const semantic=await ensureCollection('Choreograph · Semantic');
collections.primitives={id:primitive.id,mode:primitive.modes[0].modeId};
collections.semantic={id:semantic.id,mode:semantic.modes[0].modeId};
const allVariables=await figma.variables.getLocalVariablesAsync();
async function ensureTokens(collection,definitions){
  const mode=collection.modes[0].modeId;
  const missing=definitions.filter(t=>!allVariables.some(v=>v.variableCollectionId===collection.id&&v.name===t.name));
  const made=(await createSemanticTokens(collection,{Value:mode},missing)).variables;
  const output={};
  for(const def of definitions){
    const v=made[def.name]||allVariables.find(v=>v.variableCollectionId===collection.id&&v.name===def.name);
    v.scopes=def.scopes;
    v.setVariableCodeSyntax('WEB',def.codeSyntax.WEB);
    output[def.name]=v;variables[def.name]=v.id;
  }
  return output;
}
const code=name=>'var(--'+name.toLowerCase().replaceAll('/','-')+')';
const primitives=await ensureTokens(primitive,Object.entries(CONFIG.primitives).map(([name,value])=>({name:'Primitive/'+name,type:'COLOR',values:{Value:value},scopes:['FRAME_FILL','SHAPE_FILL','TEXT_FILL','STROKE_COLOR'],codeSyntax:{WEB:code('primitive/'+name)}})));
const semanticDefs=Object.entries(CONFIG.colors).map(([name,ref])=>({name,type:'COLOR',values:{Value:{type:'VARIABLE_ALIAS',id:primitives['Primitive/'+ref].id}},scopes:name.includes('/Text/')?['TEXT_FILL']:name.includes('/Border/')?['STROKE_COLOR']:['FRAME_FILL','SHAPE_FILL','STROKE_COLOR'],codeSyntax:{WEB:code(name)}}));
for(const [name,value] of Object.entries(CONFIG.spacing))semanticDefs.push({name:'Space/'+name,type:'FLOAT',values:{Value:value},scopes:['GAP'],codeSyntax:{WEB:code('space/'+name)}});
for(const [name,value] of Object.entries(CONFIG.radius))semanticDefs.push({name:'Radius/'+name,type:'FLOAT',values:{Value:value},scopes:['CORNER_RADIUS'],codeSyntax:{WEB:code('radius/'+name)}});
// BOOLEAN has no dedicated visibility scope in this API; its explicit supported scope is ALL_SCOPES.
for(const [name,value] of [['CRMConnected',false],['CRMNotConnected',true]])semanticDefs.push({name:'Prototype/'+name,type:'BOOLEAN',values:{Value:value},scopes:['ALL_SCOPES'],codeSyntax:{WEB:code('prototype/'+name)}});
await ensureTokens(semantic,semanticDefs);
const fontNames=[...new Map(Object.values(CONFIG.type).map(t=>[t.family+'/'+t.style,{family:t.family,style:t.style}])).values()];
await Promise.all(fontNames.map(f=>figma.loadFontAsync(f)));
const existingStyles=await figma.getLocalTextStylesAsync();
for(const [name,t] of Object.entries(CONFIG.type)){
  let s=existingStyles.find(s=>s.name===name);
  if(!s){s=figma.createTextStyle();s.name=name;s.fontName={family:t.family,style:t.style};s.fontSize=t.size;s.lineHeight={unit:'PIXELS',value:t.line};s.letterSpacing={unit:'PIXELS',value:t.tracking};}
  styles[name]=s.id;
}
return {createdNodeIds,mutatedNodeIds,entityDelta:{pages,collections,variables,styles},stats:{primitiveColors:Object.keys(primitives).length,semanticTokens:semanticDefs.length,textStyles:Object.keys(styles).length,fontFamilies:[...new Set(fontNames.map(f=>f.family))],pages:figma.root.children.map(p=>({id:p.id,name:p.name}))}};
