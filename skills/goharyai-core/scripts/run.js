#!/usr/bin/env node
/* Runs any core script with the right interpreter.
   node run.js <script> [args...]
     script.py  → the Python that has the modules the script declares in a "# needs: a, b" header
     script.js  → node
   Reads env.json (written by env.py). Falls back to python3/python when env.json is missing. */
const fs = require('fs'), path = require('path'), { spawnSync } = require('child_process');
const HERE = __dirname;
const [script, ...args] = process.argv.slice(2);
if (!script) { console.error('usage: node run.js <script.py|script.js> [args]'); process.exit(2); }
const file = path.isAbsolute(script) ? script : path.join(HERE, script);
if (!fs.existsSync(file)) { console.error('no such script: ' + file); process.exit(2); }

let cmd;
if (file.endsWith('.js')) cmd = [process.execPath, file];
else {
  const head = fs.readFileSync(file, 'utf8').split('\n').slice(0, 15).join('\n');
  const m = head.match(/#\s*needs:\s*([^\n]+)/);
  const needs = m ? m[1].split(',').map(s => s.trim()).filter(Boolean) : [];
  let env = null;
  try { env = JSON.parse(fs.readFileSync(path.join(HERE, 'env.json'), 'utf8')); } catch (e) {}
  let py = null;
  if (env) {
    for (const [c, info] of Object.entries(env.python || {})) {
      if (needs.every(n => info[n])) { py = c.split(' '); break; }
    }
  }
  if (!py) py = [process.platform === 'win32' ? 'python' : 'python3'];
  if (needs.length && env && !Object.values(env.python || {}).some(i => needs.every(n => i[n])))
    console.error(`⚠️ no Python with [${needs.join(', ')}] found by env.py — trying ${py.join(' ')}`);
  cmd = [...py, file];
}
const r = spawnSync(cmd[0], [...cmd.slice(1), ...args], { stdio: 'inherit', env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' } });
process.exit(r.status === null ? 1 : r.status);
