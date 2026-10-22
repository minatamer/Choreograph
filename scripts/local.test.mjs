import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:net';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { assertFree, identity, owned, root, localEnvironment } from './local.mjs';

test('local app configuration is explicit and displays the OAuth origin',()=>{
  const env=localEnvironment({PATH:'retained',CHOREOGRAPH_PROFILE:'live',OPENAI_API_KEY:'ambient',HUBSPOT_CLIENT_ID:'ambient'},'CHOREOGRAPH_PROFILE=fake\nCHOREOGRAPH_ORIGIN=http://localhost:45860\n');
  assert.equal(env.PATH,'retained');assert.equal(env.CHOREOGRAPH_PROFILE,'fake');
  assert.equal(env.OPENAI_API_KEY,undefined);assert.equal(env.HUBSPOT_CLIENT_ID,undefined);
  assert.equal(env.CHOREOGRAPH_ORIGIN,'http://localhost:45860');
  assert.throws(()=>localEnvironment({},'CHOREOGRAPH_ORIGIN=https://elsewhere.example'),/Local origin/);
});

test('an unrelated listener is refused and remains reachable', async () => {
  const server = createServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try { await assert.rejects(assertFree(server.address().port), /unavailable/); assert.equal(server.listening, true); }
  finally { await new Promise(resolve => server.close(resolve)); }
});
test('PID reuse and a sibling command never pass ownership checks', () => {
  const identity = { CreationDate: 'first', CommandLine: `${root}/.venv/python choreograph.server` };
  assert.equal(owned({ identity }, identity), true);
  assert.equal(owned({ identity }, { ...identity, CreationDate: 'second' }), false);
  assert.equal(owned({ identity }, { ...identity, CommandLine: 'another repository' }), false);
});

test('Windows service survives its launcher without a visible window', { skip: process.platform !== 'win32' }, async () => {
  const directory = mkdtempSync(path.join(tmpdir(), 'choreograph hidden '));
  const log = path.join(directory, 'probe with spaces.log');
  const probe = 'console.log("ready"); const timer=setInterval(()=>console.log("alive"),100); setTimeout(()=>clearInterval(timer),8000);';
  const source = `import {launchBackground} from ${JSON.stringify(new URL('./local.mjs', import.meta.url).href)}; const child=await launchBackground(process.execPath, ['-e', ${JSON.stringify(probe)}], {cwd:${JSON.stringify(root)},env:process.env,log:${JSON.stringify(log)}}); console.log(child.pid);`;
  let receipt;
  try {
    const launcher = spawnSync(process.execPath, ['--input-type=module', '-e', source], { cwd: root, encoding: 'utf8', windowsHide: true, timeout: 20000 });
    assert.equal(launcher.status, 0, 'background launcher must return successfully');
    const pid = Number(launcher.stdout.trim());
    assert.ok(Number.isSafeInteger(pid) && pid > 0);
    receipt = { pid, identity: identity(pid) };
    assert.ok(owned(receipt, receipt.identity));
    await new Promise(resolve => setTimeout(resolve, 600));
    assert.ok(owned(receipt, identity(pid)), 'service must survive launcher exit');
    assert.match(readFileSync(log, 'utf8'), /ready[\s\S]*alive/);
    const window = spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', `(Get-Process -Id ${pid}).MainWindowHandle.ToInt64()`], { encoding: 'utf8', windowsHide: true });
    assert.equal(window.status, 0);
    assert.equal(window.stdout.trim(), '0', 'background supervisor must have no visible window');
  } finally {
    if (receipt && owned(receipt, identity(receipt.pid))) {
      const cleanup = spawnSync('taskkill.exe', ['/PID', String(receipt.pid), '/T', '/F'], { windowsHide: true, encoding: 'utf8' });
      assert.equal(cleanup.status, 0);
    }
    assert.equal(path.dirname(path.resolve(directory)), path.resolve(tmpdir()));
    assert.ok(path.basename(directory).startsWith('choreograph hidden '));
    rmSync(directory, { recursive: true, force: true });
  }
});
