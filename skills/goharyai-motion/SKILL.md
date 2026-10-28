---
name: goharyai-motion
description: Makes a motion-graphics video with no camera footage — from a script or an idea — kinetic typography timed word by word to a voice-over, counters, lists, terminal typing, product screenshots with zoom, quotes, branded end card; English voice generated offline or any recorded voice (Arabic included); original music and sound effects; 9:16 or 16:9. Use when the user says "motion graphics video", "animate this script", "explain this in a video without me on camera", "app demo video from screenshots", "text video", "فيديو موشن", "حوّل النص ده لفيديو", "اشرح التطبيق بفيديو", "فيديو بدون ظهوري". Not for talking-head footage (goharyai-reel).
---

# goharyai-motion — script → motion video

`$CORE` = `~/.claude/skills/goharyai-core`. Project folder with `work/`, `out/`, and `work/motion/` (the scene page).

## 1. Script first, approve, then build
Write the voice-over script: 60–140 words for a 25–50 s reel, one sentence per line, hook in the first line, a number or a concrete claim by line 3, CTA last. Show it to the user and get a yes before any rendering — rewriting the script after rendering costs the whole render.

## 2. Voice + word timings
- English: `node $CORE/scripts/run.js tts.py work/vo.txt work/vo.wav --voice am_michael --speed 1.05` → `work/vo.words.json` (exact timings, no transcription needed). Voices: `am_michael` (warm), `am_adam` (deep), `am_fenrir` (energetic), `af_heart`, `bf_emma` (UK).
- Arabic or the user's own voice: they record (or generate elsewhere) `work/vo.wav`; then `node $CORE/scripts/run.js transcribe.py work/vo.wav work/vo.words.json --lang ar`. Check the text; fix names in the json.
- Rhythm: the script's natural pace sets the video length. Never speed audio after generation; change `--speed` and regenerate.

## 3. Scenes
Copy `$CORE/templates/motion/compose.html` to `work/motion/` and write `work/motion/data.json`:
```json
{ "words": <vo.words.json>, "theme": "dark", "captions": true, "hot": ["free", "today"],
  "scenes": [
    {"type":"hero",  "a":0,        "b":"@hours",  "text":"Most people *waste* hours", "sub":"editing one reel"},
    {"type":"type",  "a":"@This",  "b":"@music",  "label":"$ one command", "text":"goharyai-reel ./raw.mp4"},
    {"type":"list",  "a":"@three", "b":"@result", "title":"What it does", "items":["Cuts silences","Word captions","Music + SFX"]},
    {"type":"stat",  "a":"@twelve","b":"@faster", "value":12, "suffix":"×", "label":"faster than *manual*"},
    {"type":"image", "a":"@look",  "b":"@now",    "src":"file:///…/screen.png", "caption":"The result", "zoom":1.08},
    {"type":"quote", "a":"@said",  "b":"@follow", "text":"“Build once, post everywhere.”", "who":"Ahmed Farouk Gohary"},
    {"type":"end",   "a":"@follow","b":28.5,      "text":"Follow for the next one", "sub":"@goharyai"} ] }
```
Scene grammar: **one idea per scene, 2.5–6 s each**, scene boundaries on word starts (`"@word"`), the hero scene carries the hook, a `stat` or `list` in the middle, `end` for the last 2.5–3 s. 6–9 scenes for 30 s. Images: the user's screenshots/product photos only (`file:///` absolute paths), never stock from the web. `theme: "light"` for a clean editorial look, `dark` for cinematic.
Preview before rendering:
```bash
node $CORE/scripts/render.js work/motion preview 0.5 3 7 12 18 25     # look at every prev/*.jpg
```
Check text fits (no line wider than the frame, no overlap with captions at the bottom third), accent used on ≤ 2 words per scene, logo visible bottom-left.

## 4. Render
```bash
JOBS=2 node $CORE/scripts/render.js work/motion all --out work/video.mp4      # ~30 fps × duration frames; ≈ 1 min per 10 s on a laptop
```
`RESUME=1` continues after a crash. Then music, SFX, mix (cuts = scene start times):
```bash
node $CORE/scripts/run.js score.py work/score.wav DUR --bpm 108 --key Dm --mood drive --cuts "3.1,7.4,12.0,…"
node $CORE/scripts/run.js sfx.py work/events.json work/sfx.wav --dur DUR      # whoosh per scene, pop per list item, tick on counters, chime on end
node $CORE/scripts/run.js mix.py work/video.mp4 out --voice work/vo.wav --music work/score.wav --sfx work/sfx.wav
```

## 5. QA and deliver
`node $CORE/scripts/run.js qa.py out/final.mp4 --script work/vo.txt` must pass (script match ≥ 90 % proves no word was cut). `sheet.py` for a 12-frame look. Deliver `final.mp4`, `final_nomusic.mp4`, the sheet, and the script as the post caption.

## 16:9 explainer
`"w":1920, "h":1080` in data.json; the template scales type with the short side. Captions move to the bottom 14 %. Same flow.

## Rules
- Pure function of time: no CSS animations or timers in a scene page — frames render in any order.
- Red accent on one element per scene; never a red background.
- Type sizes: hero ≥ 96 px, body ≥ 44 px at 1080 wide — phones are read at arm's length.
- The last frame is a still end card for ≥ 1.5 s (platforms freeze it as the loop point).
