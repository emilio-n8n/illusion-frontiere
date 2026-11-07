// Render the YouTube thumbnails (1280x720) from studio/thumbnail.html.
//
//   node studio/thumbnail.mjs
//   node studio/thumbnail.mjs --only a
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const only = process.argv.includes('--only')
  ? process.argv[process.argv.indexOf('--only') + 1]
  : '';
const outDir = path.join(root, 'out');
fs.mkdirSync(outDir, { recursive: true });

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ttf': 'font/ttf',
  '.woff2': 'font/woff2',
};
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent((req.url || '/').split('?')[0]));
  fs.readFile(p, (err, buf) => {
    if (err) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'content-type': MIME[path.extname(p)] || 'application/octet-stream' });
    res.end(buf);
  });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

function findChrome() {
  const c = [process.env.CHROME, chromium.executablePath(),
    path.join(os.homedir(), '.cache/ms-playwright/chromium-1248/chrome-linux64/chrome')].filter(Boolean);
  for (const p of c) { if (fs.existsSync(p)) return p; }
  throw new Error('no Chromium');
}

const browser = await chromium.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
const versions = only ? [only] : ['a', 'b'];
for (const v of versions) {
  await page.goto(`http://127.0.0.1:${port}/studio/thumbnail.html?v=${v}`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.READY === true || window.READY_ERROR, null, { timeout: 30000 });
  const err = await page.evaluate(() => window.READY_ERROR || null);
  if (err) throw new Error(err);
  const file = path.join(outDir, `thumbnail-${v}.jpg`);
  await page.screenshot({ path: file, type: 'jpeg', quality: 94 });
  console.log(`✓ ${file}`);
}
await browser.close();
server.close();
