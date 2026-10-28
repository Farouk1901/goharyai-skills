# -*- coding: utf-8 -*-
# needs: numpy, soundfile
"""Synthesised sound effects placed on a timeline, no sample files needed.

    sfx.py <events.json> <out.wav> --dur 30
    events.json: [{"t": 1.2, "kind": "whoosh", "gain": 0.8}, {"t": 2.0, "kind": "pop"}, ...]

Kinds: whoosh (transition), thud (impact/hit), pop (card appears), tick (counter step), chime (success),
       key (keystroke), paper (card slide), riser (build-up, 1.5 s before a reveal).
Mix the result with mix.py --sfx.  Keep it sparse: one effect per visual event, never on every word.
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import json, sys, numpy as np, soundfile as sf

a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
events = json.load(open(a[0], encoding="utf-8")); OUT = a[1]
DUR = float(a[a.index("--dur") + 1]) if "--dur" in a else max(e["t"] for e in events) + 2
SR = 48000; N = int(DUR * SR); buf = np.zeros(N); rng = np.random.RandomState(5)

def lpf(x, k):
    y = np.empty_like(x); z = 0.0
    for i in range(len(x)): z += k * (x[i] - z); y[i] = z
    return y
norm = lambda x: x / (np.abs(x).max() + 1e-9)
def env(L, atk, dec): tt = np.arange(L) / SR; return np.minimum(1, tt / atk) * np.exp(-tt / dec)

def whoosh(d=.32):
    L = int(d * SR); tt = np.arange(L) / SR; x = rng.randn(L); y = np.empty(L); z = 0.0
    for i in range(L): k = .02 + .25 * np.sin(np.pi * i / L) ** 2; z += k * (x[i] - z); y[i] = z
    return norm(y) * np.sin(np.pi * tt / d) ** 1.5
def thud(f0=150, f1=50, d=.35):
    L = int(d * SR); tt = np.arange(L) / SR; f = f0 * np.exp(np.log(f1 / f0) * tt / d)
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / .09) + lpf(rng.randn(L), .3) * np.exp(-tt / .01) * .5)
def pop(f=900, d=.07):
    L = int(d * SR); tt = np.arange(L) / SR; fr = f * np.exp(-tt * 18)
    return norm(np.sin(2 * np.pi * np.cumsum(fr + 200) / SR) * env(L, .002, .025))
def tick(d=.03): L = int(d * SR); return norm(lpf(rng.randn(L), .5) * env(L, .0005, .004))
def chime(f=1320, d=.5):
    L = int(d * SR); tt = np.arange(L) / SR
    return norm((np.sin(2 * np.pi * f * tt) + .5 * np.sin(2 * np.pi * f * 1.5 * tt) * (tt > .07)) * env(L, .003, .16))
def key(): L = int(.04 * SR); return norm(lpf(rng.randn(L), .6) * env(L, .0005, .006))
def paper(d=.18):
    L = int(d * SR); return norm(lpf(rng.randn(L), .45) * np.sin(np.pi * np.arange(L) / L) * (1 + .6 * np.sin(np.arange(L) / SR * 2 * np.pi * 37)))
def riser(d=1.5):
    L = int(d * SR); tt = np.linspace(0, 1, L); x = rng.randn(L); y = np.empty(L); z = 0.0
    for i in range(L): z += (.01 + .4 * tt[i] ** 2) * (x[i] - z); y[i] = z
    return norm(y) * tt ** 2.2
KINDS = {"whoosh": whoosh, "thud": thud, "pop": pop, "tick": tick, "chime": chime, "key": key, "paper": paper, "riser": riser}
GAIN = {"whoosh": .55, "thud": .8, "pop": .45, "tick": .35, "chime": .5, "key": .3, "paper": .4, "riser": .5}
for e in events:
    k = e.get("kind", "pop")
    if k not in KINDS: print("unknown kind", k); continue
    sig = KINDS[k]() * GAIN[k] * float(e.get("gain", 1))
    t0 = e["t"] - (1.5 if k == "riser" else 0)
    i = max(0, int(t0 * SR)); j = min(N, i + len(sig)); buf[i:j] += sig[:j - i]
buf = np.clip(buf, -1, 1)
sf.write(OUT, np.stack([buf, buf], 1).astype(np.float32), SR)
print(f"sfx {len(events)} events, {DUR:.1f}s → {OUT}")
