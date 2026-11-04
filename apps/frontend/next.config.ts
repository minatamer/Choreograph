import type {NextConfig} from 'next';
import path from 'node:path';
const config: NextConfig = {
  output: 'standalone',
  outputFileTracingRoot: path.resolve(import.meta.dirname,'../..'),
  poweredByHeader: false,
  devIndicators: false,
  logging:{incomingRequests:{ignore:[/^\/auth\/hubspot\/callback/]}},
  async redirects(){
    const origin=process.env.CHOREOGRAPH_ORIGIN;
    // Match the browser's host before NextURL normalizes loopback addresses.
    // Keep guest cookies, write-origin checks and the OAuth host aligned.
    const local=origin==='http://localhost:45860'?[{
      source:'/demo/:path*',has:[{type:'host' as const,value:'127[.]0[.]0[.]1'}],
      destination:origin+'/demo/:path*',permanent:false,
    }]:[];
    // Preserve old portfolio links without redirecting API or OAuth requests.
    const hosted=['/','/demo/:path*'].map(source=>({
      source,has:[{type:'host' as const,value:'choreograph-frontend-ue3m7uxqdq-ew[.]a[.]run[.]app'}],
      destination:'https://trychoreograph.com'+source,permanent:true,
    }));
    return [...local,...hosted];
  },
  async headers() {
    return [{source:'/(.*)',headers:[
      {key:'X-Content-Type-Options',value:'nosniff'},
      {key:'Referrer-Policy',value:'same-origin'},
      {key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=()'},
      {key:'X-Frame-Options',value:'DENY'},
    ]}];
  },
};
export default config;
