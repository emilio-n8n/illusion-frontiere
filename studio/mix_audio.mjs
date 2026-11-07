// Build the full audio mix: voice + one music bed per act, ducked under voice.
//
//   node studio/mix_audio.mjs
//   node studio/mix_audio.mjs --video out/film-final-voiced.mp4 --out out/film-final.mp4
//
// Reads studio/narration/index.json for block durations (already measured on
// the real voice) and films/.../script/blocks.json for the act of each block.
// Music beds: films/.../audio/music/M00..M05.wav (90-120 s, looped per act).
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = process.argv.slice(2);
const get = (name, fallback) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};

const narrationIndex = JSON.parse(fs.readFileSync(path.join(root, 'studio/narration/index.json'), 'utf8'));
const scriptBlocks = JSON.parse(fs.readFileSync(path.join(root, 'films/01-illusion-frontiere/script/blocks.json'), 'utf8'));
const actById = new Map(scriptBlocks.blocks.map(b => [b.id, b.act]));

// Order matters: 'ACTE I ' must not swallow 'ACTE II '. Trailing space does it.
const MUSIC = [
  ['PROLOGUE', 'M00'],
  ['ACTE V ', 'M05'],
  ['ACTE IV ', 'M04'],
  ['ACTE III ', 'M03'],
  ['ACTE II ', 'M02'],
  ['ACTE I ', 'M01'],
  ['FINALE', 'M05'],
];

function bedFor(act) {
  const upper = (act || '').toUpperCase();
  for (const [key, bed] of MUSIC) {
    if (upper.startsWith(key)) return bed;
  }
  return 'M00';
}

const audioDir = path.join(root, 'out/audio');
const voiceDir = path.join(root, 'films/01-illusion-frontiere/audio/blocks');
const musicDir = path.join(root, 'films/01-illusion-frontiere/audio/music');
fs.mkdirSync(audioDir, { recursive: true });

// --- 1. voice track: concatenate the 70 measured takes in order -----------
const voiceList = path.join(audioDir, 'voice-list.txt');
fs.writeFileSync(voiceList, narrationIndex.map(b => {
  const f = path.join(voiceDir, `${b.id}.wav`);
  if (!fs.existsSync(f)) throw new Error(`missing voice take ${b.id}`);
  return `file '${f.replace(/'/g, "'\\''")}'`;
}).join('\n') + '\n');

const voiceWav = path.join(audioDir, 'voice.wav');
let r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
  '-i', voiceList, '-c:a', 'pcm_s16le', voiceWav], { stdio: 'inherit' });
if (r.status !== 0) process.exit(r.status || 1);

// --- 2. music track: one looped bed per contiguous act -------------------
const groups = [];
for (const b of narrationIndex) {
  const act = actById.get(b.id) || 'PROLOGUE';
  const last = groups[groups.length - 1];
  if (last && last.act === act) last.duration += b.duration;
  else groups.push({ act, duration: b.duration });
}

const musicParts = [];
groups.forEach((g, i) => {
  const bed = bedFor(g.act);
  const src = path.join(musicDir, `${bed}.wav`);
  if (!fs.existsSync(src)) throw new Error(`missing music bed ${bed}`);
  const out = path.join(audioDir, `music-${String(i).padStart(2, '0')}.wav`);
  const fadeOut = Math.min(2.5, g.duration / 4);
  const filter = `afade=t=in:st=0:d=2,afade=t=out:st=${Math.max(0, g.duration - fadeOut).toFixed(2)}:d=${fadeOut.toFixed(2)},` +
    `aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo`;
  r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-stream_loop', '-1',
    '-i', src, '-t', g.duration.toFixed(3), '-af', filter,
    '-c:a', 'pcm_s16le', out], { stdio: 'inherit' });
  if (r.status !== 0) process.exit(r.status || 1);
  musicParts.push(out);
  console.log(`music ${bed} for ${g.act} (${g.duration.toFixed(0)}s)`);
});

const musicList = path.join(audioDir, 'music-list.txt');
fs.writeFileSync(musicList, musicParts.map(f => `file '${f.replace(/'/g, "'\\''")}'`).join('\n') + '\n');
const musicWav = path.join(audioDir, 'music.wav');
r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
  '-i', musicList, '-c:a', 'pcm_s16le', musicWav], { stdio: 'inherit' });
if (r.status !== 0) process.exit(r.status || 1);

// --- 3. mix: duck music under voice, normalise to -14 LUFS ---------------
const musicGain = get('--music-gain', '0.16');
const mixWav = path.join(audioDir, 'mix.wav');
const graph = [
  '[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[voice]',
  `[1:a]volume=${musicGain},aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[music]`,
  '[music][voice]sidechaincompress=threshold=0.04:ratio=10:attack=15:release=350[ducked]',
  '[voice][ducked]amix=inputs=2:duration=longest:weights=1 1:normalize=0[mix]',
  '[mix]aformat=sample_fmts=fltp:channel_layouts=stereo,loudnorm=I=-14:TP=-1:LRA=11[a]',
].join(';');

r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error',
  '-i', voiceWav, '-i', musicWav,
  '-filter_complex', graph, '-map', '[a]', '-c:a', 'pcm_s24le', '-ar', '48000', '-ac', '2', mixWav], { stdio: 'inherit' });
if (r.status !== 0) process.exit(r.status || 1);
console.log(`✓ mix ${path.relative(root, mixWav)}`);

// --- 4. attach to video --------------------------------------------------
const video = get('--video', 'out/film-final-voiced.mp4');
const out = get('--out', 'out/film-final.mp4');
if (video && fs.existsSync(path.join(root, video))) {
  r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error',
    '-i', path.join(root, video), '-i', mixWav,
    '-map', '0:v:0', '-map', '1:a:0',
    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
    '-movflags', '+faststart', path.join(root, out)], { stdio: 'inherit' });
  if (r.status !== 0) process.exit(r.status || 1);
  console.log(`✓ ${out}`);
}
