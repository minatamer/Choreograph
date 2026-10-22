import type {NextConfig} from 'next';
import path from 'node:path';
const config: NextConfig = {
  output: 'standalone',
  outputFileTracingRoot: path.resolve(import.meta.dirname,'../..'),
  poweredByHeader: false,
  devIndicators: false,
  logging:{incomingRequests:{ignore:[/^\/auth\/hubspot\/callback/]}},
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
