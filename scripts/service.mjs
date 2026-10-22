import { spawn } from 'node:child_process';
import { readFileSync, openSync, closeSync } from 'node:fs';

// A hidden Windows supervisor owns the service tree and direct log handles.
// This descriptor contains paths/arguments only; configuration is inherited.
const launch = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const fd = openSync(launch.log, 'a');
const child = spawn(launch.command, launch.args, {
  cwd: launch.cwd, env: process.env, windowsHide: true,
  stdio: ['ignore', fd, fd],
});
closeSync(fd);
child.on('error', () => { console.error('SERVICE_START_FAILED'); process.exitCode = 1; });
child.on('exit', code => { process.exitCode = code ?? 1; });
