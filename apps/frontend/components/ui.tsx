import Link from 'next/link';
import type {ReactNode,ButtonHTMLAttributes} from 'react';
import brandMark from '@/lib/brand-mark.json';

export function Mark() {
  return <svg className="brand-mark" aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none">{brandMark.map(line=><path key={line.d} d={line.d} stroke={line.color} strokeWidth="2"/>)}</svg>;
}
export function Arrow({direction='right'}:{direction?:'right'|'up'}) {
  return <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" className={direction==='up'?'arrow-up':''}><path d="M4 12h15m-6-6 6 6-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>;
}
export function Wordmark(){return <Link href="/" className="wordmark" aria-label="Choreograph home"><Mark/><span>choreograph</span></Link>;}
export function Spinner(){return <span className="loading-spinner" aria-hidden="true"/>;}
export function Button({children,kind='primary',className='',busy=false,disabled,...props}:ButtonHTMLAttributes<HTMLButtonElement>&{kind?:'primary'|'secondary'|'quiet';children:ReactNode;busy?:boolean}) {
  return <button className={`button ${kind} ${className}`} disabled={disabled||busy} aria-busy={busy||undefined} {...props}>{busy?<span className="button-busy-label">{children}</span>:children}{busy&&<Spinner/>}</button>;
}
export function ActionLink({href,children,secondary=false}:{href:string;children:ReactNode;secondary?:boolean}){
  return <Link href={href} className={`button ${secondary?'secondary':'primary'}`}>{children}<Arrow/></Link>;
}
export function Badge({children,tone='blue'}:{children:ReactNode;tone?:'blue'|'red'|'green'|'amber'|'neutral'}) {return <span className={`badge ${tone}`}>{children}</span>;}
export function AppHeader({children,className=''}:{children?:ReactNode;className?:string}){return <header className={`app-header glass ${className}`}><Wordmark/><div className="header-right">{children}</div></header>;}
