import type {Metadata} from 'next';
import localFont from 'next/font/local';
import './tokens.css';
import './globals.css';
const sans=localFont({src:'./fonts/GoogleSansFlex.ttf',weight:'1 1000',style:'normal',display:'swap',variable:'--font-sans'});
export const metadata:Metadata={title:'Choreograph — A better time, arranged.',description:'An AI front desk for customer questions, quotes and bookings. Try the fictional Juniper Cleaning demo.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en" className={sans.variable}><body><a className="skip-link" href="#main">Skip to content</a>{children}</body></html>;}
