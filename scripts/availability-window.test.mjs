import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import ts from 'typescript';
import * as windowing from '../apps/frontend/lib/availability-window.ts';
import {localDay} from '../apps/frontend/lib/calendar-metrics.ts';
import {periodSlots} from '../apps/frontend/lib/availability-period.ts';
import {clockReader,weekUtcOffset} from '../apps/frontend/lib/timezone.ts';

test('initial dates clamp stale, malformed and out-of-horizon requests to today',()=>{
 const today='2026-10-25';
 for(const initial of [undefined,'2026-10-24','2026-10-19','2026-11-24','2026-13-25','2026-02-30','invalid']){
  assert.equal(windowing.calendarWindowStart(today,initial),today);
 }
 assert.equal(windowing.calendarWindowStart(today,'2026-10-28'),'2026-10-28');
 assert.equal(windowing.calendarWindowStart(today,'2026-11-23'),'2026-11-23');
 assert.equal(windowing.calendarWindowStart(today,undefined,false),'2026-10-19');
});

test('selection drops past and too-late dates and chooses actual matching availability',()=>{
 const week={days:[{date:'2026-10-24',status:'past',slots:[]},{date:'2026-10-25',status:'closed',slots:[]},
  {date:'2026-10-26',status:'busy',slots:[]},{date:'2026-10-27',status:'available',slots:[{start:'2026-10-27T14:00:00Z'}]},
  {date:'2026-10-28',status:'available',slots:[{start:'2026-10-28T09:00:00Z'}]}]};
 const matches=day=>periodSlots(day.slots,'UTC','morning').length>0;
 assert.equal(windowing.calendarSelectedDay(week,'2026-10-25','2026-10-24',matches),'2026-10-28');
 assert.equal(windowing.calendarSelectedDay(week,'2026-10-25','2026-10-26',matches),'2026-10-26'); // explicit busy-day inspection
 assert.equal(windowing.calendarSelectedDay({days:[{date:'2026-10-25',status:'past',slots:[]},...week.days.slice(2)]},
  '2026-10-25','2026-10-25',day=>day.slots.length>0),'2026-10-27');
 assert.equal(windowing.calendarSelectedDay({days:[]},'2026-10-25','',matches),'');
});

