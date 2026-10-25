import {NextRequest} from 'next/server';
import {approvedRoute,boundedBody} from '@/lib/bridge';
import {configuredAPI,authorizeAPI} from '@/lib/private-api';

async function bridge(request: NextRequest, context: {params: Promise<{path:string[]}>}) {
  const {path} = await context.params;
  if (!approvedRoute(request.method,path)) return Response.json({code:'ROUTE_UNAVAILABLE'}, {status:404});
  const origin = process.env.CHOREOGRAPH_ORIGIN ?? 'http://127.0.0.1:45860';
  if (!['GET','HEAD'].includes(request.method) && request.headers.get('origin') !== origin)
    return Response.json({code:'ORIGIN_REQUIRED',message:'This page uses an old address. Reload the demo and try again.'}, {status:403});
  const secret = process.env.CHOREOGRAPH_BRIDGE_SECRET;
  if (!secret) return Response.json({code:'SERVICE_UNAVAILABLE'}, {status:503});
  let api:URL;
  try{api=configuredAPI();}catch{return Response.json({code:'SERVICE_UNAVAILABLE'},{status:503});}
  const url = new URL(`/v1/${path.join('/')}`,api);
  for (const key of ['week','start','version','page']) {
    const value = request.nextUrl.searchParams.get(key);
    if (value && value.length <= 80) url.searchParams.set(key,value);
  }
  const headers = new Headers({'x-choreograph-bridge':secret,'origin':origin});
  const guestCookie=request.cookies.get('choreograph_guest')?.value;
  const cookies:string[]=[];
  if(guestCookie && /^[A-Za-z0-9_-]{32,128}$/.test(guestCookie))cookies.push(`choreograph_guest=${guestCookie}`);
  const humanCookie=request.cookies.get('choreograph_human')?.value;
  if(humanCookie&&/^v1\.[0-9]{1,12}\.[0-9]{1,12}\.[0-9a-f]{64}$/.test(humanCookie))cookies.push(`choreograph_human=${humanCookie}`);
  if(cookies.length)headers.set('cookie',cookies.join('; '));
  for (const key of ['content-type','x-csrf-token','idempotency-key']) {
    const value=request.headers.get(key); if(value) headers.set(key,value);
  }
  const proof=request.headers.get('x-turnstile-token');
  if(proof&&proof.length<=2048)headers.set('x-turnstile-token',proof);
  const max = path[0] === 'documents' ? 2_850_000 : 16_384;
  let body: Uint8Array | undefined;
  if (!['GET','HEAD'].includes(request.method)) {
    if(request.headers.get('content-type')?.split(';')[0] !== 'application/json') return Response.json({code:'JSON_REQUIRED'},{status:415});
    try {body=await boundedBody(request.body,max);}
    catch(error){const code=error instanceof Error&&error.message==='BODY_TOO_LARGE'?'BODY_TOO_LARGE':'BODY_TIMEOUT';
      return Response.json({code},{status:code==='BODY_TOO_LARGE'?413:408});}
  }
  try {
    await authorizeAPI(headers,api);
    const timeout=path[0]==='chat'||(path[0]==='documents'&&path[2]==='replace')||(path[0]==='crm'&&['callback','setup'].includes(path[1]))?70_000:25_000;
    const upstream=await fetch(url,{method:request.method,headers,body:body as BodyInit|undefined,redirect:'error',cache:'no-store',signal:AbortSignal.timeout(timeout)});
    const out=new Headers({'cache-control':'no-store','content-type':upstream.headers.get('content-type')??'application/json'});
    for(const cookie of upstream.headers.getSetCookie())out.append('set-cookie',cookie);
    for(const name of ['content-disposition','x-source-page','content-security-policy','x-content-type-options']) {const value=upstream.headers.get(name);if(value)out.set(name,value);}
    return new Response(upstream.body,{status:upstream.status,headers:out});
  } catch {return Response.json({code:'SERVICE_UNAVAILABLE',message:'Please try again in a moment.'},{status:503});}
}
export {bridge as GET,bridge as POST,bridge as PUT};
