// Inject STATE. Restyle the existing landing and entry; no new screens.
figma.skipInvisibleInstanceChildren=false;const page=await figma.getNodeByIdAsync('15:3');await figma.setCurrentPageAsync(page);
const vars=Object.fromEntries((await figma.variables.getLocalVariablesAsync()).map(v=>[v.name,v]));const styles=await figma.getLocalTextStylesAsync();
const fonts=new Map();for(const n of page.findAllWithCriteria({types:['TEXT']}))for(const s of n.getStyledTextSegments(['fontName']))fonts.set(JSON.stringify(s.fontName),s.fontName);await Promise.all([...fonts.values()].map(f=>figma.loadFontAsync(f)));
const glass=(await figma.getLocalEffectStylesAsync()).find(s=>s.name==='Material/Glass');const changed=[];
function fill(n,key){n.fills=[figma.variables.setBoundVariableForPaint({type:'SOLID',color:{r:1,g:1,b:1}},'color',vars[key])];changed.push(n.id);}
async function frosted(n){fill(n,'Color/Surface/Glass');for(const p of ['topLeftRadius','topRightRadius','bottomLeftRadius','bottomRightRadius'])n.setBoundVariable(p,vars['Radius/24']);n.strokes=[figma.variables.setBoundVariableForPaint({type:'SOLID',color:{r:1,g:1,b:1}},'color',vars['Color/Border/Glass'])];n.strokeWeight=1;await n.setEffectStyleIdAsync(glass.id);changed.push(n.id);}
for(const n of page.findAllWithCriteria({types:['FRAME']})){
 if(['Hero canvas','Mobile hero'].includes(n.name))fill(n,'Color/Background/Page');
 if(['Masthead','Mobile masthead'].includes(n.name)){for(const p of ['paddingTop','paddingBottom','paddingLeft','paddingRight'])n.setBoundVariable(p,vars['Space/12']);await frosted(n);}
 if(['Meet the fictional demo','Mobile final invitation'].includes(n.name)){fill(n,'Color/Background/Subtle');for(const t of n.findAllWithCriteria({types:['TEXT']}))if(t.name==='Title'||t.name==='Body'||t.name==='Footer')fill(t,'Color/Text/Primary');}
}
for(const n of page.findAllWithCriteria({types:['TEXT']})){
 if(n.characters==='AI FRONT DESK / SERVICE BUSINESSES'){n.characters='SCHEDULING FOR SERVICE BUSINESSES';changed.push(n.id);}
 if(n.characters==='Juniper assistant'){n.characters='Juniper';changed.push(n.id);}
}
return {createdNodeIds:[],mutatedNodeIds:[...new Set(changed)],stats:{restyled:true}};
