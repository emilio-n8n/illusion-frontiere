// Build one block JSON per storyboard block from films/.../storyboard/shots.json.
// A block is the unit that gets rendered, cached and concatenated.
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const manifestPath = path.join(root, 'films/01-illusion-frontiere/storyboard/shots.json');
const outDir = path.join(root, 'studio/blocks');
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

const titles = {
  B00: 'Prologue — Le meuble',
  B01: 'Apprendre',
  B02: 'Mémoire',
  B03: 'Le corps',
  B04: 'Émotion',
  B05: 'Conscience',
  B06: 'La frontière',
};

const order = ['B00', 'B01', 'B02', 'B03', 'B04', 'B05', 'B06'];
const groups = new Map(order.map(id => [id, []]));
for (const shot of manifest.shots) {
  if (!groups.has(shot.block)) groups.set(shot.block, []);
  groups.get(shot.block).push(shot);
}

fs.mkdirSync(outDir, { recursive: true });
const index = [];

for (const id of [...groups.keys()].sort()) {
  const shots = groups.get(id);
  if (!shots.length) continue;
  const duration = shots.reduce((sum, s) => sum + Number(s.duration || 0), 0);
  const block = {
    id,
    title: titles[id] || id,
    fps: manifest.fps || 24,
    width: manifest.width || 1920,
    height: manifest.height || 1080,
    fadeIn: id === 'B00' ? 1.2 : 0.35,
    fadeOut: id === 'B06' ? 1.4 : 0.35,
    duration: Number(duration.toFixed(3)),
    shots: shots.map((s, i) => ({
      id: s.id,
      src: `/assets/generated/${s.id}.png`,
      duration: Number(s.duration),
      camera: s.camera || 'static',
      overlay: s.overlay || '',
      overlayPos: s.overlayPos || 'left',
      stamp: s.overlay === 'CONSCIENT : PRÉSUMÉ',
      transition: i === 0 ? 'cut' : 'cut',
      seed: s.seed || 0,
      title: s.title,
    })),
  };
  fs.writeFileSync(path.join(outDir, `${id}.json`), JSON.stringify(block, null, 2) + '\n');
  index.push({ id, title: block.title, duration: block.duration, shots: block.shots.length });
}

fs.writeFileSync(path.join(outDir, 'index.json'), JSON.stringify(index, null, 2) + '\n');
for (const entry of index) {
  console.log(`${entry.id}  ${entry.duration.toFixed(1)}s  ${entry.shots} shots  ${entry.title}`);
}
console.log(`total ${index.reduce((s, e) => s + e.duration, 0).toFixed(1)}s`);
