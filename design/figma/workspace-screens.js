const page=await figma.getNodeByIdAsync(STATE.entities.pages['02 · Key Screens']);await figma.setCurrentPageAsync(page);
function record(name,node){hotspots[name]=node.id;return node;}
function bindProperty(instance,property,variable){const key=Object.keys(instance.componentProperties).find(k=>k.split('#')[0]===property);if(!key)throw Error('Missing property '+property+' on '+instance.name);instance.setProperties({[key]:{type:'VARIABLE_ALIAS',id:V['Prototype/'+variable].id}});}
function summary(p,mode='selected'){
  const i=inst(p,'Request summary',C['Request/Summary']);for(const[name,v]of [['Service','Service'],['Details','Details'],['Total','Total']])bindProperty(i,name,v);
  if(mode==='selected'){for(const[name,v]of [['Date','Date'],['Time','Time']])bindProperty(i,name,v);}
  if(mode==='busy')setText(i,{Date:'Friday 30 October',Time:'09:00 preferred · Your local time',Note:'That day is occupied. Choose a free alternative.'});
  if(mode==='week')setText(i,{Service:'Regular clean · 1 bedroom',Details:'No add-ons · 1 hr 30 min',Date:'Choose a day from this week',Time:'Your local time',Total:'$60',Note:'Every offered time fits the whole service.'});return i;
}
async function app(name,business=false){
  const root=await figma.getNodeByIdAsync(STATE.entities.frames[name]);if(root.children.length)throw Error('Screen already populated '+root.id);mutatedNodeIds.push(root.id);
  const header=inst(root,'App header',C['Navigation/AppHeader']);if(business)setText(instanceByName(header,'Switch perspective'),{Label:'Customer view'});
  const body=auto(root,'Workspace',1440,'HORIZONTAL',24,32);fixed(body,1440,912);
  const nav=inst(body,'Workspace navigation',C['Navigation/DemoSidebar']);if(business){const b=nav.findAllWithCriteria({types:['INSTANCE']}).find(n=>n.name==='Status · Customer');if(b)setText(b,{Label:'Business'});}
  const main=auto(body,'Conversation',752,'VERTICAL',16);fixed(main,752,848);
  const heading=auto(main,'Conversation heading',752,'VERTICAL',4);txt(heading,'Title',business?'A clear picture of the day.':'Let’s arrange your clean.','Type/Title/M',752);txt(heading,'Context','Juniper Cleaning · Your local time · Fictional demo','Type/Body/S',752,'Color/Text/Secondary');
  const messages=auto(main,'Conversation messages',752,'VERTICAL',16);const side=auto(body,'Companion pane',368,'VERTICAL',20);
  return {root,header,body,main,messages,side,nav};
}
function finishChat(a,prefix){
  const space=auto(a.main,'Remaining conversation space',752,'VERTICAL',0);space.layoutSizingVertical='FILL';
  const composer=inst(a.main,'Composer',C['Chat/Composer']);composer.resize(752,composer.height);bindProperty(composer,'Draft','Draft');record(prefix+'-send',instanceByName(composer,'Send'));record(prefix+'-questions',instanceByName(composer,'Questions to try'));a.root.placeholder=false;
}
function user(p,text){return inst(p,'Your message',C['Chat/UserMessage'],{Body:text});}
function assistant(p,text){return inst(p,'Assistant reply',C['Chat/AssistantText'],{Body:text});}
function week(p,prefix,open=false){const i=inst(p,'Interactive week',C['Calendar/Week']);if(open){setText(i,{Context:'Regular clean · 1 hr 30 min · Your local time',Alternative:'Choose a free day. Monday is a good start.'});for(const[d,t]of [['MON','09:00\n10:30'],['TUE','10:00\n11:30'],['THU','09:00\n10:30'],['SAT','09:00\n10:30']]){const day=instanceByName(i,'Day/'+d);setText(day,{Time:t});if(d==='MON'){day.swapComponent(C['Calendar/Day'].children.find(c=>c.name==='State=Selected'));setText(day,{Day:'MON',Date:'26',Status:'Suggested',Time:t});}if(d==='SAT'){day.swapComponent(C['Calendar/Day'].children.find(c=>c.name==='State=Available'));setText(day,{Day:'SAT',Date:'31',Status:'Free',Time:t});}}setText(instanceByName(i,'Use time'),{Label:'Use Monday 09:00'});}
  record(prefix+'-use-time',instanceByName(i,'Use time'));for(const d of ['MON','TUE','THU','SAT'])record(prefix+'-day-'+d,instanceByName(i,'Day/'+d));return i;
}

