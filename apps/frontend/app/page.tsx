import Link from 'next/link';
import {Wordmark,Mark,Arrow,ActionLink,Badge} from '@/components/ui';

const days=[['MON','26','Question','What’s included?'],['TUE','27','Source','Guide page 2'],['WED','28','Quote','$185 · 4½ hours'],['THU','29','Request','Morning preferred'],['FRI','30','Fully booked','Booked jobs'],['SAT','31','Available','09:00–13:30'],['SUN','1','Confirmed','Booking complete']];
export default function Landing(){return <main id="main" className="landing">
  <section className="landing-hero" id="idea">
    <nav className="index-rail glass" aria-label="On this page"><Mark/>{[['01','The idea','#idea'],['02','The flow','#flow'],['03','Try demo','/demo']].map(([number,label,href])=><Link key={number} href={href}><strong>{number}</strong><span>{label}</span></Link>)}<small>Front<br/>desk</small></nav>
    <div className="hero-canvas">
      <header className="landing-masthead glass"><Wordmark/><span className="eyebrow">Scheduling for service businesses</span><Link href="/demo" className="mobile-demo-link" aria-label="Try demo"><Arrow/></Link></header>
      <div className="hero-copy"><h1>Answer questions.<br/>Find a time.<br/>Book the job.</h1><div className="hero-invitation"><p>An AI front desk for customer questions, quotes and bookings.</p><ActionLink href="/demo">Try demo</ActionLink><small>Explore fictional Juniper Cleaning.<br/>No Choreograph signup. HubSpot is optional.</small></div></div>
      <div className="landing-week glass"><div className="card-heading"><h2>From enquiry to booking</h2><Badge>Sample week</Badge></div><div className="week-illustration">{days.map(([day,date,title,detail],index)=><div key={day} className={`illustrated-day ${index===4?'occupied':index===5?'selected':index===6?'muted':''}`}><span>{day}</span><strong>{date}</strong><b>{title}</b><small>{detail}</small></div>)}</div><div className="week-footer"><div className="illustrated-conversation"><span>“Friday morning?”</span><Arrow/><span>“Saturday at 09:00”</span></div><small>Your local time</small></div></div>
    </div>
  </section>
  <section id="flow" className="landing-flow"><span className="eyebrow blue-text">How it works</span><h2>From enquiry to booking</h2><div className="steps">{[['01','Ask a question','Choose a suggested question or write your own. Read the source beside the answer.'],['02','Choose a time','Check the week and choose an available appointment.'],['03','Confirm the booking','Review the quote and approve the request in Business view.']].map(([n,title,body])=><article key={n}><strong>{n}</strong><h3>{title}</h3><p>{body}</p></article>)}</div></section>
  <section className="landing-cta"><div><h2>Try Juniper Cleaning.</h2><p>Explore sample services, company guides and a pre-filled calendar.</p></div><ActionLink href="/demo">Explore the demo</ActionLink></section>
  <footer className="landing-footer"><Wordmark/><small>AI front desk for service businesses</small></footer>
</main>;}
