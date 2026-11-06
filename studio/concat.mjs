// Concatenate rendered block mp4s into the silent film master.
//
//   node studio/concat.mjs
//   node studio/concat.mjs --out out/film-silent.mp4
//   node studio/concat.mjs --audio audio/mix.wav
//
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = process.argv.slice(2);
const get = (name, fallback) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};

const dir = get('--dir', 'blocks');
const index = JSON.parse(fs.readFileSync(path.join(root, 'studio', dir, 'index.json'), 'utf8'));
const blockDir = path.resolve(root, get('--blocks', `out/${dir}`));
const out = path.resolve(root, get('--out', 'out/film-silent.mp4'));
const audio = get('--audio', '');

const files = index.map(b => path.join(blockDir, `${b.id}.mp4`));
const missing = files.filter(f => !fs.existsSync(f));
if (missing.length) {
  console.error(`missing ${missing.length} block(s):`);
  for (const f of missing) console.error('  ' + path.relative(root, f));
  process.exit(1);
}

const list = path.join(root, 'out/concat.txt');
fs.mkdirSync(path.dirname(list), { recursive: true });
fs.writeFileSync(list, files.map(f => `file '${f.replace(/'/g, "'\\''")}'`).join('\n') + '\n');

const ffArgs = ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list];
if (audio) ffArgs.push('-i', path.resolve(root, audio));
ffArgs.push('-c:v', 'copy');
if (audio) ffArgs.push('-c:a', 'aac', '-b:a', '192k', '-shortest');
ffArgs.push('-movflags', '+faststart', out);

fs.mkdirSync(path.dirname(out), { recursive: true });
const r = spawnSync('ffmpeg', ffArgs, { stdio: 'inherit' });
if (r.status !== 0) process.exit(r.status || 1);
console.log(`✓ ${out}`);
