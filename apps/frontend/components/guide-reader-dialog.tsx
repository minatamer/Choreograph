'use client';
import {motion} from 'motion/react';
import {ExpandingDialog} from './expanding-dialog';
import {SourceReader,type SourceSelection} from './source-reader';

export function GuideReaderDialog({selection,onClose,opener,layoutId=selection.version_id}:{selection:SourceSelection;onClose:()=>void;opener:HTMLElement|null;layoutId?:string}){
 return <ExpandingDialog layoutId={layoutId} className="guide-reader-dialog" label="Document reader" onClose={onClose} opener={opener}><motion.div className="guide-reader-content" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} transition={{duration:.18,delay:.12}}><SourceReader selection={selection} onClose={onClose}/></motion.div></ExpandingDialog>;
}
