# -*- coding: utf-8 -*-
# needs: faster_whisper
"""Speech → word timings with faster-whisper (runs locally, no API key).

    transcribe.py <audio_or_video> <out_words.json> [--lang auto|en|ar|...] [--model small|medium|large-v3] [--prompt "names, terms"]

Writes out_words.json = [{"w": "word", "s": start, "e": end}] and out_words.txt (plain text).
Model default: "small" for English, "medium" for Arabic and other languages (small mangles Arabic).
--prompt helps spelling of names/brands ("GoharyAI, LEXU, ChatGPT").
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import json, os, subprocess, sys, tempfile

a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
src, out = a[0], a[1]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
lang = opt("--lang", "auto"); lang = None if lang == "auto" else lang
model_name = opt("--model") or ("small" if lang == "en" else "medium")
prompt = opt("--prompt")

# 16 kHz mono wav keeps whisper fast and avoids container quirks
tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", tmp], check=True)

from faster_whisper import WhisperModel
model = WhisperModel(model_name, device="cpu", compute_type="int8")
segments, info = model.transcribe(tmp, language=lang, word_timestamps=True, vad_filter=True,
                                  vad_parameters=dict(min_silence_duration_ms=300), initial_prompt=prompt,
                                  condition_on_previous_text=False)
words = []
for seg in segments:
    for w in seg.words or []:
        t = w.word.strip()
        if not t: continue
        words.append({"w": t, "s": round(w.start, 3), "e": round(w.end, 3)})
os.unlink(tmp)
# whisper sometimes gives zero-length or overlapping words; keep times monotonic
for i, w in enumerate(words):
    if i and w["s"] < words[i - 1]["e"]: w["s"] = words[i - 1]["e"]
    if w["e"] <= w["s"]: w["e"] = round(w["s"] + 0.12, 3)
json.dump(words, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
open(os.path.splitext(out)[0] + ".txt", "w", encoding="utf-8").write(" ".join(w["w"] for w in words))
print(f"language={info.language} ({info.language_probability:.2f}) words={len(words)} dur={words[-1]['e'] if words else 0}s → {out}")
