import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';

const EXE = process.env.CHROME || `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome`;
const here = path.dirname(new URL(import.meta.url).pathname);
const html = process.argv[2] || 'animation.html';
const outDir = path.join(here, process.argv[3] || 'frames');
const stills = process.argv[4] ? process.argv[4].split(',').map(Number) : null;
fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });

// serve the folder over http so the canvas stays untainted
const MIME = { '.html':'text/html', '.jpg':'image/jpeg', '.png':'image/png', '.ttf':'font/ttf', '.woff2':'font/woff2' };
const server = http.createServer((req, res) => {
  const p = path.join(here, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, b) => e ? (res.writeHead(404), res.end()) : (res.writeHead(200, { 'content-type': MIME[path.extname(p)] || 'application/octet-stream' }), res.end(b)));
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const browser = await chromium.launch({ executablePath: EXE, args: ['--no-sandbox','--force-color-profile=srgb'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on('console', m => console.log('  page:', m.text()));
page.on('pageerror', e => console.log('  pageerror:', e.message));

await page.goto('http://127.0.0.1:' + port + '/' + html);
await page.evaluate(() => window.READY);
const { duration, fps } = await page.evaluate(() => window.SPEC);
const n = Math.round(duration * fps);
console.log(`capture ${n} frames @ ${fps}fps, ${duration}s`);

const t0 = Date.now();
if (stills) {
  for (const t of stills) {
    const data = await page.evaluate(t => { window.setT(t); return document.getElementById('c').toDataURL('image/jpeg', 0.95); }, t);
    fs.writeFileSync(path.join(outDir, `still-${t}.jpg`), Buffer.from(data.split(',')[1], 'base64'));
  }
  console.log(`stills: ${stills.join(', ')}`);
} else {
for (let i = 0; i < n; i++) {
  const data = await page.evaluate(t => { window.setT(t); return document.getElementById('c').toDataURL('image/jpeg', 0.95); }, i / fps);
  fs.writeFileSync(path.join(outDir, String(i).padStart(5, '0') + '.jpg'), Buffer.from(data.split(',')[1], 'base64'));
  if (i % 30 === 0) process.stdout.write(`  ${i}/${n}\r`);
}
}
console.log(`\nrendered in ${((Date.now()-t0)/1000).toFixed(1)}s`);
await browser.close();
server.close();
