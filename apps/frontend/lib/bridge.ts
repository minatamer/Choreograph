export function approvedRoute(method: string, segments: string[]) {
  const route = segments.join('/');
  const uuid = '[0-9a-f-]{36}';
  const rules: Record<string, RegExp[]> = {
    GET: [/^session$/, /^availability$/, new RegExp(`^documents/${uuid}$`), new RegExp(`^documents/${uuid}/source$`),new RegExp(`^requests/${uuid}/availability$`)],
    POST: [/^session$/, /^reset$/, /^chat$/, /^requests$/, /^documents\/(service|preparation|access|changes|safety|questions)\/replace$/, /^crm\/(connect|callback|setup|skip|consent|disconnect|finish)$/, new RegExp(`^requests/${uuid}/(approve|cancel|complete|reschedule)$`)],
    PUT: [/^draft$/, new RegExp(`^documents/${uuid}$`)],
  };
  return (rules[method] ?? []).some(rule => rule.test(route));
}

export async function boundedBody(stream: ReadableStream<Uint8Array> | null, max: number, timeout=10_000) {
  if(!stream) return new Uint8Array();
  const reader=stream.getReader();const chunks:Uint8Array[]=[];let size=0;
  let timer:ReturnType<typeof setTimeout>|undefined;
  const read=async()=>{
    while(true){const part=await reader.read();if(part.done)break;size+=part.value.length;
      if(size>max)throw new Error('BODY_TOO_LARGE');chunks.push(part.value);}
    const result=new Uint8Array(size);let offset=0;for(const chunk of chunks){result.set(chunk,offset);offset+=chunk.length;}return result;
  };
  try {return await Promise.race([read(),new Promise<never>((_,reject)=>{timer=setTimeout(()=>reject(new Error('BODY_TIMEOUT')),timeout);})]);}
  catch(error){await reader.cancel().catch(()=>{});throw error;}
  finally{clearTimeout(timer);reader.releaseLock();}
}
