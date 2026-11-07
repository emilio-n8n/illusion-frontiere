// Fetch missing Blender batch chunks, skipping complete ones.
//
//   node tools/fetch_chunks.mjs <run-id> [parallel=4]
//
// Expected chunks come from blender/depth_batch.json (6 chunks per shot,
// as dispatched). A chunk dir is complete when its frame count matches
// end-start+1; incomplete dirs are deleted and re-fetched.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const runId = process.argv[2];
const parallel = Math.max(1, Number(process.argv[3] || 4));
if (!runId) {
  console.error('usage: node tools/fetch_chunks.mjs <run-id> [parallel]');
  process.exit(2);
}

const PER_SHOT = 6;
const batch = JSON.parse(fs.readFileSync(path.join(root, 'blender/depth_batch.json'), 'utf8'));
const jobs = [];
for (const b of batch) {
  const size = Math.ceil(b.frames / PER_SHOT);
  let s = 1, c = 0;
  while (s <= b.frames) {
    const e = Math.min(b.frames, s + size - 1);
    const name = `blender-batch-${b.shot}-chunk-${c}`;
    const dir = path.join(root, 'out/blender/chunks', name);
    let have = 0;
    if (fs.existsSync(dir)) {
      have = fs.readdirSync(dir).filter(f => /^frame-\d+\.png$/.test(f)).length;
    }
    const want = e - s + 1;
    if (have === want) {
      // complete, skip
    } else {
      if (fs.existsSync(dir)) {
        fs.rmSync(dir, { recursive: true, force: true });
      }
      jobs.push(name);
    }
    s = e + 1;
    c++;
  }
}

console.log(`${jobs.length} chunk(s) to fetch (${batch.length} shots)`);
if (!jobs.length) process.exit(0);

let failed = 0;
const queue = [...jobs];
async function worker() {
  while (queue.length) {
    const name = queue.shift();
    const r = spawnSync('gh', ['run', 'download', String(runId), '-n', name,
      '-D', path.join(root, 'out/blender/chunks', name)], { stdio: 'pipe' });
    if (r.status !== 0) {
      console.error(`FAIL ${name}: ${r.stderr.toString().slice(-200)}`);
      failed++;
    } else {
      console.log(`ok ${name} (${queue.length} left)`);
    }
  }
}
await Promise.all(Array.from({ length: Math.min(parallel, queue.length) }, worker));
console.log(failed ? `${failed} failed` : 'all chunks fetched');
process.exit(failed ? 1 : 0);
