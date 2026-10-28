# -*- coding: utf-8 -*-
"""Applies a cut plan: keeps the listed blocks, in order, and re-encodes to one clean file.

    cut.py <video> <plan.json> <out.mp4> [--zoom] [--size 1080x1920] [--fit cover|contain] [--fps 30]

--zoom   alternates a subtle punch-in (1.00 → 1.08) between consecutive blocks, the standard
         talking-head trick that hides jump cuts. Needs --size.
--size   output frame (default: keep source size). cover = fill and crop, contain = pad with blur.
Audio is kept in sync by trimming audio and video with the same timestamps.
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import json, subprocess, sys

a = sys.argv[1:]
if len(a) < 3: sys.exit(__doc__)
video, planf, out = a[0], a[1], a[2]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
ZOOM, FIT, FPS = "--zoom" in a, opt("--fit", "cover"), int(opt("--fps", 30))
size = opt("--size"); W, H = (map(int, size.lower().split("x")) if size else (None, None))
plan = json.load(open(planf, encoding="utf-8"))
blocks = [b for b in plan["keep"] if not b.get("drop")]
if not blocks: sys.exit("plan has no blocks to keep")

probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:stream_tags=rotate:side_data_list", "-of", "json", video]))
st = probe["streams"][0]; sw, sh = st["width"], st["height"]
rot = int(st.get("tags", {}).get("rotate", 0) or 0) or next((int(d.get("rotation", 0)) for d in st.get("side_data_list", []) if "rotation" in d), 0)
if rot % 180: sw, sh = sh, sw                      # phones store vertical video as rotated landscape
if not W: W, H = sw, sh

def frame_filter(i):
    """scale/crop to WxH, optional punch-in on odd blocks"""
    z = 1.08 if (ZOOM and i % 2) else 1.0
    if FIT == "contain":
        base = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black"
    else:
        base = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    if z > 1: base += f",scale=iw*{z}:ih*{z},crop={W}:{H}:(iw-{W})/2:(ih-{H})*0.42"
    return base + f",fps={FPS},setsar=1"

parts, fc = [], []
for i, b in enumerate(blocks):
    fc.append(f"[0:v]trim=start={b['s']}:end={b['e']},setpts=PTS-STARTPTS,{frame_filter(i)}[v{i}];"
              f"[0:a]atrim=start={b['s']}:end={b['e']},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={max(0, b['e'] - b['s'] - 0.015)}:d=0.015[a{i}]")
    parts.append(f"[v{i}][a{i}]")
fc.append("".join(parts) + f"concat=n={len(blocks)}:v=1:a=1[v][a]")
cmd = ["ffmpeg", "-y", "-v", "error", "-stats", "-i", video, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
       "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print(f"cut {len(blocks)} blocks → {out} ({W}x{H}{', zoom' if ZOOM else ''})")
