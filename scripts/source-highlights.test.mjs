import {test} from 'node:test';
import assert from 'node:assert/strict';
import {sourceTextMatches,sourceTextBlocks} from '../apps/frontend/lib/source-highlights.ts';
import {citationGroups,reviewMessage} from '../apps/frontend/lib/chat-sources.ts';

test('PDF matching follows real line breaks and partial text items',()=>{
 const items=['Before the clean: keep cats in a','separate safe room. Bring water.'];
 const content='Before the clean: keep cats in a separate safe room. Bring water.';
 const matches=sourceTextMatches(items,[{content,excerpt:'keep cats in a separate safe room.'}]);
 assert.deepEqual(matches,[{item:0,from:18,to:32},{item:1,from:0,to:19}]);
 assert.equal(matches.map(match=>items[match.item].slice(match.from,match.to)).join(' '),'keep cats in a separate safe room.');
});
test('ligatures, nonbreaking spaces and typographic quotes keep original character ranges',()=>{
 const actual='Our oﬃce’s\u00a0policy';
 const result=sourceTextMatches([actual],[{content:"Our office's policy",excerpt:"office's policy"}]);
 assert.deepEqual(result,[{item:0,from:4,to:actual.length}]);
 const unicode='🧹 Our policy: keep pets safe.';
 assert.deepEqual(sourceTextMatches([unicode],[{content:unicode,excerpt:'keep pets safe.'}]),[{item:0,from:15,to:30}]);
});
test('passage context disambiguates repeated quotes on one page',()=>{
 const items=['First section. A time is free.','Second section. A time is free.'];
 assert.deepEqual(sourceTextMatches(items,[{content:items[1],excerpt:'A time is free.'}]),[{item:1,from:16,to:31}]);
 assert.deepEqual(sourceTextMatches(items,[{content:'Another policy',excerpt:'A time is free.'}]),[]);
 assert.deepEqual(sourceTextMatches(items,[{content:'Missing words.',excerpt:'Missing words.'}]),[]);
 assert.deepEqual(sourceTextMatches(items,[{content:'Missing heading. A time is free.',excerpt:'A time is free.'}]),[]);
});
test('FAQ highlights preserve text and merge overlapping exact excerpts',()=>{
 const text='Keep pets in a safe room.';
 const parts=sourceTextBlocks(text,['pets in a safe room','a safe room'].map(excerpt=>({content:text,excerpt})))[0].parts;
 assert.equal(parts.map(part=>part.text).join(''),text);
 assert.deepEqual(parts.filter(part=>part.highlight).map(part=>part.text),['pets in a safe room']);
 assert.deepEqual(sourceTextBlocks('<script>plain text</script>',[])[0].parts,[{text:'<script>plain text</script>',highlight:false}]);
});
test('citations group by actual version and page without losing distinct evidence',()=>{
 const claim={version_id:'a',page:1,passage_id:'one',excerpt:'First quote'};
 const groups=citationGroups([claim,{...claim,passage_id:'two',excerpt:'Second quote'},claim,{...claim,page:2},{...claim,version_id:'b'}]);
 assert.equal(groups.length,3);assert.equal(groups[0].claims.length,2);
 assert.deepEqual(groups.map(group=>group.key),['a:1','a:2','b:1']);
});
test('review stays with its planning message after unrelated questions and refresh',()=>{
 const rows=[{id:'plan',role:'assistant',cards:['week']},{id:'question',role:'user',cards:[]},{id:'answer',role:'assistant',cards:[]}];
 assert.equal(reviewMessage(rows),'plan');assert.equal(reviewMessage(JSON.parse(JSON.stringify(rows))),'plan');
 assert.equal(reviewMessage([...rows,{id:'new-plan',role:'assistant',cards:['quote']}]),'new-plan');
 assert.equal(reviewMessage([{id:'legacy',role:'assistant',cards:[]},...rows.slice(1)]),'legacy');
});
test('text reader preserves original section order and highlights across a Markdown heading',()=>{
 const text='# Questions\n\n## Service area\nFictional homes only. No real address.\n\n## Supplies\nBring a mop.';
 const content='Service area\nFictional homes only. No real address.';
 const blocks=sourceTextBlocks(text,[{content,excerpt:'Service area\nFictional homes only.'}]);
 assert.deepEqual(blocks.filter(block=>block.level).map(block=>block.parts.map(part=>part.text).join('')),['Questions','Service area','Supplies']);
 assert.deepEqual(blocks.flatMap(block=>block.parts.filter(part=>part.highlight).map(part=>part.text)),['Service area','Fictional homes only.']);
});
