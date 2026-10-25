import {EntryClient} from '@/components/entry-client';
import './welcome.css';
export default async function Entry({searchParams}:{searchParams:Promise<Record<string,string|string[]|undefined>>}){
  const {crm,step}=await searchParams;
  return <EntryClient resumeSetup={step==='connect'||crm==='connected'||crm==='unavailable'||crm==='cancelled'}/>;
}
