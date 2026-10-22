// Renders the animation frame by frame in headless Chromium and muxes it with
// the soundtrack into prize-call.mp4 (1920x1080, 30 fps, 16:9).
//
//   node animations/prize-call/tools/render.mjs              # full video
//   node animations/prize-call/tools/render.mjs --stills 3,14.6,36 out/   # test frames
//
// Needs Playwright (with Chromium) and ffmpeg.
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { join, dirname, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')); }

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.m4a': 'audio/mp4' };
const server = createServer(async (req, res) => {
  try {
    const p = join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    if (!p.startsWith(ROOT)) throw new Error('outside');
    const body = await readFile(p.endsWith('/') ? join(p, 'index.html') : p);
    res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }).end(body);
  } catch { res.writeHead(404).end(); }
}).listen(0);
const url = `http://127.0.0.1:${server.address().port}/index.html`;

const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
});
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
page.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
page.on('pageerror', e => console.error('page error:', e.message));
await page.goto(url);
await page.waitForFunction(() => window.frameAt, null, { timeout: 120000 });
const grab = async t => Buffer.from((await page.evaluate(t => window.frameAt(t), t)).split(',')[1], 'base64');

const args = process.argv.slice(2);
if (args[0] === '--stills') {
  const dir = args[2] || 'stills';
  await mkdir(dir, { recursive: true });
  for (const t of args[1].split(',').map(Number)) {
    await writeFile(join(dir, `t${t.toFixed(2)}.jpg`), await grab(t));
    console.log('still', t);
  }
} else {
  const FPS = 30;
  const duration = await page.evaluate(() => window.DURATION);
  const frames = Math.round(duration * FPS);
  const out = join(ROOT, 'prize-call.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-i', join(ROOT, 'soundtrack.m4a'), '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '22',
    '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-shortest', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < frames; i++) {
    const buf = await grab(i / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) console.log(`frame ${i}/${frames}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log('wrote', out);
}
await browser.close();
server.close();
