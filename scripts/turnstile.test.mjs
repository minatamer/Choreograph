import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mountVerification} from '../apps/frontend/lib/turnstile.ts';

test('background success is action/command bound and never opens a dialog',()=>{
 let options,opened=0;const results=[],removed=[];
 const api={render:(node,value)=>{options=value;return 'widget';},remove:id=>removed.push(id)};
 const stop=mountVerification(api,{},'public-site','assistant','command',proof=>results.push(proof),()=>opened++);
 assert.equal(options.appearance,'interaction-only');assert.equal(options.retry,'never');
 assert.equal(options.action,'assistant');assert.equal(options.cData,'command');assert.equal(options['response-field'],false);
 options.callback('proof');options['before-interactive-callback']();options.callback('late');
 assert.deepEqual(results,['proof']);assert.equal(opened,0);stop();stop();assert.deepEqual(removed,['widget']);
});
test('only required interaction opens the dialog; failure ends this attempt once',()=>{
 let options,opened=0;const results=[];
 const stop=mountVerification({render:(node,value)=>{options=value;return 'id';},remove:()=>{}},{},'site','workspace','key',
  proof=>results.push(proof),()=>opened++);
 options['before-interactive-callback']();assert.equal(opened,1);
 assert.equal(options['error-callback'](),true);options['expired-callback']();options['timeout-callback']();
 assert.deepEqual(results,[undefined]);stop();
});
test('unmount fences late callbacks and removes only its own widget',()=>{
 let options;const removed=[];
 const stop=mountVerification({render:(node,value)=>{options=value;return 'owned';},remove:id=>removed.push(id)},{},'site','documents','key',
  ()=>assert.fail('late callback'),()=>assert.fail('late interaction'));
 stop();options.callback('late');options['unsupported-callback']();options['before-interactive-callback']();
 assert.deepEqual(removed,['owned']);
});
test('synchronous success, render error and cleanup error settle safely',()=>{
 const results=[];
 const stop=mountVerification({render:(node,options)=>{options.callback('sync');return 'id';},remove:()=>{throw Error('vendor');}},
  {},'site','assistant','key',proof=>results.push(proof),()=>assert.fail('interaction'));
 stop();assert.deepEqual(results,['sync']);
 mountVerification({render:()=>{throw Error('vendor');},remove:()=>assert.fail('no widget')},{},'site','assistant','key',
  proof=>results.push(proof),()=>{})();
 assert.deepEqual(results,['sync',undefined]);
});
