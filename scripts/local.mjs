import { createServer } from 'node:net';
import { spawn, spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync, mkdirSync, openSync, closeSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import {parseEnv} from 'node:util';

export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const services = JSON.parse(readFileSync(path.join(root, 'config/local-services.json'), 'utf8'));
const runtime = path.join(root, '.runtime');
const windows = process.platform === 'win32';
const python = path.join(root, '.venv', windows ? 'Scripts/python.exe' : 'bin/python');
const receiptPath = path.join(runtime, 'services.json');

export function localEnvironment(ambient, source) {
  const explicit=parseEnv(source);
  const origin=explicit.CHOREOGRAPH_ORIGIN??'http://127.0.0.1:45860';
  if(!['http://localhost:45860','http://127.0.0.1:45860'].includes(origin))throw new Error('Local origin must use the repository frontend port.');
  const inherited=Object.fromEntries(Object.entries(ambient).filter(([key])=>!/^CHOREOGRAPH_|^OPENAI_|^HUBSPOT_/i.test(key)));
  return {...inherited,...explicit,NEXT_TELEMETRY_DISABLED:'1',PYTHONUNBUFFERED:'1',CHOREOGRAPH_ORIGIN:origin};
}

export async function assertFree(port) {
  await new Promise((resolve, reject) => {
    const server = createServer();
    server.once('error', () => reject(new Error(`Port ${port} is unavailable; no process was stopped.`)));
    server.listen(port, services.host, () => server.close(resolve));
  });
}
function run(command, args, options = {}) {
  const result = spawnSync(command, args, { cwd: root, windowsHide: true, stdio: 'inherit', ...options });
  if (result.error || result.status !== 0) throw new Error('Local command failed. Inspect its fixed diagnostic.');
}
function compose(args) {
  run('docker', ['compose', '--project-name', services.project, '--env-file', '.env.local', '-f', 'compose.yaml', ...args]);
}
function readReceipts() {
  return existsSync(receiptPath) ? JSON.parse(readFileSync(receiptPath, 'utf8')) : {};
}
export function identity(pid) {
  if (!Number.isSafeInteger(pid) || pid < 1) return null;
  if (windows) {
    const result = spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command',
      `Get-CimInstance Win32_Process -Filter 'ProcessId = ${pid}' | Select-Object ProcessId,CommandLine,CreationDate | ConvertTo-Json -Compress`],
    { encoding: 'utf8', windowsHide: true });
    if (result.status !== 0) throw new Error('Process ownership could not be checked.');
    return result.stdout.trim() ? JSON.parse(result.stdout) : null;
  }
  const result = spawnSync('ps', ['-p', String(pid), '-o', 'lstart=,args='], { encoding: 'utf8' });
  return result.status === 0 ? { CommandLine: result.stdout.trim(), CreationDate: result.stdout.slice(0, 24) } : null;
}
export function owned(receipt, current) {
  return Boolean(current && current.CreationDate === receipt.identity.CreationDate &&
    current.CommandLine?.toLowerCase().includes(root.toLowerCase()) &&
    current.CommandLine === receipt.identity.CommandLine);
}
function descendants(pid) {
  if (!windows) return [];
  const script = `$items = @(Get-CimInstance Win32_Process); $ids = [System.Collections.Generic.HashSet[int]]::new(); [void]$ids.Add(${pid}); do { $changed = $false; foreach ($item in $items) { if ($ids.Contains([int]$item.ParentProcessId) -and $ids.Add([int]$item.ProcessId)) { $changed = $true } } } while ($changed); @($items | Where-Object { $_.ProcessId -ne ${pid} -and $ids.Contains([int]$_.ProcessId) } | Select-Object ProcessId,ParentProcessId,CommandLine,CreationDate) | ConvertTo-Json -Compress`;
  const result=spawnSync('powershell.exe',['-NoProfile','-NonInteractive','-Command',script],{encoding:'utf8',windowsHide:true});
  if(result.status!==0)throw new Error('Owned descendants could not be checked.');
  const parsed=result.stdout.trim()?JSON.parse(result.stdout):[];
  return Array.isArray(parsed)?parsed:[parsed];
}
async function ready(url, child) {
  for (let n = 0; n < 100; n++) {
    if (!identity(child.pid)) throw new Error('Owned service exited before readiness.');
    try { if ((await fetch(url, { signal: AbortSignal.timeout(1000) })).ok) return; } catch {}
    await new Promise(resolve => setTimeout(resolve, 400));
  }
  throw new Error('Owned service did not become ready; inspect .runtime logs.');
}
export async function launchBackground(command, args, { cwd, env, log }) {
  if (windows) {
    // Start-Process gives Windows an independent, explicitly hidden window.
    // Pass paths/arguments as data, never as interpolated PowerShell source.
    const quote = value => `"${value.replace(/(\\*)"/g, '$1$1\\"').replace(/(\\+)$/, '$1$1')}"`;
    const launchFile = `${log}.launch.json`;
    writeFileSync(launchFile, JSON.stringify({ command, args, cwd, log }));
    const argumentsString = [path.join(root, 'scripts/service.mjs'), launchFile].map(quote).join(' ');
    const script = '$launch = [Console]::In.ReadToEnd() | ConvertFrom-Json; $child = Start-Process -FilePath $launch.command -ArgumentList $launch.arguments -WindowStyle Hidden -PassThru -ErrorAction Stop; $child.Id';
    const result = spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', script], {
      env, input: JSON.stringify({ command: process.execPath, arguments: argumentsString }),
      encoding: 'utf8', windowsHide: true, timeout: 15000,
    });
    const pid = Number(result.stdout?.trim());
    if (result.error || result.status !== 0 || !Number.isSafeInteger(pid) || pid < 1) throw new Error('Hidden background launch failed.');
    return { pid };
  }
  const fd = openSync(log, 'a');
  try {
    const child = spawn(command, args, { cwd, env, detached: true, stdio: ['ignore', fd, fd] });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
    child.unref();
    return child;
  } finally { closeSync(fd); }
}
async function start(target) {
  const receipts = readReceipts();
  if (Object.entries(receipts).some(([name,r]) => (!target||name===target)&&(identity(r.pid)||(r.descendants??[]).some(item=>{const current=identity(item.ProcessId);return current&&current.CreationDate===item.CreationDate&&current.CommandLine===item.CommandLine;})))) throw new Error('Recorded services still exist. Check status before starting.');
  if(!target||target==='frontend')await assertFree(services.ports.frontend);
  if(!target||target==='api')await assertFree(services.ports.api);
  if(!target||target==='frontend')run(process.execPath,[path.join(root,'scripts/pdf-assets.mjs')]);
  mkdirSync(runtime, { recursive: true });
  const env = localEnvironment(process.env,readFileSync(path.join(root,'.env.local'),'utf8'));
  const definitions = [
    ['api', python, ['-m', 'choreograph.server'], path.join(root, 'apps/backend'), `http://127.0.0.1:${services.ports.api}/health`],
    ['runner', python, ['-m', 'choreograph.runner'], path.join(root, 'apps/backend'), null],
    ['frontend', process.execPath, [path.join(root, 'node_modules/next/dist/bin/next'), 'dev', '--hostname', services.host, '--port', String(services.ports.frontend)], path.join(root, 'apps/frontend'), `http://127.0.0.1:${services.ports.frontend}`],
  ];
  const started = {...receipts};
  const launched=[];
  try {
  for (const [name, command, args, cwd, url] of definitions) {
    if(target&&name!==target)continue;
    const instance=name==='runner'?randomUUID():null;
    const log = path.join(runtime, `${name}-${randomUUID()}.log`);
    const child = await launchBackground(command, args, { cwd, env:instance?{...env,CHOREOGRAPH_RUNNER_INSTANCE:instance}:env, log });
    const info = identity(child.pid);
    if (!info) throw new Error('Unable to record owned service identity.');
    started[name] = { pid: child.pid, identity: info, root, cwd, log, port:services.ports[name]??null, descendants:[] };
    launched.push(name);
    writeFileSync(receiptPath, JSON.stringify(started, null, 2));
    if (url) await ready(url, child);
    if(instance){
      let healthy=false;
      for(let n=0;n<100;n++){
        if(!identity(child.pid))throw new Error('Owned runner exited before readiness.');
        try{const state=JSON.parse(readFileSync(path.join(runtime,'runner-ready.json'),'utf8'));if(state.instance===instance&&state.status==='ready'&&Date.now()-Date.parse(state.at)<10000){healthy=true;break;}}catch{}
        await new Promise(resolve=>setTimeout(resolve,200));
      }
      if(!healthy)throw new Error('Owned runner did not become ready; inspect its fixed diagnostic.');
    }
    started[name].descendants=descendants(child.pid);
    writeFileSync(receiptPath, JSON.stringify(started,null,2));
  }
  } catch(error) {
    for(const name of launched.reverse())await stop(name);
    throw error;
  }
  console.log(`Choreograph is ready at ${env.CHOREOGRAPH_ORIGIN}`);
}
async function stop(target) {
  const receipts = readReceipts();
  for (const [name, receipt] of Object.entries(receipts).reverse()) {
    if(target&&name!==target)continue;
    const current = identity(receipt.pid);
    if(current&&!owned(receipt,current))throw new Error(`Ownership mismatch for ${name}; no process was stopped.`);
    const known=new Map((receipt.descendants??[]).map(item=>[item.ProcessId,item]));
    if(current)for(const item of descendants(receipt.pid))known.set(item.ProcessId,item);
    receipt.descendants=[...known.values()];writeFileSync(receiptPath,JSON.stringify(receipts,null,2));
    if(current){
      if (windows) run('taskkill.exe', ['/PID', String(receipt.pid), '/T', '/F']);
      else process.kill(-receipt.pid, 'SIGTERM');
    }
    for(const item of known.values()){
      const child=identity(item.ProcessId);if(!child)continue;
      if(child.CreationDate!==item.CreationDate||child.CommandLine!==item.CommandLine)continue;
      run('taskkill.exe',['/PID',String(item.ProcessId),'/T','/F']);
    }
    await new Promise(resolve=>setTimeout(resolve,250));
    if(identity(receipt.pid)&&owned(receipt,identity(receipt.pid)))throw new Error(`Could not verify ${name} stopped.`);
    for(const item of known.values()){const child=identity(item.ProcessId);if(child&&child.CreationDate===item.CreationDate&&child.CommandLine===item.CommandLine)throw new Error(`Owned ${name} descendant survived.`);}
    if(receipt.port)await assertFree(receipt.port);
    delete receipts[name];
    writeFileSync(receiptPath, JSON.stringify(receipts, null, 2));
  }
  mkdirSync(runtime, { recursive: true });
  writeFileSync(receiptPath, JSON.stringify(receipts));
  console.log('Owned app processes stopped. Database and volumes were preserved.');
}
async function main(action) {
  if (action === 'start') await start();
  else if (['start-api','start-frontend','start-runner'].includes(action))await start(action.slice(6));
  else if (action === 'stop') await stop();
  else if (['stop-api','stop-frontend','stop-runner'].includes(action))await stop(action.slice(5));
  else if (action === 'status') {
    for (const [name, receipt] of Object.entries(readReceipts())) console.log(name, owned(receipt, identity(receipt.pid)) ? 'running (owned)' : 'stopped or identity mismatch');
  } else if (action === 'db-up') {
    const inspect = spawnSync('docker', ['inspect', services.container, '--format', '{{.State.Running}}'], { encoding: 'utf8', windowsHide: true });
    if (inspect.status === 0 && inspect.stdout.trim() === 'true') {
      const label = spawnSync('docker', ['inspect', services.container, '--format', '{{index .Config.Labels \"com.docker.compose.project\"}}'], { encoding: 'utf8', windowsHide: true });
      if (label.status !== 0 || label.stdout.trim() !== services.project) throw new Error('Database ownership mismatch.');
    } else await assertFree(services.ports.postgres);
    compose(['up', '-d', '--wait', 'postgres']);
  } else if (action === 'db-stop') {
    const inspect = spawnSync('docker', ['inspect', services.container, '--format', '{{index .Config.Labels "com.docker.compose.project"}}'], { encoding: 'utf8', windowsHide: true });
    if (inspect.status !== 0 || inspect.stdout.trim() !== services.project) throw new Error('Database ownership was not verified.');
    compose(['stop', 'postgres']);
  } else throw new Error('Use start, stop, status, db-up or db-stop.');
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv[2]).catch(error => { console.error(error.message); process.exitCode = 1; });
}
