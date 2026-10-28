# -*- coding: utf-8 -*-
# needs: PIL
"""Contact sheet: one image with N frames of a video so the model can look at a whole edit at once.

    sheet.py <video> <out.jpg> [--n 12] [--cols 6] [--w 240] [--times "1,2.5,4"]
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw

a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
video, out = a[0], a[1]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
N, COLS, W = int(opt("--n", 12)), int(opt("--cols", 6)), int(opt("--w", 240))
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video]).decode().strip())
times = [float(x) for x in opt("--times", "").split(",") if x.strip()] or [dur * (i + .5) / N for i in range(N)]
tmp = tempfile.mkdtemp(); tiles = []
for i, t in enumerate(times):
    f = os.path.join(tmp, f"{i}.jpg")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", video, "-frames:v", "1", "-q:v", "3", f], check=True)
    im = Image.open(f); im.thumbnail((W, W * 2)); d = ImageDraw.Draw(im); d.rectangle((0, 0, 70, 22), fill="black"); d.text((4, 4), f"{t:.1f}s", fill="white"); tiles.append(im)
tw, th = max(t.width for t in tiles), max(t.height for t in tiles)
rows = (len(tiles) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * tw, rows * th), "#222")
for i, t in enumerate(tiles): sheet.paste(t, ((i % COLS) * tw, (i // COLS) * th))
sheet.save(out, quality=85); print(f"sheet {len(tiles)} frames → {out}")
