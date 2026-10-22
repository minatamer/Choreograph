import {boundedBody} from './bridge.ts';

type Values=Record<string,string|undefined>;
export function configuredAPI(values:Values=process.env){
  const url=new URL(values.CHOREOGRAPH_API_URL??'http://127.0.0.1:45861');
  if(url.pathname!=='/'||url.username||url.password||url.search||url.hash||!['http:','https:'].includes(url.protocol))throw Error('API_CONFIGURATION_INVALID');
  // HTTP is confined to this checkout's loopback or isolated Docker API alias.
  if(url.protocol==='http:'&&!['127.0.0.1','localhost','[::1]','api'].includes(url.hostname))throw Error('API_CONFIGURATION_INVALID');
  return url;
}

export function createAPIAuthorizer(fetcher:typeof fetch=fetch,now:()=>number=Date.now){
  let cached:{audience:string;token:string;expires:number}|null=null;
  let pending:{audience:string;promise:Promise<string>}|null=null;
  async function identity(audience:string){
    if(cached?.audience===audience&&cached.expires>now()+60_000)return cached.token;
    if(pending?.audience===audience)return pending.promise;
    const promise=(async()=>{
      // Fixed server-side metadata destination. Guest input never selects it.
      const metadata=new URL('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity');
      metadata.searchParams.set('audience',audience);metadata.searchParams.set('format','full');
      const response=await fetcher(metadata,{headers:{'Metadata-Flavor':'Google'},redirect:'error',cache:'no-store',signal:AbortSignal.timeout(2000)});
      if(!response.ok||response.headers.get('Metadata-Flavor')!=='Google')throw Error('API_IDENTITY_UNAVAILABLE');
      const bytes=await boundedBody(response.body,8192,2000);const token=new TextDecoder().decode(bytes).trim();
      if(!/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(token))throw Error('API_IDENTITY_INVALID');
      const claims=JSON.parse(Buffer.from(token.split('.')[1],'base64url').toString('utf8'));
      if(claims.aud!==audience||!Number.isFinite(claims.exp)||claims.exp*1000<=now()+60_000)throw Error('API_IDENTITY_INVALID');
      // Metadata is the trusted token issuer here; receiving Cloud Run IAM
      // verifies its signature. Decoding only bounds local cache freshness.
      cached={audience,token,expires:claims.exp*1000};return token;
    })();
    pending={audience,promise};
    try{return await promise;}finally{if(pending?.promise===promise)pending=null;}
  }
  return async(headers:Headers,api:URL,values:Values=process.env)=>{
    const mode=values.CHOREOGRAPH_API_AUTH??'none';
    if(mode==='none')return;
    if(mode!=='google'||api.protocol!=='https:')throw Error('API_IDENTITY_CONFIGURATION_INVALID');
    const audience=values.CHOREOGRAPH_API_AUDIENCE??api.origin;
    const target=new URL(audience);
    if(target.protocol!=='https:'||target.username||target.password||target.search||target.hash||target.pathname!=='/')throw Error('API_IDENTITY_CONFIGURATION_INVALID');
    headers.set('authorization',`Bearer ${await identity(audience)}`);
  };
}

export const authorizeAPI=createAPIAuthorizer();
