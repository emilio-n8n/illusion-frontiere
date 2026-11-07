// Mux rendered narration blocks with their measured voice takes.
//
//   node studio/mux_voice.mjs
//   node studio/mux_voice.mjs --only N001,N002
//   node studio/mux_voice.mjs --dir narration --out-dir voiced
//
// For each block: video out/<dir>/<id>.mp4 + voice films/.../audio/blocks/<id>.wav
// -> out/voiced/<id>.mp4 (video copied, audio as AAC, padded or trimmed to the
// video duration). Blocks without a measured take are skipped.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = process.argv.slice(2);
const get = (name, fallback) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};
const dir = get('--dir', 'narration');
const outDirName = get('--out-dir', 'voiced');
const only = get('--only', '')
  .split(',')
  .map(s => s.trim())
  .filter(Boolean);

const index = JSON.parse(fs.readFileSync(path.join(root, 'studio', dir, 'index.json'), 'utf8'));
const entries = only.length ? index.filter(b => only.includes(b.id)) : index;
if (!entries.length) {
  console.error('no blocks selected');
  process.exit(1);
}

fs.mkdirSync(path.join(root, 'out', outDirName), { recursive: true });
let ok = 0, skipped = 0, failed = 0;

for (const entry of entries) {
  const video = path.join(root, 'out', dir, `${entry.id}.mp4`);
  const voice = path.join(root, 'films/01-illusion-frontiere/audio/blocks', `${entry.id}.wav`);
  const out = path.join(root, 'out', outDirName, `${entry.id}.mp4`);
  if (!fs.existsSync(video)) {
    console.log(`skip ${entry.id}: no video ${path.relative(root, video)}`);
    skipped++;
    continue;
  }
  if (!fs.existsSync(voice) || fs.statSync(voice).size < 2000) {
    console.log(`skip ${entry.id}: no voice take`);
    skipped++;
    continue;
  }
  const r = spawnSync('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-i', video,
    '-i', voice,
    '-map', '0:v:0', '-map', '1:a:0',
    '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '1',
    '-af', 'aresample=async=1',
    '-shortest',
    '-movflags', '+faststart',
    out,
  ], { stdio: 'inherit' });
  if (r.status !== 0) {
    console.error(`${entry.id} FAILED`);
    failed++;
  } else {
    ok++;
  }
}

console.log(`mux: ${ok} ok, ${skipped} skipped, ${failed} failed`);

// Copy the narration index so `node studio/concat.mjs --dir voiced` works.
if (ok) {
  const voicedIndex = entries
    .filter(b => fs.existsSync(path.join(root, 'out', outDirName, `${b.id}.mp4`)))
    .map(b => ({ id: b.id, title: b.title, duration: b.duration, shots: b.shots }));
  fs.mkdirSync(path.join(root, 'studio', outDirName), { recursive: true });
  fs.writeFileSync(
    path.join(root, 'studio', outDirName, 'index.json'),
    JSON.stringify(voicedIndex, null, 2) + '\n',
  );
}
process.exit(failed ? 1 : 0);
