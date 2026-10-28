# -*- coding: utf-8 -*-
# needs: rembg, PIL
"""Cuts a person or product out of its background → transparent PNG.

    rembg.py <photo.jpg> <out.png> [--model isnet-general-use|u2net]
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import sys
from PIL import Image
from rembg import new_session, remove

a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
model = a[a.index("--model") + 1] if "--model" in a else "isnet-general-use"
im = Image.open(a[0]).convert("RGBA")
out = remove(im, session=new_session(model), alpha_matting=True, alpha_matting_foreground_threshold=240, alpha_matting_background_threshold=10)
out.save(a[1]); print(f"cutout {out.size[0]}x{out.size[1]} → {a[1]}")
