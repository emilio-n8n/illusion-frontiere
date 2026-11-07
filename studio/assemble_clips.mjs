// Assemble downloaded Blender batch chunks into one graded mp4 per shot.
//
//   node studio/assemble_clips.mjs
//
// Expects out/blender/chunks/blender-batch-<shot>-chunk-<n>/frame-####.png
// Writes out/blender/shots/<shot>.mp4 (same grade as the rest of the film).
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const batch = JSON.parse(fs.readFileSync(path.join(root, 'blender/depth_batch.json'), 'utf8'));
const chunksDir = path.join(root, 'out/blender/chunks');
const shotsDir = path.join(root, 'out/blender/shots');
const framesRoot = path.join(root, 'out/blender/frames');

fs.mkdirSync(shotsDir, { recursive: true });
fs.mkdirSync(framesRoot, { recursive: true });

const GRADE = [
  'split[a][b]',
  '[b]gblur=sigma=10[b]',
  '[a][b]blend=screen,eq=saturation=0.85:contrast=1.06,vignette=PI/4,' +
  'colorbalance=bs=0.10:bm=0.04,noise=alls=8:allf=t',
].join(';');

// Clips are raw media: the engine (studio/render.html) owns the grade, grain
// and vignette so a clip and a still in the same block match exactly.
// --grade bakes the look into the clip instead (standalone delivery only).
const useGrade = process.argv.includes('--grade');

let ok = 0;
for (const b of batch) {
  const shot = b.shot;
  const frameDir = path.join(framesRoot, shot);
  fs.rmSync(frameDir, { recursive: true, force: true });
  fs.mkdirSync(frameDir, { recursive: true });

  const chunkDirs = fs.readdirSync(chunksDir)
    .filter(d => d.startsWith(`blender-batch-${shot}-chunk-`))
    .sort((x, y) => Number(x.split('-').pop()) - Number(y.split('-').pop()));
  if (!chunkDirs.length) {
    console.log(`skip ${shot}: no chunks`);
    continue;
  }
  let n = 0;
  for (const dir of chunkDirs) {
    for (const f of fs.readdirSync(path.join(chunksDir, dir)).filter(f => /^frame-\d+\.png$/.test(f)).sort()) {
      fs.copyFileSync(path.join(chunksDir, dir, f), path.join(frameDir, f));
      n++;
    }
  }
  if (n !== b.frames) {
    console.log(`WARN ${shot}: ${n}/${b.frames} frames`);
    continue;
  }
  const out = path.join(shotsDir, `${shot}.mp4`);
  const r = spawnSync('ffmpeg', [
    '-y', '-loglevel', 'error', '-framerate', '24',
    '-i', path.join(frameDir, 'frame-%04d.png'),
    ...(useGrade ? ['-vf', GRADE] : []),
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out,
  ], { stdio: 'inherit' });
  if (r.status !== 0) {
    console.log(`FAIL ${shot}`);
    continue;
  }
  console.log(`ok ${shot} (${n} frames, ${(fs.statSync(out).size / 1024 / 1024).toFixed(1)} MB)`);
  ok++;
}
console.log(`${ok}/${batch.length} clips assembled`);
