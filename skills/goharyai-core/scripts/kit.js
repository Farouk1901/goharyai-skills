/* kit.js — browser-side toolkit injected into every compose.html by browser.js.
   A page defines scenes with K.scene({a, b, html, upd}); window.draw(t) builds the active scene once
   and updates it every frame. Word timings come from data.words via window.init(data): K.wt('word', n).
   Everything is deterministic in t (seconds), so frames can be rendered in any order and in parallel. */
(function () {
  const K = window.K = {};
  const B = window.BRAND || {};
  K.brand = B; K.C = (B.colors || {}); K.F = (B.fonts || {});
  K.D = {}; K.W = [];

  /* math */
  K.cl = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  K.pr = (t, a, b) => K.cl((t - a) / (b - a));
  K.lerp = (a, b, k) => a + (b - a) * k;
  K.eo = x => 1 - Math.pow(1 - x, 3);
  K.ei = x => x * x * x;
  K.eio = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  K.back = x => { const c1 = 1.7, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
  K.nz = (t, s = 0) => Math.sin(t * 1.3 + s) * .5 + Math.sin(t * 2.7 + s * 1.7) * .3 + Math.sin(t * 5.1 + s * .3) * .2;
  K.fmt = n => Number(n).toLocaleString('en-US');

  /* words */
  const norm = s => (s || '').toLowerCase().replace(/[^\p{L}\p{N}']/gu, '');
  K.norm = norm;
  K.wt = (w, n = 1, end = false) => { let k = 0; for (const x of K.W) { if (norm(x.w) === norm(w)) { k++; if (k === n) return end ? x.e : x.s; } } console.log('MISSING word ' + w + ' #' + n); return 0; };
  K.wi = (w, n = 1) => { let k = 0; for (let i = 0; i < K.W.length; i++) if (norm(K.W[i].w) === norm(w)) { k++; if (k === n) return i; } return -1; };
  K.type = (s, u, a, cps = 28) => s.slice(0, Math.floor(K.cl((u - a) * cps, 0, s.length)));
  K.count = (v, u, a, d = 1) => Math.round(v * K.eo(K.pr(u, a, a + d)));

  /* element motion helpers: each one sets opacity + transform from a progress value */
  K.T = (el, s) => { el.style.transform = s; };
  K.pop = (el, t, a, d = .35, extra = '') => { const k = K.pr(t, a, a + d); el.style.opacity = k > 0 ? 1 : 0; K.T(el, extra + ' scale(' + K.back(k) + ')'); };
  K.fade = (el, t, a, d = .3, ty = 18, extra = '') => { const k = K.eo(K.pr(t, a, a + d)); el.style.opacity = k; K.T(el, extra + ' translateY(' + ((1 - k) * ty) + 'px)'); };
  K.fadeOut = (el, t, a, d = .3) => { const k = K.pr(t, a, a + d); if (k > 0) el.style.opacity = Math.min(parseFloat(el.style.opacity || 1), 1 - k); };
  K.flipIn = (el, t, a, d = .55) => { const k = K.eio(K.pr(t, a, a + d)); el.style.opacity = Math.min(1, K.pr(t, a, a + d * .45)); K.T(el, `perspective(1800px) rotateY(${(1 - k) * -70}deg) scale(${K.lerp(.82, 1, k)})`); el.style.filter = `blur(${(1 - k) * 4}px)`; };
  K.zoomIn = (el, t, a, d = .3) => { const k = K.eo(K.pr(t, a, a + d)); el.style.opacity = k; K.T(el, `scale(${K.lerp(1.35, 1, k)})`); el.style.filter = `blur(${(1 - k) * 10}px)`; };
  K.blurOut = (el, t, a, d = .3) => { const k = K.pr(t, a, a + d); if (k > 0) { el.style.opacity = 1 - k; el.style.filter = `blur(${k * 12}px)`; K.T(el, `scale(${1 + k * .2})`); } };
  K.slideIn = (el, t, a, d = .4, dx = 80) => { const k = K.eo(K.pr(t, a, a + d)); el.style.opacity = k; K.T(el, `translateX(${(1 - k) * dx}px)`); };
  K.drift = (el, t, ax = 6, ay = 4, s = 0) => { K.T(el, `translate(${K.nz(t, s) * ax}px,${K.nz(t * .8, s + 2) * ay}px)`); };

  /* caption chunks: up to N words, break on punctuation, pauses and before short function words */
  const STOP = new Set(['the', 'a', 'an', 'to', 'of', 'and', 'or', 'it', 'is', 'as', 'if', 'in', 'for', 'you', 'your', 'that', 'this', 'by', 'on', 'but', 'i', 'are', 'its', 'my', 'و', 'في', 'من', 'على', 'عن', 'إلى', 'أو', 'ده', 'دي']);
  K.chunks = (max = 3) => { if (K._ch) return K._ch; const C = []; let cur = []; K.W.forEach((w, i) => { const nx = K.W[i + 1]; cur.push(w); const brk = /[.,!?،؟]$/.test(w.w) || cur.length >= max || (nx && nx.s - w.e > .25) || (nx && cur.length >= 2 && STOP.has(norm(nx.w))); if (brk || !nx) { C.push(cur); cur = []; } }); return K._ch = C; };
  K.capAt = t => { let ch = null; for (const c of K.chunks()) if (t >= c[0].s - .05 && t < c[c.length - 1].e + .2) ch = c; return ch; };
  K.disp = w => w.replace(/[.,!?،؟]$/, '');
  /* draws the active chunk into #cap with a per-word pop and the brand accent on "hot" words */
  K.caption = (t, { el = document.getElementById('cap'), hot = [] } = {}) => {
    if (!el) return; const c = K.capAt(t);
    if (!c) { el.style.display = 'none'; return; }
    el.style.display = 'block';
    el.dir = /[؀-ۿ]/.test(c.map(w => w.w).join(' ')) ? 'rtl' : 'ltr';     // Arabic chunks read right-to-left
    el.innerHTML = c.map(w => { const k = K.eo(K.pr(t, w.s - .05, w.s + .14)); if (k <= 0) return ''; const isHot = hot.some(h => norm(w.w).startsWith(norm(h))); return `<span class="${isHot ? 'hot' : ''}" style="opacity:${k};display:inline-block;transform:translateY(${(1 - k) * 10}px) scale(${K.lerp(.9, 1, k)})">${K.disp(w.w)}</span>`; }).join(' ');
  };

  /* svg icons that need no files */
  K.icon = {
    check: (c = '#fff', s = 64) => `<svg width="${s}" height="${s}" viewBox="0 0 100 100" fill="none" stroke="${c}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"><path d="M18 54 L40 76 L84 28"/></svg>`,
    arrow: (c = '#fff', s = 64) => `<svg width="${s}" height="${s}" viewBox="0 0 100 100" fill="none" stroke="${c}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"><path d="M14 50 H82 M56 24 L84 50 L56 76"/></svg>`,
    star: (c = '#fff', s = 64, w = 11) => `<svg width="${s}" height="${s}" viewBox="0 0 100 100"><g stroke="${c}" stroke-width="${w}" stroke-linecap="round">${Array.from({ length: 12 }, (_, k) => { const a = k * Math.PI / 6, r2 = k % 2 ? 40 : 46; return `<line x1="${50 + Math.cos(a) * 12}" y1="${50 + Math.sin(a) * 12}" x2="${50 + Math.cos(a) * r2}" y2="${50 + Math.sin(a) * r2}"/>`; }).join('')}</g></svg>`,
    play: (c = '#fff', s = 64) => `<svg width="${s}" height="${s}" viewBox="0 0 100 100"><path d="M30 18 L80 50 L30 82 Z" fill="${c}"/></svg>`,
    bolt: (c = '#fff', s = 64) => `<svg width="${s}" height="${s}" viewBox="0 0 100 100"><path d="M56 6 L22 56 H48 L42 94 L78 42 H52 Z" fill="${c}"/></svg>`,
    tri: (c = '#E40000', s = 40) => `<svg width="${s}" height="${s}" viewBox="0 0 100 100"><path d="M50 10 L92 90 H8 Z" fill="${c}"/></svg>`
  };
  K.logo = (theme = 'dark', h = 56) => { const src = (B.logo || {})[theme === 'dark' ? 'on_dark' : 'on_light']; return src ? `<img src="${src}" style="height:${h}px;width:auto;display:block">` : `<span style="font:800 ${h * .6}px ${K.F.latin || 'Inter'},sans-serif">${B.name || ''}</span>`; };

  /* scenes */
  K.S = []; K.scene = o => { K.S.push(o); return o; };
  let cur = null;
  window.init = async function (data) { K.D = data || {}; K.W = (data && data.words) || []; K._ch = null; if (K.onInit) await K.onInit(data); await document.fonts.ready; };
  window.draw = async function (t) {
    const root = document.getElementById('scene') || document.body;
    const sc = K.S.find(s => t >= s.a() && t < s.b()) || K.S[K.S.length - 1];
    if (sc && cur !== sc) { cur = sc; root.innerHTML = sc.html(); await Promise.all([...root.querySelectorAll('img')].map(i => i.decode ? i.decode().catch(() => { }) : 0)); }
    if (sc && sc.upd) sc.upd(t, t - sc.a(), root);
    if (K.after) K.after(t, sc);
  };
})();
