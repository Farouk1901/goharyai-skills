# -*- coding: utf-8 -*-
# needs: numpy
"""Cut plan for a talking-head video: drops silences and gives you an editable sentence list.

    cutplan.py <video> <words.json> <plan.json> [--pad 0.10] [--gap 0.45] [--min 0.35]

Reads the word timings, groups words into sentences, and writes plan.json:
  {"keep": [{"id": 1, "s": 1.20, "e": 4.85, "text": "..."} ...], "removed_silence": 12.4}
Silences longer than --gap between words are cut (keeping --pad seconds on each side).
Edit plan.json by hand (delete sentences, fix the text) and pass it to cut.py.
A readable copy is written next to it as plan.txt.
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import json, os, subprocess, sys

a = sys.argv[1:]
if len(a) < 3: sys.exit(__doc__)
video, wordsf, out = a[0], a[1], a[2]
opt = lambda k, d: float(a[a.index(k) + 1]) if k in a else d
PAD, GAP, MIN = opt("--pad", 0.10), opt("--gap", 0.45), opt("--min", 0.35)
words = json.load(open(wordsf, encoding="utf-8"))
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video]).decode().strip())

# sentences: break on end punctuation or a long pause
sents, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    nxt = words[i + 1] if i + 1 < len(words) else None
    if w["w"].rstrip().endswith((".", "!", "?", "؟", "。")) or not nxt or nxt["s"] - w["e"] > 0.9:
        sents.append(cur); cur = []

keep, removed = [], 0.0
for n, s in enumerate(sents, 1):
    # inside a sentence, also split out any pause longer than GAP
    parts, blk = [], [s[0]]
    for w in s[1:]:
        if w["s"] - blk[-1]["e"] > GAP: parts.append(blk); blk = [w]
        else: blk.append(w)
    parts.append(blk)
    for p in parts:
        st, en = max(0.0, p[0]["s"] - PAD), min(dur, p[-1]["e"] + PAD)
        if en - st < MIN: continue
        keep.append({"id": len(keep) + 1, "sentence": n, "s": round(st, 3), "e": round(en, 3), "text": " ".join(w["w"] for w in p)})
total = sum(k["e"] - k["s"] for k in keep)
plan = {"source": os.path.abspath(video), "duration": round(dur, 3), "kept": round(total, 3), "removed": round(dur - total, 3), "keep": keep}
json.dump(plan, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.splitext(out)[0] + ".txt", "w", encoding="utf-8") as f:
    for k in keep: f.write(f"[{k['id']:>3}] {k['s']:7.2f}–{k['e']:7.2f}  {k['text']}\n")
print(f"source {dur:.1f}s → keep {total:.1f}s ({len(keep)} blocks, {len(sents)} sentences), removed {dur - total:.1f}s → {out}")
