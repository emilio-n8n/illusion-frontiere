// Build one render block per narration block (N001...N070).
//
// This is the silent animatic layer: exact narration text as subtitles, the
// suggested shots split across the block duration. When the voice is measured,
// re-run tools/measure_audio.py then this script: the durations follow the voice.
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const blocksPath = path.join(root, 'films/01-illusion-frontiere/script/blocks.json');
const shotsPath = path.join(root, 'films/01-illusion-frontiere/storyboard/shots.json');
const outDir = path.join(root, 'studio/narration');

const data = JSON.parse(fs.readFileSync(blocksPath, 'utf8'));
const storyboard = JSON.parse(fs.readFileSync(shotsPath, 'utf8'));
const shotMap = new Map(storyboard.shots.map(s => [s.id, s]));

function weights(n) {
  if (n <= 1) return [1];
  if (n === 2) return [.55, .45];
  return [.45, .3, .25];
}

fs.mkdirSync(outDir, { recursive: true });
const index = [];

// A rendered 2.5D travelling clip wins over the still image when present.
// Note: the clip plays from 0 for the allocated duration; if the allocation
// exceeds the clip, the tail freezes (re-time after measure_audio.py).
function shotSrc(id) {
  const clip = path.join(root, 'out/blender/shots', `${id}.mp4`);
  if (fs.existsSync(clip) && fs.statSync(clip).size > 50_000) {
    return `/out/blender/shots/${id}.mp4`;
  }
  return `/assets/generated/${id}.png`;
}

for (const block of data.blocks) {
  const ids = (block.suggestedShots && block.suggestedShots.length ? block.suggestedShots : ['B00-S01'])
    .filter(id => shotMap.has(id));
  const w = weights(ids.length);
  let allocated = 0;
  const shots = ids.map((id, i) => {
    const src = shotMap.get(id);
    const last = i === ids.length - 1;
    const duration = last
      ? Math.max(.5, block.seconds - allocated)
      : Math.max(.5, Math.round(block.seconds * w[i] * 1000) / 1000);
    allocated += duration;
    return {
      id,
      src: shotSrc(id),
      duration: Math.round(duration * 1000) / 1000,
      camera: src.camera || 'static',
      overlay: '',
      overlayPos: 'left',
      transition: 'cut',
      seed: src.seed || 0,
      title: src.title,
    };
  });

  const json = {
    id: block.id,
    title: block.act,
    fps: 24,
    width: 1920,
    height: 1080,
    fadeIn: .18,
    fadeOut: .18,
    duration: Math.round(block.seconds * 1000) / 1000,
    subtitle: block.text,
    shots,
  };
  fs.writeFileSync(path.join(outDir, `${block.id}.json`), JSON.stringify(json, null, 2) + '\n');
  index.push({
    id: block.id,
    title: block.act,
    duration: json.duration,
    shots: shots.length,
    audio: block.audio || null,
    measured: !!block.measured,
  });
}

fs.writeFileSync(path.join(outDir, 'index.json'), JSON.stringify(index, null, 2) + '\n');
const total = index.reduce((s, b) => s + b.duration, 0);
console.log(`${index.length} narration blocks, ${(total / 60).toFixed(2)} min`);
