import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import ts from 'typescript';

const forbidden=new Set(['alert','confirm','prompt']),globals=new Set(['window','globalThis','self']);
function nativeReferences(sources){
 const options={noLib:true,noResolve:true,allowJs:true,jsx:ts.JsxEmit.Preserve,target:ts.ScriptTarget.ES2022};
 const host=ts.createCompilerHost(options);
 host.getSourceFile=(name,version)=>sources.has(name)?ts.createSourceFile(name,sources.get(name),version,true):undefined;
 host.fileExists=name=>sources.has(name);host.readFile=name=>sources.get(name);
 const program=ts.createProgram([...sources.keys()],options,host),checker=program.getTypeChecker(),violations=[];
 for(const file of program.getSourceFiles()){
  const report=node=>violations.push(`${file.fileName}:${file.getLineAndCharacterOfPosition(node.getStart()).line+1}`);
  const browser=node=>node&&ts.isIdentifier(node)&&globals.has(node.text);
  function visit(node){
   if(ts.isPropertyAccessExpression(node)&&browser(node.expression)&&forbidden.has(node.name.text))report(node);
   if(ts.isElementAccessExpression(node)&&browser(node.expression)&&node.argumentExpression&&ts.isStringLiteralLike(node.argumentExpression)&&forbidden.has(node.argumentExpression.text))report(node);
   if(ts.isCallExpression(node)&&ts.isIdentifier(node.expression)&&forbidden.has(node.expression.text)&&!checker.getSymbolAtLocation(node.expression))report(node);
   if(ts.isVariableDeclaration(node)&&node.initializer&&browser(node.initializer)&&ts.isObjectBindingPattern(node.name)){
    for(const element of node.name.elements)if(forbidden.has((element.propertyName??element.name).getText(file).replaceAll(/['"]/g,'')))report(element);
   }
   ts.forEachChild(node,visit);
  }
  visit(file);
 }
 return violations;
}
function files(root){
 return readdirSync(root,{withFileTypes:true}).flatMap(entry=>{
  if(['generated','pdfjs','pdfjs-dist','node_modules','.next'].includes(entry.name))return [];
  const target=path.join(root,entry.name);
  return entry.isDirectory()?files(target):/\.(?:tsx?|jsx?|mjs)$/.test(entry.name)&&!entry.name.endsWith('.d.ts')?[target]:[];
 });
}

test('all authored website source uses app-owned UI instead of browser native prompts',()=>{
 const root=fileURLToPath(new URL('../apps/frontend/',import.meta.url));
 const sources=new Map(['app','components','lib','public'].flatMap(name=>files(path.join(root,name))).map(file=>[file,readFileSync(file,'utf8')]));
 assert.ok(sources.size>50);assert.deepEqual(nativeReferences(sources),[],'Use ConfirmationDialog for confirmations and designed inline feedback for alerts.');
});

test('the native prompt guard catches direct, computed, aliased and bare globals without flagging local handlers or ARIA alerts',()=>{
 for(const source of ['window.confirm("Reset?")','window["prompt"]("Name")','globalThis.alert("Failed")','self.confirm("Sure?")','confirm("Reset?")','const ask=window.confirm; ask("Reset?")','const {confirm:ask}=window; ask("Reset?")']){
  assert.ok(nativeReferences(new Map([['/fixture.tsx',source]])).length>0,source);
 }
 assert.deepEqual(nativeReferences(new Map([['/fixture.tsx','export {}; function confirm(){return true;} confirm(); const view=<p role="alert">Confirm your choice</p>;']])),[]);
});
