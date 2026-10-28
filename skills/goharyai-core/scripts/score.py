# -*- coding: utf-8 -*-
# needs: numpy, soundfile
"""Original background music composed in code, different for every video (no library loops, no licensing).

    score.py <out.wav> <duration> [--bpm 108] [--key Dm] [--cuts "5,9,19"] [--mood drive|calm|dark] [--seed 7]

Strings pad + bass + pulse ostinato, hits on every cut time, a rise toward the end and a soft tail.
Change key/bpm/seed per video so two videos never share a track. Mix it with mix.py (ducked under the voice).
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import sys, numpy as np, soundfile as sf

a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
OUT, DUR = a[0], float(a[1])
opt = lambda k, d: a[a.index(k) + 1] if k in a else d
BPM, KEY, MOOD, SEED = float(opt("--bpm", 108)), opt("--key", "Dm"), opt("--mood", "drive"), int(opt("--seed", 7))
CUTS = [float(x) for x in opt("--cuts", "").split(",") if x.strip()]
SR = 44100; N = int(DUR * SR); t = np.arange(N) / SR
rng = np.random.RandomState(SEED)
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
root, minor = NOTE[KEY.rstrip("m")], KEY.endswith("m")
hz = lambda semi, octv=3: 440 * 2 ** ((root + semi + 12 * (octv - 4) - 9) / 12)
PROG = [[0, 3, 7], [-4, 0, 3], [3, 7, 10], [-2, 2, 5]] if minor else [[0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]]
if MOOD == "dark": PROG = [[0, 3, 7], [-2, 1, 5], [0, 3, 7], [-4, -1, 3]]
beat = 60 / BPM; bar = beat * 4

def lp(x, k):
    y = np.empty_like(x); z = 0.0
    for i in range(len(x)): z += k * (x[i] - z); y[i] = z
    return y
def env(L, atk, rel):
    tt = np.arange(L) / SR; return np.minimum(1, tt / atk) * np.minimum(1, (L / SR - tt) / rel)

pts = [0] + sorted(CUTS) + [DUR]
inten = np.interp(t, pts, np.linspace(.35, 1.0, len(pts)) ** 1.3) * np.clip((DUR - t) / 2.2, 0, 1) ** .7
if MOOD == "calm": inten *= .6
mix = np.zeros(N)
# 1) harmonic pad: three slightly detuned saws per note, low-passed
for b in range(int(DUR / bar) + 2):
    ch = PROG[b % 4]; a0 = int(b * bar * SR); a1 = min(N, int((b + 1) * bar * SR) + int(.6 * SR))
    if a0 >= N: break
    L = a1 - a0; tt = np.arange(L) / SR
    seg = np.zeros(L)
    for semi in ch:
        for det in (-.4, 0, .4):
            f = hz(semi, 3) * 2 ** (det / 1200)
            seg += (2 * ((f * tt) % 1) - 1) * .18
    mix[a0:a1] += lp(seg, .05) * env(L, .35, .5)
# 2) bass: root every beat, octave below
for b in range(int(DUR / beat) + 1):
    a0 = int(b * beat * SR); L = int(beat * .9 * SR); a1 = min(N, a0 + L)
    if a0 >= N: break
    semi = PROG[(b // 4) % 4][0]; tt = np.arange(a1 - a0) / SR
    mix[a0:a1] += np.sin(2 * np.pi * hz(semi, 2) * tt) * np.exp(-tt / (beat * .6)) * .5
# 3) pulse: 8th-note plucks, denser as intensity grows
if MOOD != "calm":
    for k in range(int(DUR / (beat / 2)) + 1):
        a0 = int(k * beat / 2 * SR)
        if a0 >= N: break
        if rng.rand() > .55 + .4 * inten[a0]: continue
        semi = PROG[(k // 8) % 4][rng.randint(3)]; L = int(.18 * SR); a1 = min(N, a0 + L); tt = np.arange(a1 - a0) / SR
        mix[a0:a1] += np.sin(2 * np.pi * hz(semi, 4) * tt) * np.exp(-tt / .06) * .22
# 4) hits on cuts: low thud + noise burst
for c in CUTS:
    a0 = int(c * SR); L = int(.5 * SR); a1 = min(N, a0 + L)
    if a0 >= N: continue
    tt = np.arange(a1 - a0) / SR; f = 140 * np.exp(-tt * 9)
    mix[a0:a1] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / .18) * .9 + lp(rng.randn(a1 - a0), .25) * np.exp(-tt / .04) * .35
# 5) riser into the last 2.5 s before each cut (subtle) and before the end
for c in CUTS + [DUR - .3]:
    a1 = min(N, int(c * SR)); a0 = max(0, a1 - int(1.8 * SR))
    if a1 <= a0: continue
    tt = np.linspace(0, 1, a1 - a0); x = rng.randn(a1 - a0); y = np.empty_like(x); z = 0.0
    for i in range(len(x)): z += (.02 + .3 * tt[i]) * (x[i] - z); y[i] = z      # filter opens as the riser builds
    mix[a0:a1] += y * tt ** 2 * .35
mix *= inten
mix = mix / (np.abs(mix).max() + 1e-9) * .8
sf.write(OUT, mix.astype(np.float32), SR)
print(f"score {DUR:.1f}s {KEY} {BPM:.0f}bpm {MOOD} cuts={len(CUTS)} → {OUT}")
