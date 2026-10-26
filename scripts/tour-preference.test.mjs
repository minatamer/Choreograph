import {test} from 'node:test';
import assert from 'node:assert/strict';
import {tourVisit,tourWasSeen,markTourSeen,TOUR_PREFERENCE} from '../apps/frontend/lib/tour-preference.ts';
test('completion is a scoped UI marker and never disables a different demo or generation',()=>{
 const values=new Map();const store=()=>({getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value)});
 const visit=tourVisit({workspace_id:'synthetic-workspace',generation:2});
 values.set('choreograph:workspace-tour:v1','seen');assert.equal(tourWasSeen(store,visit),false);
 markTourSeen(store,visit);assert.equal(tourWasSeen(store,visit),true);
 assert.equal(tourWasSeen(store,tourVisit({workspace_id:'another-workspace',generation:2})),false);
 assert.equal(tourWasSeen(store,tourVisit({workspace_id:'synthetic-workspace',generation:3})),false);
 assert.equal(values.get(TOUR_PREFERENCE),visit);
});
test('denied storage access, reads and writes do not interrupt the tour',()=>{
 const denied=()=>{throw Error('denied');};const throwing=()=>({getItem(){throw Error('denied');},setItem(){throw Error('denied');}});
 assert.equal(tourWasSeen(denied,'visit'),false);assert.equal(tourWasSeen(throwing,'visit'),false);assert.doesNotThrow(()=>markTourSeen(denied,'visit'));assert.doesNotThrow(()=>markTourSeen(throwing,'visit'));
});
