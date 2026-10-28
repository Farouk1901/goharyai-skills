# -*- coding: utf-8 -*-
"""Environment check for the GoharyAI skills. Run once, then after any install.

    python env.py            # prints a ✅/❌ table and writes env.json next to this file
    python env.py --quiet    # only writes env.json

env.json records which Python has which package (kokoro, faster_whisper, rembg, numpy, PIL)
so run.js can pick the right interpreter per script. Nothing is installed here.
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
QUIET = "--quiet" in sys.argv
NEEDS = ["numpy", "soundfile", "PIL", "faster_whisper", "kokoro", "rembg"]

def candidates():
    """Every Python we can find: the py launcher versions on Windows, python3/python on PATH, this one."""
    out = []
    if os.name == "nt" and shutil.which("py"):
        r = subprocess.run(["py", "--list"], capture_output=True, text=True)
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.startswith("-V:") or line.startswith("-"):
                tag = line.split()[0].replace("-V:", "-")
                out.append(["py", tag])
    for name in ("python3", "python"):
        if shutil.which(name): out.append([name])
    out.append([sys.executable])
    seen, uniq = set(), []
    for c in out:
        k = " ".join(c)
        if k not in seen: seen.add(k); uniq.append(c)
    return uniq

def probe(cmd):
    code = "import json,sys\nr={'version':sys.version.split()[0],'exe':sys.executable}\n" + \
           "for m in %r:\n    try:\n        __import__(m); r[m]=True\n    except Exception:\n        r[m]=False\nprint(json.dumps(r))" % NEEDS
    try:
        r = subprocess.run(cmd + ["-c", code], capture_output=True, text=True, timeout=120)
        return json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else None
    except Exception:
        return None

def find_chrome():
    env = os.environ.get("CHROME_PATH")
    if env and os.path.exists(env): return env
    pf, pf86, la = os.environ.get("PROGRAMFILES", r"C:\Program Files"), os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), os.environ.get("LOCALAPPDATA", "")
    cands = {
        "win32": [pf + r"\Google\Chrome\Application\chrome.exe", pf86 + r"\Google\Chrome\Application\chrome.exe",
                  la + r"\Google\Chrome\Application\chrome.exe", pf86 + r"\Microsoft\Edge\Application\msedge.exe",
                  pf + r"\Microsoft\Edge\Application\msedge.exe", pf + r"\BraveSoftware\Brave-Browser\Application\brave.exe"],
        "darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium",
                   "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"],
    }.get(sys.platform, ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser", "/snap/bin/chromium", "/usr/bin/microsoft-edge"])
    return next((c for c in cands if c and os.path.exists(c)), None)

def version(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return (r.stdout or r.stderr).strip().splitlines()[0][:60]
    except Exception:
        return None

env = {"ffmpeg": version(["ffmpeg", "-version"]), "ffprobe": version(["ffprobe", "-version"]),
       "node": version(["node", "-v"]), "chrome": find_chrome(),
       "puppeteer": os.path.exists(os.path.join(HERE, "..", "node_modules", "puppeteer-core")),
       "python": {}}
for cmd in candidates():
    info = probe(cmd)
    if info: env["python"][" ".join(cmd)] = info

def pick(module):
    for cmd, info in env["python"].items():
        if info.get(module): return cmd
    return None
env["python_for"] = {m: pick(m) for m in NEEDS}

with open(os.path.join(HERE, "env.json"), "w", encoding="utf-8") as f:
    json.dump(env, f, ensure_ascii=False, indent=1)

if not QUIET:
    ok = lambda v: "✅" if v else "❌"
    print(f"{ok(env['ffmpeg'])} ffmpeg   {env['ffmpeg'] or 'missing — install from ffmpeg.org (needed for everything)'}")
    print(f"{ok(env['node'])} node     {env['node'] or 'missing — install from nodejs.org'}")
    print(f"{ok(env['chrome'])} chrome   {env['chrome'] or 'missing — install Chrome/Edge/Brave or set CHROME_PATH'}")
    print(f"{ok(env['puppeteer'])} puppeteer-core {'' if env['puppeteer'] else '— run: npm install  (inside goharyai-core)'}")
    for m in NEEDS:
        p = env["python_for"][m]
        hint = {"faster_whisper": "pip install faster-whisper   (speech → word timings)",
                "kokoro": "pip install kokoro soundfile   (English voice-over; needs Python 3.10–3.12)",
                "rembg": "pip install rembg onnxruntime   (cut people out of backgrounds; optional)",
                "numpy": "pip install numpy", "soundfile": "pip install soundfile", "PIL": "pip install pillow"}[m]
        print(f"{ok(p)} {m:<14} {p or hint}")
    print("\nenv.json written. Optional items (kokoro, rembg) only matter for the skills that use them.")
