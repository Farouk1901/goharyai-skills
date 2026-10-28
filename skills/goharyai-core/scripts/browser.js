/* Headless Chrome helpers shared by render.js, still.js and captions.js.
   Finds Chrome/Edge/Brave on Windows, macOS and Linux (CHROME_PATH wins), loads local fonts,
   and opens a page at an exact pixel size with the brand kit injected as window.BRAND. */
const fs = require('fs'), path = require('path'), os = require('os'), url = require('url');
const CORE = path.resolve(__dirname, '..');

function findChrome() {
  const env = process.env.CHROME_PATH;
  if (env && fs.existsSync(env)) return env;
  const PF = process.env.PROGRAMFILES || 'C:\\Program Files', PF86 = process.env['PROGRAMFILES(X86)'] || 'C:\\Program Files (x86)', LA = process.env.LOCALAPPDATA || '';
  const cands = {
    win32: [path.join(PF, 'Google/Chrome/Application/chrome.exe'), path.join(PF86, 'Google/Chrome/Application/chrome.exe'),
      path.join(LA, 'Google/Chrome/Application/chrome.exe'), path.join(PF86, 'Microsoft/Edge/Application/msedge.exe'),
      path.join(PF, 'Microsoft/Edge/Application/msedge.exe'), path.join(PF, 'BraveSoftware/Brave-Browser/Application/brave.exe')],
    darwin: ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'],
    linux: ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/snap/bin/chromium', '/usr/bin/microsoft-edge']
  }[process.platform] || [];
  for (const c of cands) if (fs.existsSync(c)) return c;
  throw new Error('No Chrome/Edge/Brave found. Install one or set CHROME_PATH.');
}

function puppeteer() {
  for (const p of [process.env.PUPPETEER_PATH, path.join(CORE, 'node_modules/puppeteer-core'), 'puppeteer-core', 'puppeteer']) {
    if (!p) continue;
    try { return require(p); } catch (e) {}
  }
  throw new Error('puppeteer-core missing — run "npm install" inside goharyai-core');
}

async function launch() {
  return puppeteer().launch({
    executablePath: findChrome(), headless: 'new',
    args: ['--no-sandbox', '--allow-file-access-from-files', '--font-render-hinting=none', '--force-color-profile=srgb',
      '--disable-gpu-vsync', '--disable-dev-shm-usage', '--hide-scrollbars']
  });
}

/* CSS that registers every font in assets/fonts under its family name, so pages work offline. */
function fontCss() {
  const dir = path.join(CORE, 'assets/fonts');
  const fam = { 'Cairo-VF': 'Cairo', 'Inter-VF': 'Inter', 'Montserrat-VariableFont_wght': 'Montserrat', 'IBMPlexSansArabic-Bold': 'IBM Plex Sans Arabic',
    'IBMPlexSansArabic-Regular': 'IBM Plex Sans Arabic', 'Tajawal-Bold': 'Tajawal', 'NotoKufiArabic-VF': 'Noto Kufi Arabic', 'ReadexPro-VF': 'Readex Pro' };
  return fs.readdirSync(dir).filter(f => /\.(ttf|otf|woff2?)$/i.test(f)).map(f => {
    const base = f.replace(/\.[^.]+$/, ''), family = fam[base] || base.replace(/[-_].*/, '');
    const weight = /Bold/i.test(base) ? '700' : /Regular/i.test(base) ? '400' : '100 900';
    return `@font-face{font-family:"${family}";src:url("${url.pathToFileURL(path.join(dir, f)).href}");font-weight:${weight};font-display:block}`;
  }).join('\n');
}

function loadBrand(projectDir) {
  const own = projectDir && path.join(projectDir, 'brand.json');
  const file = own && fs.existsSync(own) ? own : path.join(CORE, 'brand.json');
  const b = JSON.parse(fs.readFileSync(file, 'utf8'));
  const root = path.dirname(file) === CORE ? CORE : path.dirname(file);
  for (const k of Object.keys(b.logo || {})) {
    const p = path.isAbsolute(b.logo[k]) ? b.logo[k] : path.join(root, b.logo[k]);
    b.logo[k] = fs.existsSync(p) ? url.pathToFileURL(p).href : (fs.existsSync(path.join(CORE, b.logo[k])) ? url.pathToFileURL(path.join(CORE, b.logo[k])).href : '');
  }
  return b;
}

/* Opens an HTML file at W×H, injects fonts + brand + kit.js, waits for fonts and images, then calls window.init(data). */
async function openPage(browser, htmlFile, { width = 1080, height = 1920, data = null, brand = null, scale = 1 } = {}) {
  const p = await browser.newPage();
  p.on('pageerror', e => console.log('PAGEERR', e.message));
  p.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
  await p.setViewport({ width, height, deviceScaleFactor: scale });
  await p.setCacheEnabled(false);
  /* brand + kit.js exist before the page's own scripts run, so compose.html can call K.scene() inline */
  await p.evaluateOnNewDocument((b, css) => { window.BRAND = b; window.__FONT_CSS = css; }, brand || loadBrand(path.dirname(htmlFile)), fontCss());
  await p.evaluateOnNewDocument(fs.readFileSync(path.join(__dirname, 'kit.js'), 'utf8'));
  await p.goto(url.pathToFileURL(htmlFile).href, { waitUntil: 'networkidle0', timeout: 90000 });
  await p.addStyleTag({ content: fontCss() });
  await p.evaluate(() => Promise.all(['Cairo', 'Inter', 'Montserrat'].map(f => document.fonts.load('700 40px "' + f + '"').catch(() => 0))).then(() => document.fonts.ready));
  await p.evaluate(() => Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; }))));
  if (typeof data !== 'undefined') await p.evaluate(d => window.init ? window.init(d) : 0, data);
  return p;
}

module.exports = { findChrome, launch, openPage, fontCss, loadBrand, CORE };
