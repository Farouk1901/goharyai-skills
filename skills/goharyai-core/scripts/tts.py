# -*- coding: utf-8 -*-
# needs: kokoro, soundfile, numpy
"""English voice-over with word timings, fully offline (Kokoro-82M).

    tts.py <script.txt> <out.wav> [--voice am_michael] [--speed 1.05]

Writes out.wav (24 kHz) and <out>.words.json with the exact word timings of the synthesis,
so motion scenes can be timed to words without a second transcription.
One paragraph per line; a blank line adds a short pause. Voices: am_michael, am_adam, am_fenrir, af_heart, af_bella, bf_emma, bm_george.
Arabic: Kokoro has no Arabic voice. Record the voice elsewhere (your own voice, ElevenLabs, etc.),
then run transcribe.py on it to get the word timings.
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import json, os, sys
import numpy as np, soundfile as sf

a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
src, out = a[0], a[1]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
voice, speed = opt("--voice", "am_michael"), float(opt("--speed", 1.05))
text = open(src, encoding="utf-8").read().strip()
if any("؀" <= ch <= "ۿ" for ch in text):
    sys.exit("Arabic text: Kokoro cannot voice it. Record the line elsewhere and use transcribe.py for timings.")

from kokoro import KPipeline
SR = 24000
pipe = KPipeline(lang_code="a" if voice.startswith(("a", "af", "am")) else "b")
audio, words, off = [], [], 0.0
for r in pipe(text, voice=voice, speed=speed, split_pattern=r"\n+"):
    arr = np.asarray(r.audio); audio.append(arr)
    cur = None
    for tk in (r.tokens or []):
        if tk.start_ts is None: continue
        t = tk.text
        if cur and not cur["_sp"]:                       # punctuation glued to the previous word
            cur["w"] += t; cur["e"] = round(off + (tk.end_ts or tk.start_ts), 3)
        elif t.strip() and any(ch.isalnum() for ch in t):
            cur = {"w": t, "s": round(off + tk.start_ts, 3), "e": round(off + (tk.end_ts or tk.start_ts), 3), "_sp": bool(tk.whitespace)}
            words.append(cur); continue
        elif cur:
            cur["w"] += t
        if cur: cur["_sp"] = bool(tk.whitespace)
    gap = np.zeros(int(0.12 * SR)); audio.append(gap)
    off += (len(arr) + len(gap)) / SR
for w in words: w.pop("_sp", None)
sf.write(out, np.concatenate(audio), SR)
wj = os.path.splitext(out)[0] + ".words.json"
json.dump(words, open(wj, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(f"voice={voice} dur={off:.2f}s words={len(words)} → {out}, {wj}")