const require=createRequire(import.meta.url),jsx=require('react/jsx-runtime');
const code=ts.transpileModule(readFileSync(new URL('../apps/frontend/components/week-calendar.tsx',import.meta.url),'utf8'),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX},
}).outputText;
function find(node,predicate){
 if(!node||typeof node!=='object')return;
 if(predicate(node))return node;
 for(const child of [node.props?.children].flat(Infinity)){const match=find(child,predicate);if(match)return match;}
}
function calendar({zone='Africa/Cairo',initialDate='2026-10-24',request,instant='2026-10-25T08:00:00Z'}={}){
 let index=0,tree;const values=[],effects=[],cleanups=[],dependencies=[],requests=[],selected=[];
 let now=Date.parse(instant);
 class ClockDate extends Date{static now(){return now;}}
 const deps={react:{useState:initial=>{const slot=index++;if(!(slot in values))values[slot]=typeof initial==='function'?initial():initial;
  return [values[slot],update=>{values[slot]=typeof update==='function'?update(values[slot]):update;}];},
  useEffect:(callback,next)=>{const slot=index++;
   if(!dependencies[slot]||next.some((value,n)=>!Object.is(value,dependencies[slot][n]))){dependencies[slot]=next;effects.push(()=>{cleanups[slot]?.();cleanups[slot]=callback();});}}},
  'react/jsx-runtime':jsx,'@/lib/availability-window':windowing,'@/lib/calendar-metrics':{localDay},
  '@/lib/availability-period':{periodSlots},'@/lib/timezone':{weekUtcOffset},
  '@/lib/availability-copy':{availabilityLabel:day=>day.status,unavailableReason:()=> 'No times'},
  './ui':{Badge:()=>null},'@/lib/api':{clockReader,duration:()=> '3h',api:async endpoint=>{
   requests.push(endpoint);const start=new URLSearchParams(endpoint.split('?')[1]).get('start');
   assert.ok(start,'Appointment pickers must request a rolling window');
   return {week_start:start,timezone:zone,minutes:180,preview:false,can_previous:start>localDay(now,zone),can_next:true,
    days:Array.from({length:7},(_,n)=>{const date=new Date(start+'T12:00:00Z');date.setUTCDate(date.getUTCDate()+n);
     const day=date.toISOString().slice(0,10),closed=date.getUTCDay()===0;
     return {date:day,weekday:date.toLocaleDateString('en',{weekday:'short',timeZone:'UTC'}),status:closed?'closed':'available',
      occupied:[],slots:closed?[]:[{start:day+'T09:00:00Z',end:day+'T12:00:00Z',staff_ids:['ada']}]};})};}}};
 const Component=new Function('require','exports','Date',code+'\nreturn WeekCalendar;')(
  name=>{assert.ok(name in deps,'Unexpected dependency '+name);return deps[name];},{},ClockDate);
 function render(){index=0;tree=Component({state:{workspace_id:'fixture',generation:1,revision:1,timezone:zone,quote:{minutes:180},
  draft:{},scenario:{week_start:'2026-10-19'},calendar_week_start:'2026-10-19'},initialDate,request,pending:false,onSelect:value=>selected.push(value)});}
 render();
 return {requests,selected,tree:()=>tree,render,advance:milliseconds=>{now+=milliseconds;},
  settle:async()=>{for(const effect of effects.splice(0))effect();for(let n=0;n<6;n++)await Promise.resolve();render();},
  cleanup:()=>cleanups.forEach(cleanup=>cleanup?.())};
}

test('Sunday with a restored Saturday request opens upcoming days and chooses Monday without booking',async()=>{
 const h=calendar();await h.settle();
 assert.deepEqual(h.requests,['availability?start=2026-10-25']);
 const days=find(h.tree(),node=>node.props?.['aria-label']==='Seven days of appointments');
 assert.equal(days.props.children[0].props['data-date'],'2026-10-25');
 assert.equal(days.props.children.find(day=>day.props['aria-pressed']).props['data-date'],'2026-10-26');
 assert.deepEqual(h.selected,[]);h.cleanup();
});

test('initial window follows the saved scheduling timezone across midnight',async()=>{
 for(const [zone,expected] of [['Africa/Cairo','2026-10-25'],['America/New_York','2026-10-24']]){
  const h=calendar({zone,initialDate:undefined,instant:'2026-10-25T00:30:00Z'});await h.settle();
  assert.equal(h.requests[0],'availability?start='+expected);h.cleanup();
 }
});

test('future preferences and rescheduling use the same upcoming window and retain draft-only selection',async()=>{
 const h=calendar({initialDate:'2026-10-28',request:{id:'booking',revision:1,quote:{minutes:180}}});await h.settle();
 assert.equal(h.requests[0],'requests/booking/availability?start=2026-10-28');
 const previous=find(h.tree(),node=>node.props?.['aria-label']==='Previous seven days');
 assert.equal(previous.props.disabled,false);previous.props.onClick();h.render();await h.settle();
 assert.equal(h.requests.at(-1),'requests/booking/availability?start=2026-10-25');
 const options=find(h.tree(),node=>node.props?.className==='time-options');
 assert.ok(options);options.props.children[0].props.onClick();assert.equal(h.selected.length,1);h.cleanup();
});

test('a mounted card clamps its old window on the next update after the local day advances',async()=>{
 const h=calendar({initialDate:undefined,instant:'2026-10-24T20:59:30Z'});await h.settle();
 assert.equal(h.requests[0],'availability?start=2026-10-24');
 h.advance(60_000);h.render();await h.settle();
 assert.equal(h.requests.at(-1),'availability?start=2026-10-25');h.cleanup();
});
