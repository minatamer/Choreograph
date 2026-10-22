const page=await figma.getNodeByIdAsync(STATE.entities.pages['01 · Design System']);await figma.setCurrentPageAsync(page);
const semantic=await figma.variables.getVariableCollectionByIdAsync(STATE.entities.collections.semantic.id);
let date=V['Prototype/Date'];if(!date){date=figma.variables.createVariable('Prototype/Date',semantic,'STRING');date.setValueForMode(semantic.modes[0].modeId,'Saturday 31 October');date.scopes=['TEXT_CONTENT'];date.setVariableCodeSyntax('WEB','var(--prototype-date)');}
const staff=C['Calendar/StaffDay'];
for(const [nodeName,property]of [['Title','Date']]){const n=staff.children.find(n=>n.type==='TEXT'&&n.name===nodeName);const key=staff.addComponentProperty(property,'TEXT',n.characters);n.componentPropertyReferences={characters:key};mutatedNodeIds.push(n.id);}
const appointment=staff.findOne(n=>n.name==='Appointment/Ada');for(const [nodeName,property]of [['Title','RequestTitle'],['Time','RequestTime']]){const n=appointment.children.find(n=>n.type==='TEXT'&&n.name===nodeName);const key=staff.addComponentProperty(property,'TEXT',n.characters);n.componentPropertyReferences={characters:key};mutatedNodeIds.push(n.id);}mutatedNodeIds.push(staff.id);
return {createdNodeIds,mutatedNodeIds,entityDelta:{variables:{'Prototype/Date':date.id}},stats:{dateProperty:true,staffProperties:['Date','RequestTitle','RequestTime']}};
