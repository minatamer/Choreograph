import Link from 'next/link';
import type {ReactNode,ButtonHTMLAttributes} from 'react';

export function Mark() {
  return <svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M2 6h18" stroke="var(--color-action-primary)" strokeWidth="2"/><path d="M2 12h11" stroke="var(--color-status-confirmed)" strokeWidth="2"/><path d="M2 18h15" stroke="var(--color-status-occupied)" strokeWidth="2"/></svg>;
}
export function Arrow({direction='right'}:{direction?:'right'|'up'}) {
  return <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" className={direction==='up'?'arrow-up':''}><path d="M4 12h15m-6-6 6 6-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>;
}
export function Wordmark(){return <Link href="/" className="wordmark" aria-label="Choreograph home"><Mark/><span>choreograph</span></Link>;}
export function Button({children,kind='primary',className='',...props}:ButtonHTMLAttributes<HTMLButtonElement>&{kind?:'primary'|'secondary'|'quiet';children:ReactNode}) {
  return <button className={`button ${kind} ${className}`} {...props}>{children}</button>;
}
export function ActionLink({href,children,secondary=false}:{href:string;children:ReactNode;secondary?:boolean}){
  return <Link href={href} className={`button ${secondary?'secondary':'primary'}`}>{children}<Arrow/></Link>;
}
export function Badge({children,tone='blue'}:{children:ReactNode;tone?:'blue'|'red'|'green'|'amber'|'neutral'}) {return <span className={`badge ${tone}`}>{children}</span>;}
export function AppHeader({children}:{children?:ReactNode}){return <header className="app-header glass"><Wordmark/><div className="header-right">{children}</div></header>;}
