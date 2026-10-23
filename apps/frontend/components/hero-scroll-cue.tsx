import {ScrollButton} from './scroll-button';

export function HeroScrollCue(){
  return <ScrollButton targetId="flow" className="hero-scroll-cue">
    <span className="scroll-cue-desktop"><svg viewBox="0 0 24 34" fill="none" aria-hidden="true"><rect x="4.5" y="2.5" width="15" height="28" rx="7.5" stroke="currentColor" strokeWidth="1.4"/><rect className="scroll-cue-wheel" x="11" y="8" width="2" height="6" rx="1" fill="currentColor"/></svg><span>Scroll for more</span></span>
    <span className="scroll-cue-touch"><svg className="scroll-cue-finger" viewBox="0 0 28 32" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M9 16V6a2 2 0 0 1 4 0v7a2 2 0 0 1 4 0v2a2 2 0 0 1 4 0v2a2 2 0 0 1 4 0v4a7 7 0 0 1-7 7h-2c-3 0-4.5-1.5-6-4l-4-6a2 2 0 0 1 3-2l2 2"/><path d="M13 13v4m4-2v3m4-1v2"/></svg><span>Swipe up for more</span></span>
  </ScrollButton>;
}
