// Check that every image referenced by the block index exists.
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const index = JSON.parse(fs.readFileSync(path.join(root, 'studio/blocks/index.json'), 'utf8'));
let missing = 0;
for (const entry of index) {
  const block = JSON.parse(fs.readFileSync(path.join(root, 'studio/blocks', `${entry.id}.json`), 'utf8'));
  for (const shot of block.shots) {
    const file = path.join(root, shot.src.replace(/^\//, ''));
    if (!fs.existsSync(file) || fs.statSync(file).size < 20_000) {
      console.log(`missing ${entry.id}  ${shot.id}  ${shot.src}`);
      missing++;
    }
  }
}
console.log(missing ? `${missing} missing image(s)` : 'all images present');
process.exit(missing ? 1 : 0);
