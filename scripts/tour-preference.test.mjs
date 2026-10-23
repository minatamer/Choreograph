import {test} from 'node:test';
import assert from 'node:assert/strict';
import {tourWasSeen,markTourSeen,TOUR_PREFERENCE} from '../apps/frontend/lib/tour-preference.ts';
test('the only persisted tour value is a versioned UI preference',()=>{
 const values=new Map();const store=()=>({getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value)});
 assert.equal(tourWasSeen(store),false);markTourSeen(store);assert.equal(tourWasSeen(store),true);assert.deepEqual([...values],[[TOUR_PREFERENCE,'seen']]);
});
test('denied storage access, reads and writes do not interrupt the tour',()=>{
 const denied=()=>{throw Error('denied');};const throwing=()=>({getItem(){throw Error('denied');},setItem(){throw Error('denied');}});
 assert.equal(tourWasSeen(denied),false);assert.equal(tourWasSeen(throwing),false);assert.doesNotThrow(()=>markTourSeen(denied));assert.doesNotThrow(()=>markTourSeen(throwing));
});
