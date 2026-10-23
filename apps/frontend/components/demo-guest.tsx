'use client';
import {createContext,useContext,type ReactNode} from 'react';
import {useGuest} from './use-guest';

const DemoGuestContext=createContext<ReturnType<typeof useGuest>|null>(null);

export function DemoGuestProvider({children}:{children:ReactNode}){
  // The intro starts the session explicitly. The demo layout then keeps it
  // through client navigation, without another initialization at the front desk.
  const guest=useGuest(false);
  return <DemoGuestContext.Provider value={guest}>{children}</DemoGuestContext.Provider>;
}

export function useDemoGuest(){
  const guest=useContext(DemoGuestContext);
  if(!guest)throw new Error('Demo guest provider is required.');
  return guest;
}
