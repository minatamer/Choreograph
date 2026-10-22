import {chromium} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
mkdirSync('.runtime/screens',{recursive:true});
const browser=await chromium.launch({headless:true});
const evidence=[];
try {
  for(const [label,width,height] of [['desktop',1440,1000],['short',1280,720],['phone',390,844],['small-phone',320,740]]) {
    const page=await browser.newPage({viewport:{width,height}});const errors=[];
    page.on('pageerror',()=>errors.push('PAGE_ERROR'));
    for(const [name,route] of [['landing','/'],['entry','/demo']]) {
      await page.goto('http://127.0.0.1:45860'+route,{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
      const probe=await page.evaluate(()=>({width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth,
        heading:document.querySelector('h1')?.textContent,font:getComputedStyle(document.body).fontFamily}));
      await page.screenshot({path:`.runtime/screens/${name}-${label}.png`,fullPage:true});
      evidence.push({name,label,width,height,...probe,errors});
    }
    const response=await page.request.get('http://127.0.0.1:45860/api/demo/internal/tick');
    if(response.status()!==404)throw Error('Internal bridge route was exposed');
    await page.close();
  }
} finally {await browser.close();}
writeFileSync('.runtime/shell-evidence.json',JSON.stringify(evidence,null,2));
if(evidence.some(x=>x.scroll>x.width||x.errors.length))throw Error('Visual shell probe failed');
console.log(JSON.stringify(evidence.map(({name,label,scroll,width,errors})=>({name,label,scroll,width,errors}))));
