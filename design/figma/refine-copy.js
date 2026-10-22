// Inject COPY and PAGE_ID. Preserve exposed properties and variable bindings.
figma.skipInvisibleInstanceChildren=false;
const page=await figma.getNodeByIdAsync(PAGE_ID);await figma.setCurrentPageAsync(page);
const texts=page.findAllWithCriteria({types:['TEXT']});
const fonts=new Map();for(const n of texts)for(const s of n.getStyledTextSegments(['fontName']))fonts.set(JSON.stringify(s.fontName),s.fontName);
await Promise.all([...fonts.values()].map(f=>figma.loadFontAsync(f)));
const changed=[],removed=[],variableIds=[];
const removeNames=new Set(['Artifact boundary','Hero note','Fictional context','Availability note','Calendar help','Outcome footer','What happens next','Prototype route note']);
for(const n of texts){if(n.removed)continue;
  if(removeNames.has(n.name)||n.characters==='The highlighted passage supports the answer.'){removed.push(n.id);n.remove();continue;}
  const replacement=COPY[n.characters];if(replacement===undefined)continue;
  const binding=n.boundVariables?.characters;
  if(binding){const v=await figma.variables.getVariableByIdAsync(binding.id);for(const[mode,value]of Object.entries(v.valuesByMode))if(typeof value==='string'&&COPY[value]!==undefined){v.setValueForMode(mode,COPY[value]);variableIds.push(v.id);}changed.push(n.id);continue;}
  const key=n.componentPropertyReferences?.characters;let owner=n.parent,updated=false;
  if(key)while(owner&&owner.type!=='PAGE'){
    if(owner.type==='INSTANCE'&&Object.hasOwn(owner.componentProperties,key)){owner.setProperties({[key]:replacement});changed.push(owner.id);updated=true;break;}
    const definition=owner.type==='COMPONENT_SET'?owner:owner.type==='COMPONENT'&&owner.parent?.type!=='COMPONENT_SET'?owner:null;
    if(definition&&Object.hasOwn(definition.componentPropertyDefinitions,key)){definition.editComponentProperty(key,{defaultValue:replacement});changed.push(definition.id);updated=true;break;}
    owner=owner.parent;
  }
  if(!updated)n.characters=replacement;changed.push(n.id);
}
if(PAGE_ID==='15:2'){const foundation=await figma.getNodeByIdAsync('18:153'),library=await figma.getNodeByIdAsync('18:209');library.y=foundation.y+foundation.height+80;changed.push(library.id);}
return {createdNodeIds:[],mutatedNodeIds:[...new Set(changed)],removedNodeIds:removed,mutatedVariableIds:[...new Set(variableIds)],stats:{edited:changed.length,removed:removed.length}};
