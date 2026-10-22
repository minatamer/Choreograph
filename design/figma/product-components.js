const page=await figma.getNodeByIdAsync(STATE.entities.pages['01 · Design System']);
await figma.setCurrentPageAsync(page);
let mainY=5400;
function locate(n){page.appendChild(n);n.x=2040;n.y=mainY;mainY+=n.height+64;C[n.name]=n;return n;}
function row(p,name,width=696){const n=auto(p,name,width,'HORIZONTAL',12);n.counterAxisAlignItems='CENTER';return n;}
function textProperty(c,p,name,value,style,width,color){const n=txt(p,name,value,style,width,color);prop(c,n,name,value);return n;}

const service=ownComponent('Service/Card',220,'VERTICAL',8,16,'Color/Background/Surface',12);bindStroke(service);
textProperty(service,service,'Title','Move-out clean','Type/Title/S',188);
textProperty(service,service,'Description','A careful reset for your next chapter.','Type/Body/S',188,'Color/Text/Secondary');
textProperty(service,service,'Price','From $120','Type/Label/M',188,'Color/Text/Brand');locate(service);

const answer=ownComponent('Chat/GroundedAnswer',736,'VERTICAL',16,20,'Color/Background/Surface',12);
const ar=row(answer,'Assistant identity');inst(ar,'Assistant icon',C['Icon/Spark']);oneLine(ar,'Assistant name','Juniper assistant','Type/Label/S','Color/Text/Brand');
textProperty(answer,answer,'Title','Here’s what your clean includes.','Type/Title/S',696);
textProperty(answer,answer,'Body','✓ Accessible carpets are vacuumed; shampooing is not included.\n✓ Keep your cats in a separate, comfortable room.\n✓ Oven cleaning can be added to your move-out clean.','Type/Body/M',696);
const sources=row(answer,'Sources');chip(sources,'Service Guide · p. 2','Source','Service source');chip(sources,'Preparation · p. 1','Source','Preparation source');
const aa=row(answer,'Answer actions');chip(aa,'Show the week','Default','Show the week');chip(aa,'What supplies do you use?','Default','Ask supplies');locate(answer);

const methods=ownComponent('Chat/MethodChecklist',736,'VERTICAL',12,20,'Color/Background/Surface',12);
textProperty(methods,methods,'Title','A clear method. A little preparation.','Type/Title/S',696);
textProperty(methods,methods,'Body','01  Clear the accessible work surfaces.\n02  Work through the agreed kitchen-cleaning checklist.\n03  Check the booked add-ons before finishing.','Type/Body/M',696);
chip(methods,'Fictional Service Guide · method section','Source','Method source');locate(methods);

const daySet=await createComponentWithVariants({name:'Calendar/Day',variantAxes:{State:['Available','Busy','Selected','Closed']},baseProps:{width:88,height:172,layoutMode:'VERTICAL',padding:{top:12,bottom:12,left:8,right:8},itemSpacing:8},page});
const dayKeys={Day:daySet.componentSet.addComponentProperty('Day','TEXT','FRI'),Date:daySet.componentSet.addComponentProperty('Date','TEXT','30'),Status:daySet.componentSet.addComponentProperty('Status','TEXT','Booked'),Time:daySet.componentSet.addComponentProperty('Time','TEXT','09:00\n18:00')};
for(const c of daySet.variants){
  padding(c,8);gap(c,8);radius(c,8);c.primaryAxisSizingMode='FIXED';c.counterAxisAlignItems='CENTER';
  const state=c.name.split('=')[1];bindFill(c,state==='Busy'?'Color/Status/OccupiedSurface':state==='Selected'?'Color/Brand/Canvas':state==='Closed'?'Color/Background/Page':'Color/Background/Surface');
  if(state==='Available')bindStroke(c);const color=state==='Busy'?'Color/Status/Occupied':state==='Closed'?'Color/Text/Secondary':'Color/Text/Primary';
  for(const [name,value,style] of [['Day','FRI','Type/Label/S'],['Date','30','Type/Title/M'],['Status',state==='Available'?'Free':state==='Closed'?'Closed':state==='Selected'?'Suggested':'Booked','Type/Label/S'],['Time',state==='Closed'?'—':'09:00\n13:30','Type/Caption']]){
    const n=txt(c,name,value,style,72,color);n.textAlignHorizontal='CENTER';n.componentPropertyReferences={characters:dayKeys[name]};
  }
}
daySet.componentSet.description='One reusable day, four states. Labels/date/time exposed; occupied/free/closed labels never rely on colour alone.';components['Calendar/Day']=daySet.componentSet.id;C['Calendar/Day']=daySet.componentSet;locate(daySet.componentSet);allCreatedUnder(daySet.componentSet);

