/* Renders caption chunks to transparent PNGs with headless Chrome (perfect Arabic shaping, any font).
   node captions.js <chunks.json> <out_dir> [--style tiktok|box|yellow|brand] [--w 1080] [--brand dir]
   chunks.json: [{"id":1,"text":"...","lang":"ar|en","role":"cap|hook|step"}]
   Output: <out_dir>/cap_0001.png (full size) and cap_0001_s.png (92 % size, for a 2-frame pop). */
const fs = require('fs'), path = require('path');
const { launch, openPage, loadBrand } = require('./browser.js');
const a = process.argv.slice(2);
const opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const chunks = JSON.parse(fs.readFileSync(a[0], 'utf8')), OUT = path.resolve(a[1]);
const W = +opt('--w', 1080), styleName = opt('--style', 'tiktok');
const brand = loadBrand(opt('--brand', path.dirname(path.resolve(a[0]))));
fs.mkdirSync(OUT, { recursive: true });

const STYLES = {
  tiktok: { size: 66, weight: 800, color: '#FFFFFF', stroke: '7px #000', shadow: '0 4px 10px rgba(0,0,0,.35)', box: null, hot: brand.caption?.highlight || brand.colors?.accent },
  box: { size: 58, weight: 800, color: '#111', stroke: '0', shadow: 'none', box: '#FFF', hot: brand.colors?.accent },
  yellow: { size: 66, weight: 900, color: '#FFE14D', stroke: '9px #000', shadow: '0 4px 10px rgba(0,0,0,.4)', box: null, hot: '#FFF' },
  brand: { size: 62, weight: 800, color: brand.colors?.paper || '#F8F8F8', stroke: '0', shadow: '0 6px 18px rgba(0,0,0,.45)', box: brand.colors?.ink || '#303438', hot: brand.colors?.accent }
};
const S = STYLES[styleName] || STYLES.tiktok;
const fontFor = lang => lang === 'ar' ? (brand.fonts?.arabic || 'Cairo') : (brand.fonts?.display || 'Montserrat');

const page = `<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;background:transparent}
#box{width:${W}px;display:flex;justify-content:center;padding:24px 0}
#t{display:inline-block;max-width:${Math.round(W * .82)}px;text-align:center;line-height:1.15;font-weight:${S.weight};font-size:${S.size}px;
   color:${S.color};${S.stroke !== '0' ? `-webkit-text-stroke:${S.stroke};paint-order:stroke fill;` : ''}text-shadow:${S.shadow};
   ${S.box ? `background:${S.box};padding:10px 26px;border-radius:18px;` : ''}}
#t .hot{color:${S.hot}}
</style></head><body><div id="box"><div id="t"></div></div></body></html>`;
const htmlFile = path.join(OUT, '_cap.html'); fs.writeFileSync(htmlFile, page);

(async () => {
  const b = await launch(); const p = await openPage(b, htmlFile, { width: W, height: 600, data: {}, brand });
  for (const c of chunks) {
    const scaleRole = c.role === 'hook' ? 1.22 : 1;
    const html = (c.html || c.text.replace(/\*(.+?)\*/g, '<span class="hot">$1</span>'));
    await p.evaluate((html, font, dir, sc) => { const t = document.getElementById('t'); t.innerHTML = html; t.style.fontFamily = `"${font}",sans-serif`; t.dir = dir; t.style.transform = `scale(${sc})`; t.style.transformOrigin = 'center'; }, html, fontFor(c.lang), c.lang === 'ar' ? 'rtl' : 'ltr', scaleRole);
    const box = await p.$('#box'); const bb = await box.boundingBox();
    const clip = { x: 0, y: 0, width: W, height: Math.ceil(bb.height) };
    const base = path.join(OUT, `cap_${String(c.id).padStart(4, '0')}`);
    await p.screenshot({ path: base + '.png', omitBackground: true, clip });
    await p.evaluate(sc => { document.getElementById('t').style.transform = `scale(${sc * .92})`; }, scaleRole);
    await p.screenshot({ path: base + '_s.png', omitBackground: true, clip });
    c.h = clip.height;
  }
  await b.close();
  fs.writeFileSync(path.join(OUT, 'index.json'), JSON.stringify(chunks, null, 1));
  console.log('captions', chunks.length, 'chunks →', OUT);
})().catch(e => { console.error(e); process.exit(1); });
