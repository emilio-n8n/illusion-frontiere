// Render one block to mp4 (or a few stills) with headless Chromium + ffmpeg.
//
//   node studio/render_block.mjs --block B00 --out out/blocks/B00.mp4
//   node studio/render_block.mjs --block B00 --stills 1,4.5 --scale 0.5
//
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { parseArgs } from 'node:util';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');

const { values } = parseArgs({
  options: {
    block: { type: 'string' },
    dir: { type: 'string', default: 'blocks' },
    out: { type: 'string' },
    scale: { type: 'string', default: '1' },
    fps: { type: 'string' },
    stills: { type: 'string' },
    preset: { type: 'string', default: 'medium' },
    crf: { type: 'string', default: '18' },
  },
});

if (!values.block) {
  console.error('usage: node studio/render_block.mjs --block B00 [--out out/blocks/B00.mp4] [--stills 1,4.5] [--scale 1]');
  process.exit(2);
}

const blockId = values.block;
const scale = Math.max(0.1, Math.min(1, Number(values.scale)));
const W = Math.round(1920 * scale);
const H = Math.round(1080 * scale);

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.ttf': 'font/ttf',
  '.woff2': 'font/woff2',
  '.svg': 'image/svg+xml',
};

const server = http.createServer((req, res) => {
  const urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
  let file = urlPath === '/' ? path.join(root, 'studio/render.html') : path.join(root, urlPath);
  file = path.normalize(file);
  if (!file.startsWith(root)) {
    res.writeHead(403); res.end('forbidden'); return;
  }
  fs.readFile(file, (err, buf) => {
    if (err) { res.writeHead(404); res.end('not found'); return; }
    res.writeHead(200, { 'content-type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream' });
    res.end(buf);
  });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

function findChrome() {
  const candidates = [
    process.env.CHROME,
    chromium.executablePath(),
    path.join(os.homedir(), '.cache/ms-playwright/chromium-1248/chrome-linux64/chrome'),
  ].filter(Boolean);
  for (const p of candidates) {
    try { if (fs.existsSync(p)) return p; } catch {}
  }
  throw new Error('no Chromium found; run: npx playwright install chromium');
}

const outPath = values.out ? path.resolve(root, values.out) : path.join(root, 'out/blocks', `${blockId}.mp4`);
const stillTimes = values.stills ? values.stills.split(',').map(Number).filter(n => Number.isFinite(n)) : null;
fs.mkdirSync(path.dirname(outPath), { recursive: true });

const browser = await chromium.launch({
  executablePath: findChrome(),
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-background-timer-throttling', '--force-color-profile=srgb'],
});

let exitCode = 0;
try {
  const page = await browser.newPage({
    viewport: { width: W, height: H },
    deviceScaleFactor: 1,
  });
  page.on('console', msg => { if (msg.type() === 'error') console.error('  page:', msg.text()); });
  page.on('pageerror', err => console.error('  pageerror:', err.message));

  const url = `http://127.0.0.1:${port}/studio/render.html?block=${encodeURIComponent(blockId)}&scale=${scale}&dir=${encodeURIComponent(values.dir)}`;
  console.log(`[${blockId}] ${W}x${H} scale=${scale} — ${url}`);
  await page.goto(url, { waitUntil: 'load', timeout: 120000 });
  await page.waitForFunction(() => window.READY === true || window.READY_ERROR, null, { timeout: 180000 });
  const pageError = await page.evaluate(() => window.READY_ERROR || null);
  if (pageError) throw new Error(pageError);

  const spec = await page.evaluate(() => window.SPEC);
  const fps = values.fps ? Number(values.fps) : spec.fps;
  const duration = spec.duration;
  const n = Math.max(1, Math.round(duration * fps));
  console.log(`[${blockId}] duration ${duration.toFixed(2)}s @ ${fps}fps = ${n} frames`);

  if (stillTimes) {
    const dir = path.join(path.dirname(outPath), 'stills');
    fs.mkdirSync(dir, { recursive: true });
    for (const t of stillTimes) {
      const data = await page.evaluate(t => {
        window.setT(t);
        return document.getElementById('c').toDataURL('image/jpeg', 0.95);
      }, t);
      const file = path.join(dir, `${blockId}-${t.toFixed(2)}.jpg`);
      fs.writeFileSync(file, Buffer.from(data.slice(data.indexOf(',') + 1), 'base64'));
      console.log(`  still ${file}`);
    }
    console.log(`[${blockId}] stills done`);
  } else {
    const ff = spawn('ffmpeg', [
      '-y', '-loglevel', 'error',
      '-f', 'image2pipe', '-vcodec', 'mjpeg', '-framerate', String(fps), '-i', '-',
      '-c:v', 'libx264', '-preset', values.preset, '-crf', values.crf,
      '-pix_fmt', 'yuv420p', '-movflags', '+faststart', outPath,
    ], { stdio: ['pipe', 'ignore', 'pipe'] });

    let ffErr = '';
    ff.stderr.on('data', d => { ffErr = (ffErr + d).slice(-2000); });
    const ffDone = new Promise((res, rej) => {
      ff.on('close', code => code === 0 ? res() : rej(new Error(`ffmpeg exited ${code}: ${ffErr}`)));
      ff.on('error', rej);
    });

    const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      const t = i / fps;
      const data = await page.evaluate(t => {
        window.setT(t);
        return document.getElementById('c').toDataURL('image/jpeg', 0.92);
      }, t);
      const buf = Buffer.from(data.slice(data.indexOf(',') + 1), 'base64');
      if (!ff.stdin.write(buf)) {
        await new Promise(r => ff.stdin.once('drain', r));
      }
      if (i % 12 === 0 || i === n - 1) {
        const done = i + 1;
        const rate = done / ((Date.now() - t0) / 1000);
        const eta = Math.max(0, (n - done) / Math.max(rate, .01));
        process.stdout.write(`  ${done}/${n}  ${rate.toFixed(1)} fps  ETA ${Math.floor(eta / 60)}:${String(Math.round(eta % 60)).padStart(2, '0')}\r`);
      }
    }
    ff.stdin.end();
    await ffDone;
    const secs = (Date.now() - t0) / 1000;
    const mb = (fs.statSync(outPath).size / 1024 / 1024).toFixed(1);
    console.log(`\n[${blockId}] done in ${secs.toFixed(0)}s — ${outPath} (${mb} MB)`);
  }
} catch (err) {
  console.error(`[${blockId}] FAILED: ${err.stack || err}`);
  exitCode = 1;
} finally {
  await browser.close().catch(() => {});
  server.close();
}
process.exit(exitCode);