const week=ownComponent('Calendar/Week',736,'VERTICAL',16,20,'Color/Background/Surface',12);bindStroke(week);
const wh=row(week,'Week heading');oneLine(wh,'Calendar heading','Your week','Type/Title/S');spare(wh);oneLine(wh,'Week range','26 Oct–1 Nov','Type/Label/S','Color/Text/Secondary');
textProperty(week,week,'Context','Move-out + oven · 4 hr 30 min · Your local time','Type/Body/S',696,'Color/Text/Secondary');
const days=row(week,'Days');gap(days,8);
const dayData=[['MON','26','Available','Free','09:00\n13:30'],['TUE','27','Available','Free','10:00\n14:30'],['WED','28','Busy','Booked','09:00\n18:00'],['THU','29','Available','Free','09:00\n13:30'],['FRI','30','Busy','Requested','09:00\n18:00'],['SAT','31','Selected','Suggested','09:00\n13:30'],['SUN','1','Closed','Closed','—']];
for(const [d,date,state,status,time] of dayData)inst(days,'Day/'+d,daySet.variants.find(c=>c.name===`State=${state}`),{Day:d,Date:date,Status:status,Time:time});
const wf=row(week,'Alternative');textProperty(week,wf,'Alternative','Saturday fits the full clean.','Type/Body/S',360,'Color/Text/Secondary');spare(wf);button(wf,'Use Saturday 09:00','Primary','Use time');locate(week);

const summary=ownComponent('Request/Summary',368,'VERTICAL',16,20,'Color/Background/Surface',12);bindStroke(summary);
oneLine(summary,'Eyebrow','YOUR REQUEST','Type/Label/S','Color/Text/Brand');
textProperty(summary,summary,'Service','Move-out · 2 bedrooms','Type/Title/S',328);
textProperty(summary,summary,'Details','Oven add-on · 4 hr 30 min','Type/Body/M',328,'Color/Text/Secondary');
line(summary,328);textProperty(summary,summary,'Date','Saturday 31 October','Type/Label/M',328);textProperty(summary,summary,'Time','09:00–13:30 · Your local time','Type/Body/S',328,'Color/Text/Secondary');
const sr=row(summary,'Amount',328);oneLine(sr,'Quote label','Quoted total','Type/Body/S');spare(sr);textProperty(summary,sr,'Total','$185','Type/Title/M',94);
textProperty(summary,summary,'Note','A preference until the business approves it.','Type/Caption',328,'Color/Text/Secondary');locate(summary);

const quote=ownComponent('Quote/Review',736,'VERTICAL',16,24,'Color/Background/Surface',12);bindStroke(quote);
oneLine(quote,'Heading','Your clean, clearly quoted.','Type/Title/M');
for(const [name,label,value] of [['Base','Move-out · 2 bedrooms','$160'],['Addon','Oven cleaning','$25']]){const r=row(quote,name,688);oneLine(r,'Label',label,'Type/Body/M');spare(r);textProperty(quote,r,name+'Price',value,'Type/Label/M',80);}
line(quote,688);const qr=row(quote,'Total row',688);textProperty(quote,qr,'Total','$185','Type/Title/L',160);spare(qr);textProperty(quote,qr,'Duration','4 hr 30 min','Type/Label/M',140,'Color/Text/Secondary');
textProperty(quote,quote,'Slot','Saturday 31 October · 09:00–13:30 · Your local time','Type/Body/M',688);
const exportNote=auto(quote,'Connected export consent',688,'VERTICAL',4,12,'Color/Action/Subtle',8);exportNote.setBoundVariable('visible',V['Prototype/CRMConnected']);
txt(exportNote,'Consent','By sending, you approve sharing the fictional contact and booking summary with your connected HubSpot account after business approval.','Type/Body/S',664,'Color/Text/Brand');
button(quote,'Accept quote & send request','Primary','Send request',true);txt(quote,'Review note','No payment. Your preferred time is confirmed after business review.','Type/Caption',688,'Color/Text/Secondary');locate(quote);

