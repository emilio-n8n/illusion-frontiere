import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const index = JSON.parse(fs.readFileSync(path.join(root, 'studio/blocks/index.json'), 'utf8'));
const ids = index.map(b => b.id);
const arg = process.argv[2];
if (arg === '--full') {
  console.log(JSON.stringify(index, null, 2));
} else {
  console.log(JSON.stringify(ids));
}
