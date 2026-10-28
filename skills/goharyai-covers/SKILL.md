---
name: goharyai-covers
description: Designs the still images around a video or post — reel covers (everything important inside the 1:1 centre so the profile grid shows it), YouTube thumbnails (three ideas, readable at 150 px), Instagram/LinkedIn carousels (cover, numbered points, code/prompt boxes, image slides, CTA) in a white editorial or dark cinematic style, and cut-out portraits of the user for them. Use when the user says "cover for this reel", "thumbnail", "make a carousel", "slides for Instagram", "cut me out of the background", "كفر الريل", "ثمبنيل", "اعمل كاروسيل", "قص الخلفية", or after any finished video. Not for video.
---

# goharyai-covers — covers, thumbnails, carousels

`$CORE` = `~/.claude/skills/goharyai-core`. Project folder with `work/` and `out/`.

## Reel cover (1080×1920)
1. Copy `$CORE/templates/covers/cover.html` to `work/`. Write `work/cover.json`:
   `{"title":"3 AI tools *that sell*", "kicker":"FREE GUIDE", "sub":"for online sellers", "theme":"dark", "layout":"center", "image":"file:///…/me-cutout.png"}`
   Title 2–5 words, one `*accent*` word, kicker optional, `layout` = `center` (text only), `split` (text left, person/product right), `poster` (text over a `bg` photo).
2. `node $CORE/scripts/still.js work/cover.html out/cover.jpg --w 1080 --h 1920 --data work/cover.json`
3. Look at it. The title must sit between y 420–1500 (the template does this) — the grid crop is the centre square.
4. To use it as the video's first frame: `ffmpeg -i out/cover.jpg -i final.mp4 …` is not needed; upload it as the cover in the app. If the user wants it baked in, prepend 1 frame: `ffmpeg -loop 1 -t 0.04 -i out/cover.jpg -i final.mp4 -filter_complex "[0:v]scale=1080:1920,fps=30[c];[c][1:v]concat=n=2:v=1[v]" -map "[v]" -map 1:a -c:a copy out/final_cover.mp4`.

## YouTube thumbnail (1280×720) — three ideas
Same template with `--w 1280 --h 720`. Make **three** `thumb-N.json` variants and render all; they differ in mechanism, not colour:
1. **Big claim** — 3 words, `center`.
2. **Face + object** — user's cut-out (`image`) with a 2-word title, `split`.
3. **Before/after or number** — a stat as the title ("12× faster"), `poster` over a screenshot `bg`.
Rules: ≤ 4 words, title height ≥ 18 % of frame, one accent word, no small text (read at 150 px), face looking at the camera, no logo bigger than 6 % of width.

## Carousel (1080×1350)
1. Copy `$CORE/templates/carousel/carousel.html` to `work/`, write `work/carousel.json` (see the template header): `cover` → 3–7 `point` slides (one idea each, body ≤ 25 words, optional `code` box for a prompt) → optional `image` or `list` → `cta` (what to do: save / follow / comment a word).
2. `node $CORE/scripts/still.js work/carousel.html out/slide.png --w 1080 --h 1350 --data work/carousel.json --slides N`
3. Look at slide 1 and the longest point slide; shorten any body that wraps past 4 lines. `theme:"light"` is the house style for educational posts; `dark` for announcements.
Slides carry the page counter and handle automatically; the cover carries the wordmark.

## Cut-out portrait (for covers and thumbnails)
```bash
node $CORE/scripts/run.js rembg.py photo.jpg out/cutout.png     # if rembg is installed (env.py shows it)
```
If `rembg` is missing, tell the user in one line and continue with `layout:"center"`. Use the user's own photos only.

## Deliver
Paths of the files and a one-line reason for the chosen title. For thumbnails, say which of the three you would publish and why (contrast, curiosity, readability).

## Rules
- Brand colours from `brand.json`; the red is one word or one shape per image, never a background.
- Fonts: Inter/Montserrat latin, Cairo arabic — set automatically by the templates.
- Titles are written for the viewer's problem, not the product's name.
- Every image file name says what it is: `cover-reel-<slug>.jpg`, `thumb-<slug>-1.jpg`, `carousel-<slug>-3.png`.
