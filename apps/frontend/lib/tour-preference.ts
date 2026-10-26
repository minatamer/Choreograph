export const TOUR_PREFERENCE='choreograph:workspace-tour:v2';
type PreferenceStore=Pick<Storage,'getItem'|'setItem'>;
export function tourVisit(state:{workspace_id:string;generation:number}){return `${state.workspace_id}:${state.generation}`;}
export function tourWasSeen(store:()=>PreferenceStore,visit:string){try{return store().getItem(TOUR_PREFERENCE)===visit;}catch{return false;}}
export function markTourSeen(store:()=>PreferenceStore,visit:string){try{store().setItem(TOUR_PREFERENCE,visit);}catch{/* A blocked UI preference must never block the demo. */}}
