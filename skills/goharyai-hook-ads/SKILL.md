---
name: goharyai-hook-ads
description: Builds "hook + screen demo" ads in bulk for testing — a short clip of a person speaking or reacting to camera, then a silent screen recording with one caption per step, music under everything, each hook combined with each demo (4 hooks × 4 demos = 16 ad variants named Hook1_D1.mp4 …). Use when the user says "hook ads", "UGC ad variants", "hook + screen recording", "faceless demo ad", "make ad variations", "إعلانات هوك", "ركّب الهوكات على الشرح", "اعمل نسخ إعلان", or gives folders of hooks, demos and music. Not for a single talking video (goharyai-reel).
---

# goharyai-hook-ads — hook × demo ad matrix

`$CORE` = `~/.claude/skills/goharyai-core`. The whole job is one script plus your writing.

## 1. Folder
```
project/
  hooks/<Person>/1.mp4 2.mp4 …   people talking/reacting to camera, 2–6 s each (audio kept)
  demos/*.mp4                    silent screen recordings of the product (phone or desktop)
  music/*.mp3                    one or more tracks the user has rights to
```
Other names work too (`hook`, `SC1`; `demo`, `bodies`, `screens`, `SC2`; `audio`). If the user sent files loose, move them into this layout first.

## 2. Scan
```bash
node $CORE/scripts/run.js hookads.py scan project/
```
Produces `project/hookads.json` (draft) and contact sheets in `project/hookads/`: `hook_<id>.jpg` (4 frames per hook) and `demo_<id>.jpg` (8 frames per demo). **Read the sheets** — that is how you know what each hook says and what each demo shows, without opening videos.

## 3. Write the texts (the only creative step — do it well)
Edit `hookads.json`:
- `hooks[].text` — the hook line as a caption, ≤ 7 words, present tense, the pain or the promise, one `*accent*` word. The spoken line and the caption should match in meaning, not necessarily word for word. If a hook has no speech (reaction only), the caption **is** the hook.
- `hooks[].trim` — `[start, end]` to drop a slow start; hooks longer than 5 s rarely survive.
- `demos[].steps` — `[{ "t": 0, "text": "Open the app" }, { "t": 4.5, "text": "Paste the *prompt*" }]`: one caption per visible action, timed to when the action starts on screen (read it off the demo sheet), 3–6 words, imperative, numbers as digits. 3–6 steps per demo.
- `demos[].speed` — 1.1–1.3 if the recording is slow; never above 1.4 (cursor becomes unreadable).
- `music.file`, `music.gain_db` (default −13: the demo part has no voice, so the track carries it; it ducks automatically while the hook speaks), `music.start` (skip an intro).
- `style.preset` — `tiktok` (white/black stroke, default), `box` (black on white, for light screens), `yellow`, `brand`.
Arabic texts are fine: they render RTL in the brand Arabic font.

## 4. One variant first, then all
```bash
node $CORE/scripts/run.js hookads.py build project/ --limit 1
node $CORE/scripts/run.js sheet.py project/out/<first>.mp4 project/hookads/check.jpg --n 8
```
Check: hook caption readable over the face (it sits at 25 % height), step captions in the middle band (46 %) not covering the UI element they talk about — move a step with `"y": 0.3` or `0.6` when needed; the cut hook→demo is clean; music level sensible.
```bash
node $CORE/scripts/run.js hookads.py build project/ --jobs 2        # everything; unchanged variants are skipped
```
`--only Ava1` rebuilds the variants of one hook or one demo. `--force` re-renders.

## 5. Deliver
`project/out/<hook>_<demo>.mp4` + `manifest.json`. Report: the count (hooks × demos), which variant to test first and why (strongest hook + clearest demo), and a reminder that the files have no end card by design (ad platforms add the CTA). Keep it short.

## Rules
- Hook audio stays; demo audio is dropped (screen recordings carry clicks and notifications).
- Never stretch or crop a demo so that UI text becomes unreadable: demos are fitted cover to 1080×1920; if the recording is landscape, ask for a portrait recording or place it in a `box` style with the caption above it.
- Every variant has the same music start, so the cut to the demo lands on the same beat across the matrix — vary hooks and demos, not the music.
- No brand logo on ad variants unless the user asks; the product on screen is the brand.
- Only the user's own hooks, demos and music. Never use another client's footage, even as a placeholder.
