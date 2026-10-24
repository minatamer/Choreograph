export type HighlightTarget={excerpt:string;content:string};
export type TextMatch={item:number;from:number;to:number};

function indexed(text:string){
 const units:{value:string;from:number;to:number}[]=[];let position=0;
 for(const char of text){
  const value=char.normalize('NFKC').replace(/[‘’]/g,"'").replace(/[“”]/g,'"').toLowerCase();
  for(let index=0;index<value.length;index++)if(!/\s/.test(value[index]))units.push({value:value[index],from:position,to:position+char.length});
  position+=char.length;
 }
 return {text:units.map(unit=>unit.value).join(''),units};
}

/** Exact normalized text matching only; never invent a highlight on missing evidence. */
export function sourceTextMatches(items:string[],targets:HighlightTarget[]):TextMatch[]{
 let cursor=0;
 const runs=items.map(text=>{const value=indexed(text);const start=cursor;cursor+=value.text.length;return {...value,start,end:cursor};});
 const text=runs.map(run=>run.text).join('');const matches:TextMatch[]=[];
 for(const target of targets){
  if(!target.excerpt.trim()||!target.content.includes(target.excerpt))continue;
  const excerpt=indexed(target.excerpt).text,context=indexed(target.content).text;
  if(!excerpt)continue;
  const contextStart=text.indexOf(context),base=contextStart<0?0:contextStart;
  if(contextStart<0){const first=text.indexOf(excerpt);if(first>=0&&text.indexOf(excerpt,first+excerpt.length)>=0)continue;}
  const window=contextStart<0?text:text.slice(base,base+context.length);
  const found=window.indexOf(excerpt);if(found<0)continue;
  const start=base+found,end=start+excerpt.length;
  runs.forEach((run,item)=>{
   const first=Math.max(start,run.start)-run.start,last=Math.min(end,run.end)-run.start-1;
   if(first<0||last<first||!run.units[first]||!run.units[last])return;
   matches.push({item,from:run.units[first].from,to:run.units[last].to});
  });
 }
 return matches.filter((match,index)=>matches.findIndex(other=>other.item===match.item&&other.from===match.from&&other.to===match.to)===index);
}

function textParts(text:string,ranges:{start:number;end:number}[]){
 ranges.sort((a,b)=>a.start-b.start);const merged:typeof ranges=[];
 for(const range of ranges){const last=merged.at(-1);if(last&&range.start<=last.end)last.end=Math.max(last.end,range.end);else merged.push({...range});}
 const parts:{text:string;highlight:boolean}[]=[];let start=0;
 for(const range of merged){if(range.start>start)parts.push({text:text.slice(start,range.start),highlight:false});parts.push({text:text.slice(range.start,range.end),highlight:true});start=range.end;}
 if(start<text.length)parts.push({text:text.slice(start),highlight:false});return parts;
}

/** Preserve the original Markdown/text order rather than assembling unordered retrieval chunks. */
export function sourceTextBlocks(text:string,targets:HighlightTarget[]){
 const matches=sourceTextMatches([text],targets);let position=0;
 return text.split('\n').flatMap(line=>{
  const start=position;position+=line.length+1;const raw=line.replace(/\r$/,'');if(!raw.trim())return [];
  const heading=/^(#{1,3})[ \t]+/.exec(raw),prefix=heading?.[0].length??0,body=raw.slice(prefix);
  const ranges=matches.map(match=>({start:Math.max(0,match.from-start-prefix),end:Math.min(body.length,match.to-start-prefix)})).filter(range=>range.end>range.start);
  return [{position:start,level:heading?.[1].length??0,parts:textParts(body,ranges)}];
 });
}
