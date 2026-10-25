import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import ts from 'typescript';

const code=ts.transpileModule(readFileSync(new URL('../apps/frontend/components/use-chat-scroll.ts',import.meta.url),'utf8'),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022},
}).outputText;
function harness(height=500){
 const effects=[],frames=new Map(),animations=[];let frame=0,observer;
 class Element{
  isConnected=true;focused=0;style={};listeners=new Map();
  constructor(kind,y=0,h=0){this.kind=kind;this.y=y;this.height=h;}
  closest(){return this.kind==='card'?this:null;}
  getBoundingClientRect(){return {top:this===pane?60:60+this.y-pane.scrollTop,height:this.height};}
  focus(options){assert.deepEqual(options,{preventScroll:true});this.focused++;}
  addEventListener(name,callback){const list=this.listeners.get(name)??[];list.push(callback);this.listeners.set(name,list);}
  removeEventListener(name,callback){this.listeners.set(name,(this.listeners.get(name)??[]).filter(value=>value!==callback));}
  emit(name,target=this){for(const callback of this.listeners.get(name)??[])callback({target});}
 }
 const pane=new Element('pane',0,height);pane.clientHeight=height;pane.scrollHeight=2200;pane.scrollTop=0;
 const body=new Element('body',0,2200),card=new Element('card',1800,260);
 let index=0;const refs=[];
 const dependencies={react:{useRef:initial=>{const n=index++;refs[n]={current:n===0?pane:n===1?body:initial};return refs[n];},useLayoutEffect:callback=>effects.push(callback)},
  motion:{animate:(from,to,options)=>{const animation={from,to,options,stopped:false,stop(){this.stopped=true;}};animations.push(animation);return animation;}}};
 class ResizeObserver{
  constructor(callback){this.callback=callback;observer=this;}
  observe(){} disconnect(){this.disconnected=true;}
 }
 const hook=new Function('require','exports','requestAnimationFrame','cancelAnimationFrame','ResizeObserver','Element',
  code+'\nreturn useChatScroll;')(name=>dependencies[name],{},callback=>{frames.set(++frame,callback);return frame;},
  id=>frames.delete(id),ResizeObserver,Element)('message');
 const cleanup=effects[0]();effects[1]();
 const flush=()=>{for(const [id,callback] of [...frames]){frames.delete(id);callback();}};
 flush();pane.emit('wheel');pane.scrollTop=200;
 return {pane,body,card,hook,frames,animations,cleanup,flush,newActivity:()=>effects[1](),
  resize:()=>observer.callback([{target:body}]),observer:()=>observer,
  progress:fraction=>{const active=animations.at(-1);assert.ok(active&&!active.stopped);active.options.onUpdate(active.from+(active.to-active.from)*fraction);if(fraction===1)active.options.onComplete?.();}};
}

for(const [label,height] of [['desktop',700],['short laptop',340],['phone',480]]){
 test(`time selection reveals the review smoothly inside the ${label} history pane`,()=>{
  const h=harness(height);h.pane.emit('click',h.card);
  assert.ok(h.body.style.minHeight);h.hook.reveal.current(h.card);
  assert.equal(h.body.style.minHeight,'');assert.equal(h.pane.scrollTop,200);
  h.flush();const animation=h.animations.at(-1);assert.ok(animation.options.duration>0);
  h.progress(.25);const quarter=h.pane.scrollTop;h.progress(.5);const halfway=h.pane.scrollTop;
  assert.ok(quarter>200&&halfway>quarter&&halfway<animation.to);
  h.progress(1);assert.equal(h.card.focused,1);
  const top=h.card.getBoundingClientRect().top;
  assert.ok(top>=60&&top+h.card.height<=60+height);
  h.cleanup();
 });
}

test('loading-to-ready growth keeps the review visible without stealing focus twice',()=>{
 const h=harness();h.hook.reveal.current(h.card);h.flush();h.progress(1);
 const before=h.pane.scrollTop;h.card.y+=100;h.pane.scrollHeight+=100;h.resize();h.flush();h.progress(1);
 assert.ok(h.pane.scrollTop>before);assert.equal(h.card.focused,1);h.cleanup();
});

test('manual scrolling cancels the reveal and a late resize cannot pull the visitor back',()=>{
 const h=harness();h.hook.reveal.current(h.card);h.flush();h.progress(.5);
 h.pane.emit('wheel');assert.equal(h.animations.at(-1).stopped,true);
 const top=h.pane.scrollTop,count=h.animations.length;h.resize();h.flush();
 assert.equal(h.pane.scrollTop,top);assert.equal(h.animations.length,count);assert.equal(h.card.focused,0);h.cleanup();
});

test('new messages resume ordinary bottom following and unmount retires the reveal',()=>{
 const h=harness();h.hook.reveal.current(h.card);h.flush();h.progress(1);
 h.pane.scrollHeight+=500;h.newActivity();h.flush();h.progress(1);
 assert.equal(h.pane.scrollTop,h.pane.scrollHeight-h.pane.clientHeight);
 assert.equal(h.card.focused,1);h.cleanup();assert.equal(h.observer().disconnected,true);
 h.hook.reveal.current(h.card);assert.equal(h.frames.size,0);
 assert.ok([...h.pane.listeners.values()].every(list=>list.length===0));
});
