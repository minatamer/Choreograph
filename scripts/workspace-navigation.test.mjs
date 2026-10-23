import {test} from 'node:test';
import assert from 'node:assert/strict';
import {workspaceLocation,workspaceSearch} from '../apps/frontend/lib/workspace-navigation.ts';
test('untrusted or missing destinations fall back without inventing a dashboard page',()=>{
 for(const search of ['', '?view=admin&section=../../admin','?view=business&section=settings'])assert.deepEqual(workspaceLocation(search),{business:search.includes('view=business'),page:'overview'});
});
test('each real destination round trips across role changes and preserves unrelated state',()=>{
 for(const page of ['overview','requests','calendar','guides','connections'])for(const business of [true,false]){
  const search=workspaceSearch('?keep=value&section=unknown',business,page);
  assert.deepEqual(workspaceLocation(search),{business,page});assert.equal(new URLSearchParams(search).get('keep'),'value');
 }
});
