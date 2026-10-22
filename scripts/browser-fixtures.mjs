export async function preparedRequest(context,zone='Africa/Cairo'){
  const root='http://127.0.0.1:45860';const origin={origin:root};
  const start=await context.request.post(root+'/api/demo/session',{headers:origin,data:{timezone:zone}});
  if(start.status()!==200)throw Error('Session setup failed');
  let state=await start.json();
  async function change(path,fields,method='POST'){
    const result=await context.request.fetch(root+'/api/demo/'+path,{method,headers:{...origin,'x-csrf-token':state.csrf,'idempotency-key':crypto.randomUUID()},
      data:{generation:state.generation,revision:state.revision,...fields}});
    if(result.status()!==200)throw Error('Synthetic setup command failed: '+result.status());
    const value=await result.json();state=value.state;return value;
  }
  await change('draft',{service:'move-out',bedrooms:2,oven:true},'PUT');
  const week=await (await context.request.get(root+'/api/demo/availability?week='+state.scenario.week_start)).json();
  const day=week.days.find(day=>day.date===state.scenario.alternative_date);
  let slot=day?.slots?.[0];
  if(!slot){const next=new Date(state.scenario.week_start+'T12:00:00Z');next.setUTCDate(next.getUTCDate()+7);
    const other=await (await context.request.get(root+'/api/demo/availability?week='+next.toISOString().slice(0,10))).json();
    slot=other.days.find(day=>day.date===state.scenario.alternative_date)?.slots[0];}
  if(!slot)throw Error('Guided alternative missing');
  await change('draft',{preferred_at:slot.start},'PUT');
  const submitted=await change('requests',{accept_quote:true});
  return {state,requestId:submitted.request_id};
}
