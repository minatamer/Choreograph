const page=await figma.getNodeByIdAsync(STATE.entities.pages['02 · Key Screens']);
await figma.setCurrentPageAsync(page);
const inventory=[
  ['D01 · Landing',0,0],['D02 · Demo entry',1,0],['D03 · Visual chat · Start',2,0],
  ['D04 · Visual chat · Sources',0,1],['D05 · Scheduling · Busy first choice',1,1],['D06 · Scheduling · Open week',2,1],
  ['D07 · Quote review',0,2],['D08 · Awaiting review',1,2],['D09 · Business approval',2,2],
  ['D10 · Booking · HubSpot connected',0,3],['D11 · Booking · No CRM',1,3]
];
for(const [name,column,line] of inventory){const f=rootFrame(page,name,1440,1000,80+column*1520,80+line*1120);f.placeholder=true;}
const mobile=rootFrame(page,'M01 · Landing',390,844,80,4640);mobile.placeholder=true;
return {createdNodeIds,mutatedNodeIds,entityDelta:{frames},stats:{desktopFrames:inventory.length,mobileFrames:1,onlyMobileLanding:true,width:1440,height:1000}};
