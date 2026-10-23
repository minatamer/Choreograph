import {test} from 'node:test';
import assert from 'node:assert/strict';
import {tourPlacement,tourSpotlight,tourPanels} from '../apps/frontend/lib/tour-layout.ts';
test('tour cards stay inside narrow, short and offset visual viewports',()=>{
 for(const view of [{left:0,top:0,width:320,height:430},{left:0,top:0,width:1440,height:900},{left:10,top:230,width:390,height:280}]){
  for(const target of [null,{left:-200,top:-500,right:100,bottom:100},{left:200,top:300,right:1200,bottom:1600}]){
   const box=tourPlacement(target,view,380);
   assert.ok(box.left>=view.left&&box.top>=view.top);
   assert.ok(box.left+box.width<=view.left+view.width);
   assert.ok(box.top+box.height<=view.top+view.height);
  }
 }
});
test('spotlight scrims cover the viewport except the real clipped target',()=>{
 const view={left:0,top:0,width:390,height:844};
 for(const target of [{left:20,top:200,right:370,bottom:300},{left:-30,top:600,right:500,bottom:1000}]){
  const hole=tourSpotlight(target,view),panels=tourPanels(hole,view);
  assert.ok(panels.every(panel=>panel.width>=0&&panel.height>=0));
  assert.equal(panels.reduce((area,panel)=>area+panel.width*panel.height,0)+hole.width*hole.height,view.width*view.height);
 }
});
test('placement prefers free room below or above the highlighted target',()=>{
 const view={left:0,top:0,width:1280,height:720};
 assert.equal(tourPlacement({left:100,top:100,right:400,bottom:160},view,200).top,174);
 assert.equal(tourPlacement({left:100,top:500,right:400,bottom:600},view,200).top,286);
});
