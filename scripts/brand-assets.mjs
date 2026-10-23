import {mkdir,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import sharp from 'sharp';
import brandMark from '../apps/frontend/lib/brand-mark.json' with {type:'json'};

// Offline exports of the same vector used by <Mark/>. No app server needed.
const publicRoot=new URL('../apps/frontend/public/',import.meta.url);
const brandRoot=new URL('brand/',publicRoot);
await mkdir(brandRoot,{recursive:true});
const lines=brandMark.map(({d,color})=>`<path d="${d}" stroke="${color}" stroke-width="2"/>`).join('');
const mark=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">${lines}</svg>\n`;
const icon=`<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="rim" x1="12" y1="4" x2="46" y2="60" gradientUnits="userSpaceOnUse"><stop stop-color="#fff"/><stop offset=".5" stop-color="#e6e9ed"/><stop offset="1" stop-color="#bbc3cc"/></linearGradient>
    <linearGradient id="sheen" x1="24" y1="2" x2="38" y2="62" gradientUnits="userSpaceOnUse"><stop stop-color="#fff"/><stop offset=".7" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#222" stop-opacity=".045"/></linearGradient>
  </defs>
  <circle cx="32" cy="32" r="30.5" fill="#fff" stroke="url(#rim)"/>
  <circle cx="32" cy="32" r="29.25" fill="url(#sheen)"/>
  <path d="M10 26A24 24 0 0 1 32 8" fill="none" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>
  <g transform="translate(10 8) scale(2)" fill="none" shape-rendering="crispEdges">${lines}</g>
</svg>\n`;
await writeFile(new URL('mark.svg',brandRoot),mark);
await writeFile(new URL('icon.svg',publicRoot),icon);
const png=async size=>sharp(Buffer.from(icon)).resize(size,size).png().toBuffer();
await writeFile(new URL('icon.png',publicRoot),await png(96));
for(const size of [192,512])await writeFile(new URL(`icon-${size}.png`,brandRoot),await png(size));
await writeFile(new URL('apple-touch-icon.png',publicRoot),await sharp(await png(180)).flatten({background:'#fff'}).png().toBuffer());

// PNG-backed ICO directory: small Chrome tabs through high-density shortcuts.
const sizes=[16,32,48,96,256];
const images=await Promise.all(sizes.map(png));
const directory=Buffer.alloc(6+16*sizes.length);
directory.writeUInt16LE(1,2);directory.writeUInt16LE(sizes.length,4);
let offset=directory.length;
images.forEach((bytes,index)=>{
  const entry=6+16*index,size=sizes[index];
  directory[entry]=size===256?0:size;directory[entry+1]=size===256?0:size;
  directory.writeUInt16LE(1,entry+4);directory.writeUInt16LE(32,entry+6);
  directory.writeUInt32LE(bytes.length,entry+8);directory.writeUInt32LE(offset,entry+12);
  offset+=bytes.length;
});
await writeFile(new URL('favicon.ico',publicRoot),Buffer.concat([directory,...images]));
console.log(`Generated Choreograph mark, circular SVG/PNG/ICO, Apple and manifest icons in ${fileURLToPath(publicRoot)}`);
