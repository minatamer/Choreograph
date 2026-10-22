const page=await figma.getNodeByIdAsync(STATE.entities.pages['01 · Design System']);await figma.setCurrentPageAsync(page);
const action=V['Color/Action/Primary'];const coll=await figma.variables.getVariableCollectionByIdAsync(action.variableCollectionId);const mode=coll.modes[0].modeId;const original=action.valuesByMode[mode];
const main=C['Control/Button'].children.find(n=>n.name==='Type=Primary, State=Default');
const targets=[main,await figma.getNodeByIdAsync(STATE.entities.hotspots['landing-try']),await figma.getNodeByIdAsync(STATE.entities.hotspots['mobile-try']),await figma.getNodeByIdAsync(STATE.entities.hotspots['busy-use-time'])];
const connectedBusy=await figma.getNodeByIdAsync(STATE.prototype.connectedBranch['D05 · Scheduling · Busy first choice']);targets.push(instanceByName(instanceByName(connectedBusy,'Interactive week'),'Use time'));
const inspect=()=>targets.map(n=>({id:n.id,name:n.name,binding:n.fills[0].boundVariables?.color?.id,resolved:action.resolveForConsumer(n).value,paint:n.fills[0].color}));
const before=inspect();let changed,restored;
try{action.setValueForMode(mode,{r:.08,g:.43,b:.32,a:1});changed=inspect();}finally{action.setValueForMode(mode,original);restored=inspect();}
const brand=C['Brand/Wordmark'];const wordmark=componentText(brand,'Wordmark');const originalText=wordmark.characters;
const desktop=await figma.getNodeByIdAsync(STATE.entities.frames['D01 · Landing']),mobile=await figma.getNodeByIdAsync(STATE.entities.frames['M01 · Landing']);
const consumers=[componentText(instanceByName(desktop,'Choreograph'),'Wordmark'),componentText(instanceByName(mobile,'Wordmark'),'Wordmark'),componentText(connectedBusy,'Wordmark')];let textChanged,textRestored;
try{wordmark.characters=originalText+'·';textChanged=consumers.map(n=>({id:n.id,text:n.characters}));}finally{wordmark.characters=originalText;textRestored=consumers.map(n=>({id:n.id,text:n.characters}));}
const colourPass=changed.every(n=>n.binding===action.id&&Math.abs(n.resolved.g-.43)<.0001)&&JSON.stringify(before.map(n=>n.resolved))===JSON.stringify(restored.map(n=>n.resolved));
const componentPass=textChanged.every(n=>n.text===originalText+'·')&&textRestored.every(n=>n.text===originalText);
return {createdNodeIds:[],mutatedNodeIds:[wordmark.id],verification:{colourPass,componentPass,before,changed,restored,textChanged,textRestored,restoredOriginals:true}};