const start=await app('D03 · Visual chat · Start');
txt(start.messages,'Welcome','What can we take\noff your list?','Type/Title/L',736);txt(start.messages,'Welcome copy','Choose a starting point, then Send. You can ask questions or change the details as we go.','Type/Body/M',736,'Color/Text/Secondary');
record('starter-busy',inst(start.messages,'Starter · busy first choice',C['Chat/StartChoice'],{Title:'Moving out + a preferred day',Body:'Carpets, two cats, an oven and Friday morning.'}));
record('starter-week',inst(start.messages,'Starter · open week',C['Chat/StartChoice'],{Title:'A regular clean · what’s free this week?',Body:'One bedroom. Show me the week and the available times.'}));
inst(start.messages,'Starter · clarification',C['Chat/StartChoice'],{Title:'Help me work out what I need',Body:'Try a deliberately incomplete request and guided choices.'});
const quick=auto(start.messages,'Quick question shortcuts',736,'HORIZONTAL',8);chip(quick,'What’s included?','Source','Quick source');chip(quick,'Cleaning supplies','Source','Quick supplies');record('shortcut-week',chip(quick,'What’s free this week?','Default','Quick week'));
oneLine(start.side,'Services heading','A few good ways to start.','Type/Title/S');for(const[title,description,price]of [['Regular clean','A familiar routine for an everyday home.','From $60'],['Deep clean','A more detailed clean for a fresh start.','From $90'],['Move-out clean','A careful reset for your next chapter.','From $120']]){const i=inst(start.side,'Service · '+title,C['Service/Card'],{Title:title,Description:description,Price:price});i.resize(368,i.height);i.layoutSizingVertical='HUG';}
finishChat(start,'start');

const source=await app('D04 · Visual chat · Sources');user(source.messages,'Does move-out cleaning include carpet shampooing? I have two cats. How do you clean the kitchen?');
const answer=inst(source.messages,'Grounded answer',C['Chat/GroundedAnswer'],{Body:'✓ Accessible carpets are vacuumed; shampooing is not included.\n✓ Keep your cats in a separate, comfortable room.\n✓ The agreed kitchen checklist covers accessible surfaces.\n✓ Oven cleaning is an optional booked add-on.'});record('source-show-week',instanceByName(answer,'Show the week'));record('source-supplies',instanceByName(answer,'Ask supplies'));
const contextActions=auto(source.messages,'Continue the conversation',736,'HORIZONTAL',8);record('source-open-week',chip(contextActions,'When is it free this week?','Default'));chip(contextActions,'Compare services','Default');inst(source.side,'Source preview',C['Knowledge/SourcePreview']);finishChat(source,'sources');

const busy=await app('D05 · Scheduling · Busy first choice');user(busy.messages,'Can I have the move-out clean with the oven on Friday 30 October at 09:00?');assistant(busy.messages,'Friday is already fully booked. Saturday 09:00–13:30 fits your whole clean. Would that work for you?');week(busy.messages,'busy');summary(busy.side,'busy');txt(busy.side,'Availability note','Existing demo appointments occupy Friday. These are the same records shown in Business view.','Type/Body/S',368,'Color/Text/Secondary');finishChat(busy,'busy');

const open=await app('D06 · Scheduling · Open week');user(open.messages,'I’d like a regular clean for my one-bedroom apartment. When is it free this week?');assistant(open.messages,'Here’s the week for a 1 hr 30 min clean. Choose a free time; I’ll keep the quote and your request together.');week(open.messages,'open',true);summary(open.side,'week');txt(open.side,'Calendar help','Select an available day card or the suggested time. Booked and closed days are labelled.','Type/Body/S',368,'Color/Text/Secondary');finishChat(open,'open');

const quoted=await app('D07 · Quote review');assistant(quoted.messages,'Here’s the quote and your preferred time. Check the details before sending the request to Juniper.');
const q=inst(quoted.messages,'Quote review',C['Quote/Review']);for(const[name,v]of [['Service','Service'],['BasePrice','BasePrice'],['AddonLabel','AddonLabel'],['AddonPrice','AddonPrice'],['Total','Total'],['Duration','Duration'],['Slot','Slot']])bindProperty(q,name,v);record('quote-submit',instanceByName(q,'Send request'));summary(quoted.side);finishChat(quoted,'quote');

const awaiting=await app('D08 · Awaiting review');badge(awaiting.messages,'Awaiting review','Pending');txt(awaiting.messages,'Title','Your request is with Juniper.','Type/Title/L',736);assistant(awaiting.messages,'Your preferred time is ready for a business review. Switch perspectives to check the request, assign a cleaner and confirm it.');summary(awaiting.messages);record('awaiting-business',button(awaiting.messages,'Review as business','Primary'));txt(awaiting.side,'What happens next','The business checks the quote and availability before reserving your appointment.','Type/Body/L',368,'Color/Text/Secondary');finishChat(awaiting,'awaiting');

