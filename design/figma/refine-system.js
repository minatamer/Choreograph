// Inject CONFIG, STATE and RENAMES. Update existing shared definitions in place.
figma.skipInvisibleInstanceChildren=false;
const page=await figma.getNodeByIdAsync('15:2');await figma.setCurrentPageAsync(page);
const changed=[],variableIds=[],styleIds=[];
const V=Object.fromEntries((await figma.variables.getLocalVariablesAsync()).map(v=>[v.name,v]));
const fonts=new Map();for(const n of page.findAllWithCriteria({types:['TEXT']}))for(const s of n.getStyledTextSegments(['fontName']))fonts.set(JSON.stringify(s.fontName),s.fontName);
for(const t of Object.values(CONFIG.type))fonts.set(t.family+'/'+t.style,{family:t.family,style:t.style});await Promise.all([...fonts.values()].map(f=>figma.loadFontAsync(f)));
for(const[old,name]of Object.entries(RENAMES)){const v=V[old];if(v){v.name=name;v.setVariableCodeSyntax('WEB','var(--'+name.toLowerCase().replaceAll('/','-')+')');V[name]=v;delete V[old];variableIds.push(v.id);}}
const primitive=await figma.variables.getVariableCollectionByIdAsync(STATE.entities.collections.primitives.id),semantic=await figma.variables.getVariableCollectionByIdAsync(STATE.entities.collections.semantic.id);
function rgba(hex){const s=hex.slice(1);return {r:parseInt(s.slice(0,2),16)/255,g:parseInt(s.slice(2,4),16)/255,b:parseInt(s.slice(4,6),16)/255,a:s.length===8?parseInt(s.slice(6,8),16)/255:1};}
for(const[name,hex]of Object.entries(CONFIG.primitives)){const key='Primitive/'+name;let v=V[key];if(!v){v=figma.variables.createVariable(key,primitive,'COLOR');V[key]=v;}v.scopes=['FRAME_FILL','SHAPE_FILL','TEXT_FILL','STROKE_COLOR','EFFECT_COLOR'];v.setValueForMode(primitive.modes[0].modeId,rgba(hex));v.setVariableCodeSyntax('WEB','var(--'+key.toLowerCase().replaceAll('/','-')+')');variableIds.push(v.id);}
for(const[name,target]of Object.entries(CONFIG.colors)){let v=V[name];if(!v){v=figma.variables.createVariable(name,semantic,'COLOR');V[name]=v;}v.scopes=name.includes('/Text/')?['TEXT_FILL']:name.includes('/Border/')?['STROKE_COLOR']:['FRAME_FILL','SHAPE_FILL','TEXT_FILL'];v.setValueForMode(semantic.modes[0].modeId,figma.variables.createVariableAlias(V['Primitive/'+target]));v.setVariableCodeSyntax('WEB','var(--'+name.toLowerCase().replaceAll('/','-')+')');variableIds.push(v.id);}
for(const s of await figma.getLocalTextStylesAsync()){const t=CONFIG.type[s.name];if(!t)continue;s.fontName={family:t.family,style:t.style};s.fontSize=t.size;s.lineHeight={unit:'PIXELS',value:t.line};s.letterSpacing={unit:'PIXELS',value:t.tracking};styleIds.push(s.id);}
let glass=(await figma.getLocalEffectStylesAsync()).find(s=>s.name==='Material/Glass');if(!glass){glass=figma.createEffectStyle();glass.name='Material/Glass';}
glass.effects=[{type:'BACKGROUND_BLUR',blurType:'NORMAL',radius:24,visible:true},{type:'DROP_SHADOW',color:{r:.12,g:.2,b:.32,a:.09},offset:{x:0,y:4},radius:18,spread:0,visible:true,blendMode:'NORMAL'}];styleIds.push(glass.id);
function fill(n,key){n.fills=[figma.variables.setBoundVariableForPaint({type:'SOLID',color:{r:1,g:1,b:1}},'color',V[key])];changed.push(n.id);}
function corners(n,key){for(const p of ['topLeftRadius','topRightRadius','bottomLeftRadius','bottomRightRadius'])n.setBoundVariable(p,V['Radius/'+key]);changed.push(n.id);}
async function frosted(n){fill(n,'Color/Surface/Glass');n.strokes=[figma.variables.setBoundVariableForPaint({type:'SOLID',color:{r:1,g:1,b:1}},'color',V['Color/Border/Glass'])];n.strokeWeight=1;await n.setEffectStyleIdAsync(glass.id);changed.push(n.id);}
const C={};for(const[name,id]of Object.entries(STATE.entities.components)){const n=await figma.getNodeByIdAsync(id);if(n)C[name]=n;}
for(const n of C['Control/Button'].children){corners(n,'Full');if(n.name.includes('Type=Secondary')&&!n.name.includes('Disabled'))await frosted(n);}
for(const n of C['Control/Chip'].children)corners(n,'Full');
for(const name of ['Chat/Composer','Chat/UserMessage','Chat/AssistantText','Chat/GroundedAnswer'])corners(C[name],'24');
await frosted(C['Chat/Composer']);await frosted(C['Navigation/AppHeader']);await frosted(C['Navigation/LandingRail']);
for(const name of ['Calendar/Week','Service/Card','Chat/StartChoice','Quote/Review','Knowledge/SourcePreview','Request/Summary','Booking/Receipt','Integration/Status'])corners(C[name],'16');
for(const n of C['Calendar/Day'].children)corners(n,'16');
const mark=C['Icon/Mark'];for(let i=0;i<mark.children.length;i++){const n=mark.children[i];const token=['Color/Action/Primary','Color/Status/Confirmed','Color/Status/Occupied'][i%3];if('fills'in n&&n.fills.length)fill(n,token);else if('strokes'in n){n.strokes=[figma.variables.setBoundVariableForPaint({type:'SOLID',color:{r:0,g:0,b:0}},'color',V[token])];changed.push(n.id);}}
const labels={'Brand / Canvas':'Selection','Subtle / Lavender':'Subtle blue'};for(const n of page.findAllWithCriteria({types:['TEXT']})){if(labels[n.characters]){n.characters=labels[n.characters];changed.push(n.id);}for(const[old,name]of Object.entries(RENAMES))if(n.characters.includes(old)){n.characters=n.characters.replaceAll(old,name).replaceAll('var(--'+old.toLowerCase().replaceAll('/','-')+')','var(--'+name.toLowerCase().replaceAll('/','-')+')');changed.push(n.id);}}
return {createdNodeIds:[],mutatedNodeIds:[...new Set(changed)],mutatedVariableIds:[...new Set(variableIds)],mutatedStyleIds:styleIds,entityDelta:{variables:Object.fromEntries(Object.entries(V).map(([n,v])=>[n,v.id])),effects:{'Material/Glass':glass.id}},stats:{fontFamily:'Google Sans Flex',glassStyle:glass.id,componentFamilies:Object.keys(C).length}};
