export const TOUR_PREFERENCE='choreograph:workspace-tour:v1';
type PreferenceStore=Pick<Storage,'getItem'|'setItem'>;
export function tourWasSeen(store:()=>PreferenceStore){try{return store().getItem(TOUR_PREFERENCE)==='seen';}catch{return false;}}
export function markTourSeen(store:()=>PreferenceStore){try{store().setItem(TOUR_PREFERENCE,'seen');}catch{/* A blocked UI preference must never block the demo. */}}
