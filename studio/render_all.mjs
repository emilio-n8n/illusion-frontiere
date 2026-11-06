// Render every block whose images are present, then optionally concatenate.
//
//   node studio/render_all.mjs --scale 0.5 --parallel 3 --concat
//
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = process.argv.slice(2);
const get = (name, fallback) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};
const has = name => args.includes(name);

const dir = get('--dir', 'blocks');
const scale = get('--scale', '1');
const preset = get('--preset', 'medium');
const crf = get('--crf', '18');
const parallel = Math.max(1, Number(get('--parallel', '3')));
const force = has('--force');

const index = JSON.parse(fs.readFileSync(path.join(root, 'studio', dir, 'index.json'), 'utf8'));
const ready = [];
for (const entry of index) {
  const block = JSON.parse(fs.readFileSync(path.join(root, 'studio', dir, `${entry.id}.json`), 'utf8'));
  const imagesOk = block.shots.every(s => {
    const file = path.join(root, s.src.replace(/^\//, ''));
    return fs.existsSync(file) && fs.statSync(file).size > 20_000;
  });
  if (!imagesOk) {
    console.log(`skip ${entry.id}: images missing`);
    continue;
  }
  const out = path.join(root, 'out', dir, `${entry.id}.mp4`);
  if (fs.existsSync(out) && !force) {
    console.log(`skip ${entry.id}: already rendered (use --force)`);
    continue;
  }
  ready.push(entry.id);
}

console.log(`${ready.length} block(s) to render: ${ready.join(', ')}`);

function render(id) {
  return new Promise((resolve, reject) => {
    const p = spawn(process.execPath, [
      path.join(root, 'studio/render_block.mjs'),
      '--block', id,
      '--dir', dir,
      '--out', `out/${dir}/${id}.mp4`,
      '--scale', scale,
      '--preset', preset,
      '--crf', crf,
    ], { stdio: 'inherit', env: process.env });
    p.on('close', code => code === 0 ? resolve() : reject(new Error(`${id} failed (${code})`)));
  });
}

const queue = [...ready];
const workers = Array.from({ length: Math.min(parallel, queue.length) }, async () => {
  while (queue.length) {
    const id = queue.shift();
    await render(id);
  }
});

try {
  await Promise.all(workers);
} catch (err) {
  console.error(err.message);
  process.exit(1);
}

if (has('--concat')) {
  const p = spawn(process.execPath, [path.join(root, 'studio/concat.mjs')], { stdio: 'inherit' });
  await new Promise((res, rej) => p.on('close', code => code === 0 ? res() : rej(new Error(`concat failed (${code})`))));
}
