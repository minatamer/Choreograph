const page=await figma.getNodeByIdAsync(STATE.entities.pages['01 · Design System']);await figma.setCurrentPageAsync(page);
const semantic=await figma.variables.getVariableCollectionByIdAsync(STATE.entities.collections.semantic.id);const variableDelta={};
for(const [name,value]of [['DraftReady',false],['DraftEmpty',true]]){let v=V['Prototype/'+name];if(!v){v=figma.variables.createVariable('Prototype/'+name,semantic,'BOOLEAN');v.setValueForMode(semantic.modes[0].modeId,value);v.scopes=['ALL_SCOPES'];v.setVariableCodeSyntax('WEB','var(--prototype-'+name.toLowerCase()+')');}V['Prototype/'+name]=v;variableDelta[v.name]=v.id;}
V['Prototype/Draft'].setValueForMode(semantic.modes[0].modeId,'');
const composer=C['Chat/Composer'];const draft=composer.children.find(n=>n.type==='TEXT'&&n.name==='Draft');draft.setBoundVariable('visible',V['Prototype/DraftReady']);
let hint=composer.children.find(n=>n.name==='Empty draft hint');if(!hint){hint=txt(null,'Empty draft hint','Ask about services, times or company guidance…','Type/Body/M',690,'Color/Text/Secondary');composer.insertChild(0,hint);}hint.setBoundVariable('visible',V['Prototype/DraftEmpty']);mutatedNodeIds.push(draft.id,composer.id);
const fri=instanceByName(C['Calendar/Week'],'Day/FRI');setText(fri,{Status:'Booked'});mutatedNodeIds.push(fri.id);
return {createdNodeIds,mutatedNodeIds,entityDelta:{variables:variableDelta},stats:{composerEmptyState:true,fridayLabel:'Booked'}};
