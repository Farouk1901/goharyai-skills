/* Renders a compose.html scene page to frames and (optionally) an mp4.
   node render.js <dir> preview 2 5 9                 → <dir>/prev/t2.00.jpg … (look before rendering all)
   node render.js <dir> all [--out video.mp4]         → <dir>/frames/00000.jpg … then ffmpeg → mp4 (30 fps)
   node render.js <dir> all --png --range 3.2,6.0     → transparent PNG frames for that time window only
                                                        (overlays for real footage; compose with overlay.py)
   <dir> holds compose.html and data.json ({words:[{w,s,e}], dur?, w?, h?, fps?, ...anything the page needs}).
   Duration = data.dur, else last word end + 1.3 s.  JOBS=2 parallel pages; RESUME=1 skips existing frames. */
const fs = require('fs'), path = require('path'), { spawnSync } = require('child_process');
const { launch, openPage, loadBrand } = require('./browser.js');
const D = path.resolve(process.argv[2] || '.'), mode = process.argv[3] || 'preview';
const argv = process.argv.slice(4);
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const OUT = opt('--out') ? path.resolve(opt('--out')) : null, PNG = argv.includes('--png');
const data = JSON.parse(fs.readFileSync(path.join(D, 'data.json'), 'utf8'));
const W = data.w || 1080, H = data.h || 1920, FPS = data.fps || 30;
const words = data.words || [];
const DUR = data.dur || (words.length ? words[words.length - 1].e + 1.3 : 5);
const range = opt('--range') ? opt('--range').split(',').map(Number) : [0, DUR];
range[1] = Math.min(range[1], DUR); range[0] = Math.max(0, Math.min(range[0], range[1]));   // never render past the data duration
const JOBS = +process.env.JOBS || 2;
const html = path.join(D, 'compose.html');
const brand = loadBrand(D);

(async () => {
  if (mode === 'preview') {
    const ts = argv.filter(a => /^\d+(\.\d+)?$/.test(a)).map(Number);
    if (!ts.length) { console.error('give timestamps: render.js <dir> preview 1 2.5 4'); process.exit(2); }
    const b = await launch(); const p = await openPage(b, html, { width: W, height: H, data, brand });
    fs.mkdirSync(path.join(D, 'prev'), { recursive: true });
    for (const t of ts) { await p.evaluate(t => window.draw(t), t); await p.screenshot({ path: path.join(D, 'prev', `t${t.toFixed(2)}.${PNG ? 'png' : 'jpg'}`), type: PNG ? 'png' : 'jpeg', ...(PNG ? { omitBackground: true } : { quality: 88 }) }); }
    await b.close(); console.log('preview', ts.length, 'frames in', path.join(D, 'prev')); return;
  }
  const F = path.join(D, 'frames'); fs.mkdirSync(F, { recursive: true });
  const i0 = Math.round(range[0] * FPS), i1 = Math.round(range[1] * FPS);
  let next = i0, done = 0; const n = i1 - i0, t0 = Date.now(), ext = PNG ? '.png' : '.jpg';
  const worker = async () => {
    const b = await launch(); const p = await openPage(b, html, { width: W, height: H, data, brand });
    while (next < i1) {
      const i = next++; const f = path.join(F, String(i).padStart(5, '0') + ext);
      if (process.env.RESUME && fs.existsSync(f)) { done++; continue; }
      await p.evaluate(t => window.draw(t), i / FPS);
      await p.screenshot({ path: f, type: PNG ? 'png' : 'jpeg', ...(PNG ? { omitBackground: true } : { quality: 92 }) });
      if (++done % 150 === 0) console.log(`${done}/${n}`);
    }
    await b.close();
  };
  await Promise.all(Array.from({ length: JOBS }, worker));
  console.log('frames', n, `(${range[0]}s→${range[1].toFixed(2)}s)`, 'in', ((Date.now() - t0) / 1000).toFixed(0) + 's');
  fs.writeFileSync(path.join(D, 'frames.json'), JSON.stringify({ fps: FPS, start: i0, end: i1, png: PNG, w: W, h: H }));
  if (OUT && !PNG) {
    const r = spawnSync('ffmpeg', ['-y', '-v', 'error', '-framerate', String(FPS), '-start_number', String(i0), '-i', path.join(F, '%05d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-movflags', '+faststart', OUT], { stdio: 'inherit' });
    if (r.status !== 0) process.exit(r.status); console.log('video', OUT);
  }
})().catch(e => { console.error(e); process.exit(1); });
