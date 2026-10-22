import {readFileSync,writeFileSync} from 'node:fs';
const tokens=JSON.parse(readFileSync(new URL('../design/figma/tokens.json',import.meta.url),'utf8'));
const cssName=name=>'--'+name.replaceAll('/','-').replace(/([a-z])([A-Z])/g,'$1-$2').toLowerCase();
const lines=['/* Generated from the approved Figma foundations. Edit design/figma/tokens.json. */',':root {'];
for(const [name,value] of Object.entries(tokens.primitives))lines.push(`  ${cssName(name)}: ${value};`);
for(const [name,value] of Object.entries(tokens.colors))lines.push(`  ${cssName(name)}: var(${cssName(value)});`);
lines.push('}','');
writeFileSync(new URL('../apps/frontend/app/tokens.css',import.meta.url),lines.join('\n'));
