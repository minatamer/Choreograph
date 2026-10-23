import type {Metadata} from 'next';
import localFont from 'next/font/local';
import {ScrollButton} from '@/components/scroll-button';
import './tokens.css';
import './globals.css';
import './materials.css';
const sans=localFont({src:'./fonts/GoogleSansFlex.ttf',weight:'1 1000',style:'normal',display:'swap',variable:'--font-sans'});
export const metadata:Metadata={
  title:'Choreograph — A better time, arranged.',
  description:'An AI front desk for customer questions, quotes and bookings. Try the fictional Juniper Cleaning demo.',
  icons:{
    icon:[
      {url:'/favicon.ico',type:'image/x-icon',sizes:'16x16 32x32 48x48 96x96 256x256'},
      {url:'/icon.png',type:'image/png',sizes:'96x96'},
      {url:'/icon.svg',type:'image/svg+xml',sizes:'any'},
    ],
    apple:[{url:'/apple-touch-icon.png',type:'image/png',sizes:'180x180'}],
  },
};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en" className={sans.variable}><body><ScrollButton targetId="main" className="skip-link">Skip to content</ScrollButton>{children}</body></html>;}
