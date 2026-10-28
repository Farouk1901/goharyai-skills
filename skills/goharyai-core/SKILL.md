---
name: goharyai-core
description: Shared toolkit for the GoharyAI video skills (goharyai-reel, goharyai-hook-ads, goharyai-motion, goharyai-clone, goharyai-covers). Not invoked on its own; the other skills call its scripts. Holds the brand kit (brand.json + logo), fonts, headless-Chrome renderer, word-timed transcription, voice-over, captions, cut planning, music and SFX synthesis, mixing, QA and comparison tools. Read this file when a GoharyAI skill points you here or when you need to change the brand, fonts or a shared script.
---

# goharyai-core — shared toolkit

`$CORE` below means this folder (normally `~/.claude/skills/goharyai-core`). Every script prints its own usage when run without arguments.

## First run (once per machine)
```bash
cd $CORE && npm install                 # puppeteer-core only
node $CORE/scripts/run.js env.py        # ✅/❌ table; writes scripts/env.json
```
Requirements: **ffmpeg**, **node ≥ 18**, **Chrome/Edge/Brave**, Python 3 with `faster-whisper numpy soundfile pillow`.
Optional: `kokoro` (English voice-over, Python ≤ 3.12), `rembg` (background removal).
`run.js` picks the Python that has what a script needs (several Pythons on one machine are fine).

## Brand kit
`brand.json`: name, handle, author, colours (`accent` red `#E40000`, `ink` `#303438`, `ink_deep`, `paper` `#F8F8F8`), two logos (`on_light`, `on_dark`), fonts (`Inter` latin, `Cairo` arabic, `Montserrat` display), caption style, rules.
A project folder may contain its own `brand.json` (+ logo files) and every template uses it instead — that is how the skills work for another brand. Never edit the core one for a client; copy it into the project.

## Scripts (`$CORE/scripts`)
| Script | Does | Typical call |
|---|---|---|
| `env.py` | environment check → env.json | `node run.js env.py` |
| `transcribe.py` | speech → `words.json` [{w,s,e}] + `.txt` (faster-whisper, offline, auto language) | `node run.js transcribe.py in.mp4 work/words.json --lang en --prompt "GoharyAI, Claude"` |
| `tts.py` | English voice-over + exact word timings (Kokoro) | `node run.js tts.py script.txt work/vo.wav --voice am_michael` |
| `cutplan.py` | sentence list without silences → `plan.json` + readable `plan.txt` | `node run.js cutplan.py in.mp4 work/words.json work/plan.json` |
| `cut.py` | applies plan: concat, resize, alternating punch-in | `node run.js cut.py in.mp4 work/plan.json work/cut.mp4 --zoom --size 1080x1920` |
| `captions.py` | `chunk` words → chunks.json; `burn` PNGs into video with pop | see goharyai-reel |
| `captions.js` | renders chunk PNGs in Chrome (styles tiktok/box/yellow/brand, Arabic shaping) | `node captions.js work/chunks.json work/caps --style tiktok` |
| `render.js` | compose.html + data.json → frames → mp4; `--png --range a,b` for transparent overlays | `node render.js dir preview 1 3 5` then `node render.js dir all --out x.mp4` |
| `overlay.py` | layers `--png` frame sequences over footage at their own times | `node run.js overlay.py cut.mp4 out.mp4 cards/` |
| `still.js` | one HTML → PNG/JPG (or N slides via `window.slide(i)`) | `node still.js cover.html out.jpg --w 1080 --h 1920 --data d.json` |
| `score.py` | original music per video (key, bpm, mood, hits on cut times) | `node run.js score.py work/score.wav 32 --bpm 108 --key Dm --cuts "4,9,19"` |
| `sfx.py` | synthesised whoosh/pop/thud/tick/chime/key/paper/riser on a timeline | `node run.js sfx.py events.json work/sfx.wav --dur 32` |
| `mix.py` | voice −16 LUFS, music ducked −22 dB, sfx −6 dB → `final.mp4` + `final_nomusic.mp4` | `node run.js mix.py in.mp4 out --music work/score.wav --sfx work/sfx.wav` |
| `qa.py` | loudness, black/frozen frames, transcript vs script → pass/fail | `node run.js qa.py out/final.mp4 --script script.txt` |
| `sheet.py` | contact sheet (N frames in one image) — look at it instead of playing the video | `node run.js sheet.py out/final.mp4 out/sheet.jpg --n 12` |
| `compare.py` | reference vs mine: cuts, pacing, text sizes + side-by-side board | `node run.js compare.py ref.mp4 mine.mp4 out/cmp` |
| `hookads.py` | hook × demo matrix builder (scan / build) | see goharyai-hook-ads |

## Templates (`$CORE/templates`) — copy into the project, never edit in place
- `overlay-cards/compose.html` — title / bullets / stat / lower-third / pill / end card over footage (transparent).
- `motion/compose.html` — full-frame scenes: hero, type, list, stat, image, quote, end; built-in captions.
- `covers/cover.html` — reel cover 9:16 or YouTube thumbnail 16:9 (poster / split / center layouts).
- `carousel/carousel.html` — cover / point / image / list / cta slides, light or dark.
Each template documents its `data.json` at the top. Times accept seconds or `"@word"` / `"@word#2"` (from words.json). `*asterisks*` colour a word with the accent. Arabic text switches the block to RTL automatically.

## Writing a new scene page
A page is plain HTML + CSS + a script that registers scenes with `K.scene({a, b, html, upd})`. `window.draw(t)` is called per frame, so everything must be a pure function of `t` (no CSS animations, no timers). Helpers on `K`: easing (`eo`, `eio`, `back`), `pr(t,a,b)` progress, `pop/fade/slideIn/flipIn/zoomIn/blurOut`, `type` (typewriter), `count` (counter), `wt(word)` word time, `caption(t)` word-timed captions, `icon.*` inline SVG icons, `logo(theme, h)`. `window.BRAND` holds brand.json.

## Conventions every skill follows
- One **project folder** per video: `src/` inputs, `work/` intermediates, `out/` deliverables, `brand.json` optional.
- Look before rendering: `render.js … preview` frames and `sheet.py` sheets are cheap; full renders are not.
- `JOBS=2` on machines with ≤ 8 GB RAM; `RESUME=1` continues an interrupted render.
- Always deliver `final.mp4` **and** `final_nomusic.mp4`, and run `qa.py` before showing anything.
- Talk to the user in their language. Report in a few lines: what was made, where it is, what to check.
- Use only the user's own footage, images and brand. Never pull assets from other projects or clients.
