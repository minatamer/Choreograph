import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {root} from './local.mjs';
const commands = [
  [path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'), ['scripts/export_openapi.py']],
  [process.execPath, ['node_modules/openapi-typescript/bin/cli.js', 'apps/frontend/lib/generated/openapi.json', '-o', 'apps/frontend/lib/generated/api.d.ts']],
];
for (const [command,args] of commands) {
  const result = spawnSync(command,args,{cwd:root,windowsHide:true,stdio:'inherit'});
  if (result.status !== 0) process.exit(result.status ?? 1);
}
