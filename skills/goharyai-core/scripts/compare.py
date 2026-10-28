# -*- coding: utf-8 -*-
# needs: numpy, PIL
"""Measures a reference video against your version and builds a side-by-side board.

    compare.py <reference.mp4> <mine.mp4> <out_prefix>

Prints and writes <out_prefix>_metrics.json: duration, headline changes and their average life,
caption updates per second, motion share, hard cuts, headline and caption heights in px.
Writes <out_prefix>_board.jpg: reference on top, yours below, at the same proportional times.
Use it to match pacing, cut count and text sizes before delivering a clone.
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import json, os, statistics, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageChops, ImageStat

a = sys.argv[1:]
if len(a) < 3: sys.exit(__doc__)
ref, mine, out = a

def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode().strip())
def frames(f, d):
    os.makedirs(d, exist_ok=True)
    if not os.listdir(d): subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vf", "fps=10,scale=1080:1920", "-q:v", "4", os.path.join(d, "%05d.jpg")], check=True)
    return sorted(os.listdir(d))
def groups(ts, gap):
    g = []
    for t in ts:
        if not g or t - g[-1][-1] > gap: g.append([t])
        else: g[-1].append(t)
    return [x[0] for x in g]
def lines(path, box, thr):
    im = np.array(Image.open(path).convert("L").crop(box)).astype(int); m = im < thr; r = np.where(m.sum(1) > 3)[0]
    if len(r) == 0: return []
    outl, s, p = [], r[0], r[0]
    for y in r[1:]:
        if y - p > 6: outl.append((s + box[1], p + box[1])); s = y
        p = y
    outl.append((s + box[1], p + box[1])); return outl

def analyse(f, tag):
    d = os.path.join(tempfile.gettempdir(), f"cmp_{tag}_{abs(hash(os.path.abspath(f))) % 100000}")
    fs = frames(f, d); D = dur(f)
    Z = {"head": (0, 120, 1080, 420), "ill": (0, 420, 1080, 1300), "cap": (0, 1300, 1080, 1700)}
    prev = {k: Image.open(os.path.join(d, fs[0])).convert("L").crop(b) for k, b in Z.items()}
    ch = {k: [] for k in Z}
    for i in range(1, len(fs)):
        im = Image.open(os.path.join(d, fs[i])).convert("L")
        for k, b in Z.items():
            c = im.crop(b); ch[k].append(ImageStat.Stat(ImageChops.difference(c, prev[k])).mean[0]); prev[k] = c
    H = groups([(i + 1) / 10 for i, x in enumerate(ch["head"]) if x > 4], .35)
    C = groups([(i + 1) / 10 for i, x in enumerate(ch["cap"]) if x > 3], .15)
    gaps = [b - a for a, b in zip(H, H[1:])] or [0]
    mov = sum(1 for x in ch["ill"] if x > .8) / max(1, len(ch["ill"]))
    hh, cb = [], []
    for k in range(5, len(fs), max(1, len(fs) // 12)):
        p = os.path.join(d, fs[k]); l = lines(p, (0, 40, 1080, 460), 90); c = lines(p, (0, 1250, 1080, 1750), 40)
        if l: hh.append(l[0][1] - l[0][0])
        if c: cb.append(c[0][1] - c[0][0])
    cuts = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f, "-vf", "select='gt(scene,0.3)',metadata=print", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr.count("pts_time")
    return dict(duration=round(D, 1), headline_changes=len(H), headline_life_mean=round(statistics.mean(gaps), 2), caption_updates_per_sec=round(len(C) / D, 2),
                motion_share=round(mov, 2), hard_cuts=cuts, headline_line_px=int(statistics.median(hh)) if hh else 0, caption_box_px=int(statistics.median(cb)) if cb else 0), d, fs, D

A, da, fa, Da = analyse(ref, "r"); B, db, fb, Db = analyse(mine, "m")
res = {k: {"reference": A[k], "mine": B[k]} for k in A}
json.dump(res, open(out + "_metrics.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in res.items(): print(f"{k:24} reference {v['reference']:>7}   mine {v['mine']:>7}")
W, H = 216, 384; board = Image.new("RGB", (W * 10, H * 2), "white")
for i in range(10):
    r = (i + .5) / 10; ia = min(len(fa) - 1, int(r * Da * 10)); ib = min(len(fb) - 1, int(r * Db * 10))
    board.paste(Image.open(os.path.join(da, fa[ia])).resize((W, H)), (i * W, 0)); board.paste(Image.open(os.path.join(db, fb[ib])).resize((W, H)), (i * W, H))
board.save(out + "_board.jpg", quality=88); print("board", out + "_board.jpg")
