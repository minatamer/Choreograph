import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import ts from 'typescript';

// Exercise the real effect with font and frame readiness under explicit control.
const require=createRequire(import.meta.url);
const code=ts.transpileModule(readFileSync(new URL('../apps/frontend/components/landing-motion.tsx',import.meta.url),'utf8'),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},
}).outputText;

function harness({fonts=true}={}){
 let resolveFont,effect,nextFrame=0;
 const ready=new Promise(resolve=>{resolveFont=resolve;});
 const lead={dataset:{}};const frames=new Map();
 const deps={react:{useRef:()=>({current:lead}),useEffect:callback=>{effect=callback;}},
  'react/jsx-runtime':require('react/jsx-runtime'),'motion/react':{},'./ui':{ActionLink:()=>null}};
 const component=new Function('require','exports','document','requestAnimationFrame','cancelAnimationFrame',
  code+'\nreturn LandingHero;')(name=>{assert.ok(name in deps);return deps[name];},{},
  fonts?{fonts:{ready}}:{},callback=>{frames.set(++nextFrame,callback);return nextFrame;},id=>frames.delete(id));
 component();
 return {lead,frames,mount:()=>effect(),resolveFont,
  flushFrame:()=>{const [id,callback]=frames.entries().next().value;frames.delete(id);callback();},
  settle:async()=>{await Promise.resolve();await Promise.resolve();}};
}

test('entrance starts once font readiness and both preparation frames complete',async()=>{
 const h=harness();const cleanup=h.mount();
 assert.equal(h.frames.size,0);assert.equal(h.lead.dataset.entered,undefined);
 h.resolveFont();await h.settle();assert.equal(h.frames.size,1);
 h.flushFrame();assert.equal(h.lead.dataset.entered,undefined);
 h.flushFrame();assert.equal(h.lead.dataset.entered,'true');assert.equal(h.frames.size,0);
 cleanup();
});

test('unmount before font readiness cannot start a late animation',async()=>{
 const h=harness();h.mount()();h.resolveFont();await h.settle();
 assert.equal(h.frames.size,0);assert.equal(h.lead.dataset.entered,undefined);
});

test('unmount between preparation frames cancels the remaining callback',async()=>{
 const h=harness();const cleanup=h.mount();h.resolveFont();await h.settle();h.flushFrame();cleanup();
 assert.equal(h.frames.size,0);assert.equal(h.lead.dataset.entered,undefined);
});

test('browsers without the font readiness API still prepare and animate',async()=>{
 const h=harness({fonts:false});const cleanup=h.mount();await h.settle();
 h.flushFrame();h.flushFrame();assert.equal(h.lead.dataset.entered,'true');cleanup();
});
