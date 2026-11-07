// Check that every asset referenced by the block index exists (PNG or clip).
import fs from 'node:fs';
import path from 'node:path';

const dir = process.argv[2] || 'blocks';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const index = JSON.parse(fs.readFileSync(path.join(root, 'studio', dir, 'index.json'), 'utf8'));
let missing = 0;
for (const entry of index) {
  const block = JSON.parse(fs.readFileSync(path.join(root, 'studio', dir, `${entry.id}.json`), 'utf8'));
  for (const shot of block.shots) {
    const file = path.join(root, shot.src.replace(/^\//, ''));
    const minSize = /\.mp4$/i.test(shot.src) ? 50_000 : 20_000;
    if (!fs.existsSync(file) || fs.statSync(file).size < minSize) {
      console.log(`missing ${entry.id}  ${shot.id}  ${shot.src}`);
      missing++;
    }
  }
}
console.log(missing ? `${missing} missing asset(s)` : 'all assets present');
process.exit(missing ? 1 : 0);
