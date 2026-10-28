---
name: goharyai-reel
description: Turns a raw talking-to-camera video into a finished reel, ad or YouTube video — removes silences and bad takes, word-timed captions (Arabic or English), branded motion cards timed to the words, punch-in zooms, original music, sound effects, end card, loudness-normalised, with a QA pass. 9:16 for Reels/TikTok/Shorts, 16:9 for YouTube, multi-camera podcast clips. Use when the user says "edit this video", "make a reel from this", "remove the silences", "add captions", "cut my talking head", "منتج الفيديو ده", "اعمل ريل من الفيديو", "شيل السكتات", "ركّب كابشن", or sends a talking-head .mp4/.mov. Not for footage without speech (goharyai-motion), not for hook+screen ads (goharyai-hook-ads).
---

# goharyai-reel — talking head → finished reel

`$CORE` = `~/.claude/skills/goharyai-core` (read its SKILL.md once). Work in one project folder per video: `work/` and `out/`.

## 0. Before touching the file (silently)
- `node $CORE/scripts/run.js env.py` if `scripts/env.json` is missing.
- `ffprobe` the source: duration, size, rotation. Extract one frame and **look at it** (phones lie about rotation).
- Decide the output: 9:16 1080×1920 unless the user asked for YouTube (16:9 1920×1080) or the source is clearly landscape and they said "YouTube".
- Brand: core `brand.json` unless the project has its own. If the user gives colours/logo, write a project `brand.json` first.

## 1. Transcribe
```bash
node $CORE/scripts/run.js transcribe.py src.mp4 work/words.json --lang auto --prompt "names, brands, terms the speaker uses"
```
Read `work/words.txt`. Fix obvious misspellings of names in `words.json` (search/replace the `w` field) — captions are built from it.

## 2. Cut plan → show the user the sentences
```bash
node $CORE/scripts/run.js cutplan.py src.mp4 work/words.json work/plan.json
```
Open `work/plan.txt`. Remove: repeated takes (keep the **last** clean take of a sentence), false starts, "um/so/okay" openers, anything off-topic. Mark removals by deleting the block from `plan.json` or adding `"drop": true`.
Show the kept sentences to the user as a numbered list and ask only: "any line to remove?". Apply their answer.

## 3. Cut
```bash
node $CORE/scripts/run.js cut.py src.mp4 work/plan.json work/cut.mp4 --zoom --size 1080x1920
```
`--zoom` alternates 1.00/1.08 between blocks so jump cuts read as intentional. Re-transcribe the cut (`work/cut_words.json`) — captions and card times must come from the **cut** file, never from the source.

## 4. Captions
```bash
node $CORE/scripts/run.js captions.py chunk work/cut_words.json work/chunks.json --hot "key,words"
node $CORE/scripts/captions.js work/chunks.json work/caps --style tiktok
node $CORE/scripts/run.js captions.py burn work/cut.mp4 work/chunks.json work/caps work/captioned.mp4 --y 0.74
```
Style: `tiktok` (white, black stroke) by default; `brand` (ink box, paper text) for a calmer look; `box` for white backgrounds. Arabic chunks: `--max 4`. Hot words = the 3–6 words that carry the message, drawn in the accent red. Never caption every single word in red.

## 5. Motion cards (the part that makes it look edited)
Copy `$CORE/templates/overlay-cards/compose.html` to `work/cards/`, write `work/cards/data.json` with `words` = cut words and 3–6 cards:
- **lower** at 0.3 s: speaker name + handle (3 s).
- **title** when the topic is named ("@word" timing), **bullets** when a list is spoken (one item per spoken point, items appear 0.22 s apart), **stat** for any number, **pill** for step labels, **end** for the last 2.5–3 s (CTA + handle).
Rules: one card on screen at a time; cards sit in the top band (`pos:"top"`) so the face and captions stay clear; a card lives 2.5–6 s; nothing in the last 0.3 s before a cut.
```bash
node $CORE/scripts/render.js work/cards preview 1 4 8          # look at prev/*.png first
node $CORE/scripts/render.js work/cards all --png --range 0,DUR
node $CORE/scripts/run.js overlay.py work/captioned.mp4 work/carded.mp4 work/cards
```
Render only the ranges that have cards if the video is long (several `--range` renders into separate folders, all passed to overlay.py).

## 6. Sound
- Music: `node $CORE/scripts/run.js score.py work/score.wav DUR --bpm 104 --key Dm --mood drive --cuts "t1,t2,…"` with the card start times as cuts. Pick a different key/bpm/seed per video (Am 96 calm · Dm 108 drive · Em 118 energetic).
- SFX: `work/events.json` — `whoosh` on each card entry, `pop` on each bullet, `tick`×n on a counter, `chime` on the end card. `node $CORE/scripts/run.js sfx.py work/events.json work/sfx.wav --dur DUR`.
- Mix: `node $CORE/scripts/run.js mix.py work/carded.mp4 out --music work/score.wav --sfx work/sfx.wav` → `out/final.mp4` + `out/final_nomusic.mp4`.

## 7. QA, then deliver
```bash
node $CORE/scripts/run.js qa.py out/final.mp4 --script work/cut_words.txt
node $CORE/scripts/run.js sheet.py out/final.mp4 out/sheet.jpg --n 12
```
Look at the sheet: captions readable, no card over a face, end card present, nothing cut mid-word. Fix and re-run until `✅ pass`.
Deliver: paths of `final.mp4`, `final_nomusic.mp4`, `sheet.jpg`, and 3 caption suggestions for the post. Keep the report short.

## Variants
- **YouTube 16:9**: `--size 1920x1080`, captions `--y 0.86` style `brand`, cards `pos:"bottom"`, loudness is the same.
- **Podcast / two cameras**: cut each camera with the same `plan.json` (same timestamps), then alternate blocks between the two files in `cut.py` order (odd blocks cam A, even blocks cam B) by writing two plans; join with the concat in cut.py.
- **No speech**: this is not the skill; use goharyai-motion.

## Errors not to repeat
- Timing cards from the source words instead of the cut words → every card lands late.
- Caption band and lower-third overlapping → keep captions at `--y 0.74`, lower-third is at the bottom band by design.
- Leaving the first 0.3 s silent → the hook must start speaking immediately; trim leading silence in the plan.
- Shipping without `final_nomusic.mp4` → platforms' trending audio needs the clean version.
