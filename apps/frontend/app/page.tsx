import {Wordmark,ActionLink} from '@/components/ui';
import {BusinessStatistics} from '@/components/business-statistics';
import {LandingHero,ProductReveal,ScrollReveal} from '@/components/landing-motion';
import {HeroSchedule} from '@/components/hero-schedule';
import {HeroCollage} from '@/components/hero-collage';
import {HeroScrollCue} from '@/components/hero-scroll-cue';
import {WorkflowSteps} from '@/components/workflow-steps';
import './landing-hero.css';
import './landing-sections.css';

export default function Landing(){return <main id="main" className="landing">
  <HeroCollage/>
  <section className="landing-hero" id="idea">
    <div className="hero-canvas">
      <header className="landing-masthead glass"><Wordmark/><nav className="landing-nav" aria-label="Main navigation"><ActionLink href="/demo">Try demo</ActionLink></nav></header>
      <LandingHero/>
      <HeroScrollCue/>
    </div>
  </section>
  <section id="flow" className="landing-flow"><ScrollReveal className="flow-heading"><span className="eyebrow blue-text">How it works</span><h2>From enquiry to booking</h2></ScrollReveal><ProductReveal><HeroSchedule/></ProductReveal><WorkflowSteps/></section>
  <BusinessStatistics/>
  <footer className="landing-footer"><Wordmark/><small>AI front desk for service businesses</small></footer>
</main>;}
