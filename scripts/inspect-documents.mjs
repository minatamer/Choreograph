import {chromium,expect} from '@playwright/test';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
mkdirSync('.runtime/screens',{recursive:true});
const browser=await chromium.launch({headless:true});const results=[];
try{
  for(const [label,width,height] of [['desktop',1440,1000],['short',1280,720],['phone',390,844],['small-phone',320,740]]){
    const context=await browser.newContext({viewport:{width,height},timezoneId:'Africa/Cairo'});const page=await context.newPage();const errors=[];
    page.on('pageerror',error=>errors.push(error.message.slice(0,120)));
    await page.goto('http://127.0.0.1:45860/demo/workspace?view=business');
    const document=page.locator('.document-card').filter({has:page.getByRole('heading',{name:'Service Guide',exact:true})});
    await document.getByRole('button',{name:'Read guide'}).click();
    const reader=page.getByRole('complementary',{name:'Document reader'});
    await expect(reader.getByRole('img',{name:'Service Guide, page 1'})).toBeVisible();
    await expect(reader.locator('canvas')).toHaveAttribute('data-rendered-page','1',{timeout:20000});
    await expect(reader.getByText('Loading page…',{exact:true})).toHaveCount(0,{timeout:20000});
    if(await reader.getByText('The page could not be displayed.',{exact:false}).count())throw Error('Actual PDF canvas failed');
    await reader.getByRole('button',{name:'Next',exact:true}).click();
    await expect(reader.getByRole('img',{name:'Service Guide, page 2'})).toBeVisible();
    await expect(reader.locator('canvas')).toHaveAttribute('data-rendered-page','2',{timeout:20000});
    await expect(reader.locator('.supported-excerpt')).toContainText('Carpet shampooing');
    await expect(reader.getByText('Loading page…',{exact:true})).toHaveCount(0);
    const pixels=await reader.locator('canvas').evaluate(node=>{const data=node.getContext('2d').getImageData(0,0,node.width,node.height).data;let ink=0;for(let i=0;i<data.length;i+=4)if(data[i]<180&&data[i+1]<180&&data[i+2]<180)ink++;return ink;});
    if(pixels<500)throw Error('PDF page has no real ink');
    await page.screenshot({path:`.runtime/screens/source-${label}.png`});
    await reader.getByRole('button',{name:'Close document reader'}).click();
    await page.getByRole('button',{name:'Use revised preparation guide'}).click();
    await expect(page.getByText('The new guide is ready.',{exact:true})).toBeVisible();
    const updated=page.locator('.document-card').filter({has:page.getByRole('heading',{name:'Preparation Guide',exact:true})});
    await expect(updated).toContainText('Guest 1');
    await updated.getByRole('button',{name:'Read guide'}).click();
    await expect(reader.locator('canvas')).toHaveAttribute('data-rendered-page','1',{timeout:20000});
    const session=await (await context.request.get('http://127.0.0.1:45860/api/demo/session')).json();
    const version=session.documents.find(doc=>doc.slot==='preparation');
    const detail=await (await context.request.get(`http://127.0.0.1:45860/api/demo/documents/${version.id}`)).json();
    expect(detail.document.version).toBe('Guest 1');
    expect(detail.passages.some(p=>p.content.includes('outside the home'))).toBe(true);
    // A business-library open has no citation selection; its first page excerpt
    // may be any first ordered passage. Verify the actual passage and PDF bytes.
    await expect(reader.locator('.supported-excerpt mark')).toHaveText(detail.passages.find(p=>p.page===1).content);
    const source=await context.request.get(`http://127.0.0.1:45860/api/demo/documents/${version.id}/source`);
    expect(source.status()).toBe(200);
    const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
    expect(sha(await source.body())).toBe(sha(readFileSync('assets/knowledge/preparation-guide-v2.pdf')));
    await reader.getByRole('button',{name:'Close document reader'}).click();
    await page.reload();await expect(updated).toContainText('Guest 1');
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
    if(overflow||errors.length)throw Error(JSON.stringify({label,overflow,errors}));
    results.push({label,actualPdfCanvas:true,replacement:true,refresh:true,overflow,errors});await context.close();
  }
  writeFileSync('.runtime/document-browser-check.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results));
}finally{await browser.close();}
