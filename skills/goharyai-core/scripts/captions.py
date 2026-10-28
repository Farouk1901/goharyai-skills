# -*- coding: utf-8 -*-
"""Word-timed captions: chunk → render PNGs (captions.js) → burn into the video with a per-chunk pop.

    captions.py chunk <words.json> <chunks.json> [--max 3] [--lang auto|ar|en] [--hot "word1,word2"]
    captions.py burn  <video> <chunks.json> <png_dir> <out.mp4> [--y 0.68] [--fps 30]

Typical:  chunk → node captions.js chunks.json caps/ --style tiktok → burn.
Chunk rules: ≤ max words, break on punctuation, pauses > 0.25 s and before short function words.
Edit chunks.json freely before rendering (fix spelling, mark *hot* words with asterisks).
--y is the caption centre as a fraction of frame height (0.74 = under the face, above the lower-third band).
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import json, os, re, subprocess, sys

a = sys.argv[1:]
if len(a) < 3: sys.exit(__doc__)
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
STOP = {"the", "a", "an", "to", "of", "and", "or", "it", "is", "as", "if", "in", "for", "you", "your", "that", "this", "by", "on", "but", "i", "are", "its", "my",
        "و", "في", "من", "على", "عن", "إلى", "أو", "ده", "دي", "اللي", "يا"}
is_ar = lambda s: any("؀" <= ch <= "ۿ" for ch in s)

if a[0] == "chunk":
    words = json.load(open(a[1], encoding="utf-8"))
    MAX = int(opt("--max", 3)); lang = opt("--lang", "auto")
    hot = [h.strip().lower() for h in opt("--hot", "").split(",") if h.strip()]
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w); nxt = words[i + 1] if i + 1 < len(words) else None
        brk = re.search(r"[.,!?،؟]$", w["w"]) or len(cur) >= MAX or (nxt and nxt["s"] - w["e"] > 0.25) \
              or (nxt and len(cur) >= 2 and nxt["w"].lower().strip(".,!?") in STOP)
        if brk or not nxt:
            text = " ".join(re.sub(r"[.,!?،؟]$", "", x["w"]) for x in cur)
            if hot: text = " ".join(f"*{t}*" if t.lower().strip("*") in hot else t for t in text.split())
            l = lang if lang != "auto" else ("ar" if is_ar(text) else "en")
            chunks.append({"id": len(chunks) + 1, "text": text, "lang": l, "role": "cap", "s": cur[0]["s"], "e": cur[-1]["e"]})
            cur = []
    # hold each chunk until the next one starts (no flicker), at most 1.2 s after its last word
    for c in chunks: c["s"] = round(max(0, c["s"] - 0.05), 3)
    for i, c in enumerate(chunks):
        c["e"] = round(min(chunks[i + 1]["s"] if i + 1 < len(chunks) else c["e"] + 1.0, c["e"] + 1.2), 3)
    json.dump(chunks, open(a[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(chunks)} chunks → {a[2]}")

elif a[0] == "burn":
    video, chunksf, pngdir, out = a[1], a[2], a[3], a[4]
    Y, FPS = float(opt("--y", 0.74)), int(opt("--fps", 30))
    chunks = json.load(open(os.path.join(pngdir, "index.json"), encoding="utf-8")) if os.path.exists(os.path.join(pngdir, "index.json")) else json.load(open(chunksf, encoding="utf-8"))
    timing = {c["id"]: c for c in json.load(open(chunksf, encoding="utf-8"))}
    W, H = map(int, subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", video]).decode().strip().split(",")[:2])
    inputs, filt, last = ["-i", video], [], "[0:v]"
    POP = 2 / FPS
    n = 0
    for c in chunks:
        t = timing.get(c["id"], c); s, e = t["s"], t["e"]
        base = os.path.join(pngdir, f"cap_{c['id']:04d}")
        for suffix, (ss, ee) in (("_s", (s, s + POP)), ("", (s + POP, e))):
            inputs += ["-i", base + suffix + ".png"]; n += 1
            y = f"{Y}*H-h/2"
            filt.append(f"{last}[{n}:v]overlay=(W-w)/2:{y}:enable='between(t,{ss:.3f},{ee:.3f})'[v{n}]")
            last = f"[v{n}]"
    cmd = ["ffmpeg", "-y", "-v", "error", "-stats", *inputs, "-filter_complex", ";".join(filt), "-map", last, "-map", "0:a?",
           "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print(f"burned {len(chunks)} captions → {out}")
else:
    sys.exit(__doc__)