const source=ownComponent('Knowledge/SourcePreview',368,'VERTICAL',16,20,'Color/Background/Subtle',12);
const sh=row(source,'Document heading',328);inst(sh,'Document icon',C['Icon/Document']);oneLine(sh,'Source label','SOURCE','Type/Label/S','Color/Text/Brand');
textProperty(source,source,'Title','Service Guide.pdf','Type/Title/S',328);textProperty(source,source,'Version','Juniper Cleaning · v1 · page 2','Type/Caption',328,'Color/Text/Secondary');
const paper=auto(source,'Editable document page',328,'VERTICAL',16,24,'Color/Background/Surface',4);
txt(paper,'Page brand','JUNIPER / SERVICE GUIDE','Type/Label/S',280,'Color/Text/Secondary');txt(paper,'Page title','A clear scope\nfor a clean start.','Type/Title/M',280);line(paper,280);
const highlight=auto(paper,'Supporting passage',280,'VERTICAL',8,12,'Color/Brand/Soft',4);txt(highlight,'Passage','Move-out cleaning includes vacuuming accessible carpeted floors. Carpet shampooing is not offered.','Type/Body/M',256);
txt(paper,'Method paragraph','The agreed kitchen checklist covers accessible surfaces and the selected oven add-on. Ask about preparation before the visit.','Type/Body/S',280,'Color/Text/Secondary');
txt(paper,'Page footer','Fictional company guide · 02','Type/Caption',280,'Color/Text/Secondary');txt(source,'Source note','The highlighted passage supports the answer.','Type/Caption',328,'Color/Text/Secondary');locate(source);

const staff=ownComponent('Calendar/StaffDay',736,'VERTICAL',20,20,'Color/Background/Surface',12);bindStroke(staff);
oneLine(staff,'Title','Saturday 31 October','Type/Title/M');txt(staff,'Zone','Your local time · 09:00–18:00','Type/Body/S',696,'Color/Text/Secondary');
for(const [person,title,time,bg] of [['Ada','Move-out · review before confirming','09:00–13:30 · requested','Color/Action/Subtle'],['Noah','Regular clean · existing demo job','11:00–12:30 · confirmed','Color/Background/Page']]){const r=row(staff,'Staff/'+person);txt(r,'Cleaner',person,'Type/Label/M',72);const e=auto(r,'Appointment/'+person,612,'VERTICAL',8,16,bg,8);txt(e,'Title',title,'Type/Label/M',580);txt(e,'Time',time,'Type/Body/S',580,'Color/Text/Secondary');}
badge(staff,'Friday is fully booked','Occupied');locate(staff);

const receipt=ownComponent('Booking/Receipt',736,'VERTICAL',20,32,'Color/Background/Surface',16);bindStroke(receipt);
const rc=row(receipt,'Confirmation mark',672);inst(rc,'Check',C['Icon/Check']);badge(rc,'Booking confirmed','Confirmed');
textProperty(receipt,receipt,'Title','A clean start, arranged.','Type/Title/L',672);textProperty(receipt,receipt,'Summary','Move-out · 2 bedrooms · oven\nSaturday 31 October, 09:00–13:30\nYour local time · Ada · $185','Type/Body/L',672);line(receipt,672);txt(receipt,'Booking reference','BOOKING JUN-1042 · Fictional demo','Type/Caption',672,'Color/Text/Secondary');const rca=row(receipt,'Next actions',672);button(rca,'Back to customer','Secondary','Back to customer');button(rca,'Finish demo','Quiet','Finish demo');locate(receipt);

const crm=ownComponent('Integration/Status',368,'VERTICAL',16,20,'Color/Background/Surface',12);bindStroke(crm);
textProperty(crm,crm,'Title','Synced to HubSpot','Type/Title/S',328);textProperty(crm,crm,'Body','The fictional contact and booking summary are ready to inspect in your connected account.','Type/Body/M',328,'Color/Text/Secondary');badge(crm,'Synced','Confirmed');button(crm,'Open in HubSpot','Secondary','Open in HubSpot');txt(crm,'Destination','Your connected account','Type/Caption',328,'Color/Text/Secondary');locate(crm);

return {createdNodeIds:[...new Set(createdNodeIds)],mutatedNodeIds,entityDelta:{components},stats:{productComponents:Object.keys(components).length,dayVariants:4,weekDays:dayData.length,allNativeText:page.findAllWithCriteria({types:['TEXT']}).every(n=>['Albert Sans','Bricolage Grotesque'].includes(n.fontName.family))}};