const business=await app('D09 · Business approval',true);business.messages.name='Business overview';
const kpis=auto(business.messages,'Record-based KPIs',752,'HORIZONTAL',16);for(const[label,value]of [['Awaiting review','1'],['Existing jobs today','1'],['Cleaner availability','2 staff']]){const box=auto(kpis,label,240,'VERTICAL',8,16,'Color/Background/Surface',12);txt(box,'Label',label,'Type/Body/S',208,'Color/Text/Secondary');txt(box,'Value',value,'Type/Title/L',208);}
const staff=inst(business.messages,'Staff calendar',C['Calendar/StaffDay']);bindProperty(staff,'Date','Date');bindProperty(staff,'RequestTitle','Service');bindProperty(staff,'RequestTime','Time');record('business-documents',chip(business.messages,'Documents · 6 guides','Source'));
oneLine(business.side,'Review heading','Review request','Type/Title/M');badge(business.side,'Awaiting review','Pending');summary(business.side);txt(business.side,'Assignment','Assign cleaner','Type/Label/M',368);chip(business.side,'Ada · available','Selected');record('business-approve',button(business.side,'Confirm booking','Primary','Confirm booking',true));txt(business.side,'Approval note','Availability is checked again when you confirm. A preference is not a reservation.','Type/Caption',368,'Color/Text/Secondary');business.root.placeholder=false;

for(const [name,connected]of [['D10 · Booking · HubSpot connected',true],['D11 · Booking · No CRM',false]]){
  const a=await app(name);const r=inst(a.messages,'Booking receipt',C['Booking/Receipt']);bindProperty(r,'Summary','ReceiptSummary');record((connected?'connected':'skipped')+'-finish',instanceByName(r,'Finish demo'));record((connected?'connected':'skipped')+'-back',instanceByName(r,'Back to customer'));
  const integration=inst(a.side,'CRM outcome',C['Integration/Status']);if(!connected){setText(integration,{Title:'CRM not connected',Body:'Your booking is confirmed. No records were sent to a CRM.'});const status=integration.findAllWithCriteria({types:['INSTANCE']}).find(n=>n.name==='Status · Synced');status.swapComponent(C['Status/Badge'].children.find(c=>c.name==='Tone=Neutral'));setText(status,{Label:'Not connected'});instanceByName(integration,'Open in HubSpot').visible=false;componentText(integration,'Destination').visible=false;}
  txt(a.main,'Outcome footer','Your booking and CRM connection have separate, clear states.','Type/Caption',752,'Color/Text/Secondary');a.root.placeholder=false;
}
const synced=await figma.getNodeByIdAsync(STATE.entities.frames['D10 · Booking · HubSpot connected']);const pending=track(synced.clone());page.appendChild(pending);pending.name='D10A · Booking · CRM pending';pending.x=3120;pending.y=3440;frames[pending.name]=pending.id;allCreatedUnder(pending);
const pendingCRM=instanceByName(pending,'CRM outcome');setText(pendingCRM,{Title:'Booking saved. CRM syncing…',Body:'Your appointment is confirmed. The fictional customer and booking summary are being synced separately.'});const pendingStatus=pendingCRM.findAllWithCriteria({types:['INSTANCE']}).find(n=>n.name==='Status · Synced');pendingStatus.swapComponent(C['Status/Badge'].children.find(c=>c.name==='Tone=Pending'));setText(pendingStatus,{Label:'Pending'});instanceByName(pendingCRM,'Open in HubSpot').visible=false;
return {createdNodeIds:[...new Set(createdNodeIds)],mutatedNodeIds,entityDelta:{frames,hotspots},stats:{workspaceFrames:9,prototypeVariableBindings:page.findAllWithCriteria({types:['TEXT']}).filter(n=>n.boundVariables&&Object.keys(n.boundVariables).length).length,textFamilies:[...new Set(page.findAllWithCriteria({types:['TEXT']}).map(n=>n.fontName.family))],nodeTypes:page.findAll(()=>true).reduce((a,n)=>(a[n.type]=(a[n.type]||0)+1,a),{}),imageNodes:page.findAll(n=>'fills'in n&&Array.isArray(n.fills)&&n.fills.some(p=>p.type==='IMAGE')).map(n=>({id:n.id,name:n.name,width:n.width,height:n.height}))}};
