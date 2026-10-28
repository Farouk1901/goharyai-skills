# -*- coding: utf-8 -*-
"""Layers transparent frame sequences (from render.js --png --range) over a video.

    overlay.py <video> <out.mp4> <layer_dir> [<layer_dir> ...]

Each layer_dir is a render.js project folder containing frames/ and frames.json (fps, start, end).
Frames are placed at their own timestamps (frame index / fps), so a card rendered for 3.2–6.0 s
lands exactly there. Audio is copied from the video unchanged.
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import json, os, subprocess, sys

a = sys.argv[1:]
if len(a) < 3: sys.exit(__doc__)
video, out, layers = a[0], a[1], a[2:]
inputs, filt, last = ["-i", video], [], "[0:v]"
for n, d in enumerate(layers, 1):
    meta = json.load(open(os.path.join(d, "frames.json"), encoding="utf-8"))
    fps, s, e = meta["fps"], meta["start"], meta["end"]
    inputs += ["-framerate", str(fps), "-start_number", str(s), "-i", os.path.join(d, "frames", "%05d.png")]
    t0 = s / fps
    filt.append(f"[{n}:v]format=rgba,setpts=PTS-STARTPTS+{t0:.4f}/TB[l{n}];{last}[l{n}]overlay=0:0:eof_action=pass:enable='between(t,{t0:.3f},{e / fps:.3f})'[v{n}]")
    last = f"[v{n}]"
cmd = ["ffmpeg", "-y", "-v", "error", "-stats", *inputs, "-filter_complex", ";".join(filt), "-map", last, "-map", "0:a?",
       "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print(f"overlaid {len(layers)} layer(s) → {out}")
