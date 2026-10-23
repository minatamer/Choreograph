/** Display an instant's offset, while retaining the saved IANA zone for scheduling. */
function offsetAt(formatter:Intl.DateTimeFormat,instant:string|number|Date){
 const label=formatter.formatToParts(new Date(instant)).find(part=>part.type==='timeZoneName')!.value;
 return label.replace(/^GMT/,'UTC').replace(/^UTC[+-]00:00$/,'UTC');
}
export function utcOffset(zone:string,instant:string|number|Date){
 return offsetAt(new Intl.DateTimeFormat('en-US',{timeZone:zone,timeZoneName:'longOffset'}),instant);
}

/** A displayed week can cross a daylight-saving change. */
export function weekUtcOffset(zone:string,week:string){
 const start=new Date(week+'T12:00:00Z');
 const formatter=new Intl.DateTimeFormat('en-US',{timeZone:zone,timeZoneName:'longOffset'});
 const offsets=Array.from({length:7},(_,index)=>offsetAt(formatter,start.getTime()+index*86400000));
 return [...new Set(offsets)].join(' / ');
}
