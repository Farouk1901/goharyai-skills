---
name: goharyai-clone
description: Analyses a reference reel the user admires and rebuilds its structure with the user's own content — measures cut count, shot length, headline life, caption rate, text sizes and motion share, then offers two routes (an original idea in the same format, or a faithful professional remake), builds it with the other GoharyAI skills, and proves the match with a side-by-side comparison board before delivery. Use when the user sends a reel/TikTok/YouTube link or file and says "make one like this", "clone this style", "analyse this reel", "why does this work", "استنسخ الفيديو ده", "اعمل زي ده", "حلّل الريل ده". Needs the reference as a local file (the user downloads it; this skill never scrapes).
---

# goharyai-clone — reference analysis → remake with your content

`$CORE` = `~/.claude/skills/goharyai-core`. Project folder: `ref/` (the reference file), `work/`, `out/`.

## 1. Get the reference as a file
Ask the user for the video file (or a screen recording of it). Do not download from platforms. Put it in `ref/ref.mp4`.

## 2. Measure, don't guess
```bash
node $CORE/scripts/run.js sheet.py ref/ref.mp4 work/ref_sheet.jpg --n 16 --cols 8
node $CORE/scripts/run.js transcribe.py ref/ref.mp4 work/ref_words.json --lang auto
node $CORE/scripts/run.js compare.py ref/ref.mp4 ref/ref.mp4 work/ref      # self-compare = raw metrics of the reference
```
Read the sheet and `work/ref_metrics.json`. Write `work/analysis.md` with:
- **Format**: talking head / screen demo / motion text / mixed; aspect; length.
- **Structure** with timestamps: hook (0–2 s: what is said and shown), setup, payoff/list, CTA.
- **Rhythm**: hard cuts, average shot length, headline life, caption updates per second, motion share.
- **Type**: headline height px, caption height px, position, colour logic (what gets the accent).
- **Sound**: voice / music / SFX, where the beats land.
- **Why it works**: one paragraph — the single mechanism (curiosity gap, contrast, countdown, proof…).

## 3. Offer two routes, then wait
Show the analysis in 10 lines and the two options:
1. **Original** — same mechanism and rhythm, new script and visuals written by you for the user's product.
2. **Remake** — same structure and timings shot-for-shot, the user's words and assets in place of the original's.
Either way: only the user's own footage, screenshots, numbers and brand. Nothing from the reference is reused (no frames, no clips, no audio).

## 4. Build with the matching skill
- Talking head → **goharyai-reel** (cut plan sized to the reference's shot length; cards at the reference's headline moments).
- Hook + screen → **goharyai-hook-ads**.
- Text/motion → **goharyai-motion** (scene count and lengths from the analysis; `compare.py` headline_life_mean is your target scene length).
Carry the measured numbers into the build: if the reference changes headline every 2.4 s and captions 1.1×/s, so does yours.

## 5. Prove the match
```bash
node $CORE/scripts/run.js compare.py ref/ref.mp4 out/final.mp4 work/cmp
```
`work/cmp_board.jpg` (reference top, yours bottom, same proportional times) and `work/cmp_metrics.json`. Acceptable: cuts ±20 %, headline life ±0.5 s, caption rate ±0.3/s, text heights ±15 %. Adjust and rebuild until it holds; then run `qa.py`.

## 6. Deliver
`final.mp4`, `final_nomusic.mp4`, `cmp_board.jpg`, the metrics table (reference vs yours), and the 3-line "why it works" so the user learns the pattern. Short report.

## Rules
- The reference is a ruler, not a source: never ship any pixel or sample from it.
- Numbers on screen must be the user's real numbers; if they have none, build the Original route without numbers.
- Do not copy a competitor's name, logo or UI; replace with the user's.
- One reference per build. Two references → two analyses, then the user picks.
