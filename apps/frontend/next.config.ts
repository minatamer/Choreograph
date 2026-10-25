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
    return origin==='http://localhost:45860'?[{
      source:'/demo/:path*',has:[{type:'host' as const,value:'127[.]0[.]0[.]1'}],
      destination:origin+'/demo/:path*',permanent:false,
    }]:[];
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
