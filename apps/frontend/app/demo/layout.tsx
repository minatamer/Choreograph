import type {ReactNode} from 'react';
import {DemoGuestProvider} from '@/components/demo-guest';
import './guides.css';
import './workspace.css';
import './calendar-details.css';
import './tour.css';
import './customer-chat.css';
import './expanding-dialog.css';
import './source-citations.css';
import './verification.css';
import './booking-management.css';
import './availability.css';
import './workspace-shell.css';
import './overview.css';
import './activity-chart.css';

export default function DemoLayout({children}:{children:ReactNode}){
  return <DemoGuestProvider>{children}</DemoGuestProvider>;
}
