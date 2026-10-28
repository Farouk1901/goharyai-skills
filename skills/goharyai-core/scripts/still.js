/* Renders an HTML file to one or more PNG/JPG stills (covers, thumbnails, carousel slides).
   node still.js <page.html> <out.png> [--w 1080] [--h 1350] [--data data.json] [--slides N] [--scale 2]
   With --slides N the page must define window.slide(i); files become out-1.png … out-N.png. */
const fs = require('fs'), path = require('path');
const { launch, openPage, loadBrand } = require('./browser.js');
const a = process.argv.slice(2);
const opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const html = path.resolve(a[0]), out = path.resolve(a[1]);
const W = +opt('--w', 1080), H = +opt('--h', 1350), N = +opt('--slides', 0), scale = +opt('--scale', 1);
const data = opt('--data') ? JSON.parse(fs.readFileSync(opt('--data'), 'utf8')) : {};
(async () => {
  const b = await launch(); const p = await openPage(b, html, { width: W, height: H, data, brand: loadBrand(path.dirname(html)), scale });
  const type = /\.jpe?g$/i.test(out) ? 'jpeg' : 'png';
  if (N) for (let i = 1; i <= N; i++) { await p.evaluate(i => window.slide(i), i); await p.screenshot({ path: out.replace(/(\.[^.]+)$/, `-${i}$1`), type, ...(type === 'jpeg' ? { quality: 92 } : { omitBackground: true }) }); }
  else { if (await p.evaluate(() => !!window.slide)) await p.evaluate(() => window.slide(1)); await p.screenshot({ path: out, type, ...(type === 'jpeg' ? { quality: 92 } : { omitBackground: true }) }); }
  await b.close(); console.log('still', N ? N + ' files' : out);
})().catch(e => { console.error(e); process.exit(1); });
