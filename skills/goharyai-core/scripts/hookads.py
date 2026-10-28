# -*- coding: utf-8 -*-
"""Hook × demo matrix ads: every hook clip joined to every screen-demo clip, with step captions and music.

    hookads.py scan  <proj>                       → <proj>/hookads/scan.json + contact sheets to read
    hookads.py build <proj> [--only Ava1] [--limit 1] [--jobs 2] [--force]
                                                  → <proj>/out/<hook>_<demo>.mp4 + manifest.json

Project layout (names are flexible, see scan):
    hooks/<Person>/1.mp4 …   short talking clips (3–6 s), keep their audio   → ids Person1, Person2 …
    demos/*.mp4              silent screen recordings                      → ids D1, D2 …
    music/*.mp3|wav          one or more tracks (first is used unless set in hookads.json)
hookads.json (written by scan as a draft, edit it):
    {"style": {"preset": "tiktok"}, "music": {"file": "music/track.mp3", "gain_db": -20, "start": 0},
     "hooks": [{"id": "Ava1", "file": "hooks/Ava/1.mp4", "text": "I tried this *for a week*", "trim": [0, 4.2]}],
     "demos": [{"id": "D1", "file": "demos/a.mp4", "speed": 1.15,
                "steps": [{"t": 0.0, "text": "Open the app"}, {"t": 4.5, "text": "Paste the *prompt*"}]}]}
Caption PNGs are rendered once per unique text by captions.js (so Arabic shapes correctly) and reused.
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import hashlib, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
cmd, PROJ = a[0], os.path.abspath(a[1])
K = os.path.join(PROJ, "hookads"); os.makedirs(K, exist_ok=True)
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
VID, AUD = (".mp4", ".mov", ".m4v", ".webm", ".mkv"), (".mp3", ".wav", ".m4a", ".aac", ".ogg")
natkey = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]
rel = lambda p: os.path.relpath(p, PROJ).replace("\\", "/")
ab = lambda p: p if os.path.isabs(p) else os.path.join(PROJ, p)
W, H, FPS = 1080, 1920, 30

def probe(p):
    j = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", p]))
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), {})
    return float(j["format"]["duration"]), any(s["codec_type"] == "audio" for s in j["streams"]), v.get("width"), v.get("height")

def find_dir(names):
    for d in sorted(os.listdir(PROJ)):
        if d.lower() in names and os.path.isdir(os.path.join(PROJ, d)): return os.path.join(PROJ, d)

if cmd == "scan":
    hooks_d, demos_d, music_d = find_dir({"hooks", "hook", "sc1"}), find_dir({"demos", "demo", "bodies", "sc2", "screens"}), find_dir({"music", "audio"})
    if not hooks_d or not demos_d: sys.exit("need hooks/ and demos/ folders (or SC1/ and SC2/)")
    hooks, demos = [], []
    for person in sorted(os.listdir(hooks_d), key=natkey):
        pd = os.path.join(hooks_d, person)
        files = sorted([f for f in os.listdir(pd)], key=natkey) if os.path.isdir(pd) else [person]
        base = os.path.join(hooks_d, person) if os.path.isdir(pd) else hooks_d
        for i, f in enumerate([f for f in files if f.lower().endswith(VID)], 1):
            d, au, w, h = probe(os.path.join(base, f))
            hooks.append({"id": f"{re.sub(r'[^A-Za-z0-9]', '', person if os.path.isdir(pd) else os.path.splitext(f)[0])}{i if os.path.isdir(pd) else ''}", "file": rel(os.path.join(base, f)), "dur": round(d, 2), "audio": au, "text": ""})
    for i, f in enumerate(sorted([f for f in os.listdir(demos_d) if f.lower().endswith(VID)], key=natkey), 1):
        d, au, w, h = probe(os.path.join(demos_d, f))
        demos.append({"id": f"D{i}", "file": rel(os.path.join(demos_d, f)), "dur": round(d, 2), "speed": 1.0, "steps": [{"t": 0.0, "text": ""}]})
    music = sorted([rel(os.path.join(music_d, f)) for f in os.listdir(music_d) if f.lower().endswith(AUD + VID)], key=natkey) if music_d else []
    json.dump({"hooks": hooks, "demos": demos, "music": music}, open(os.path.join(K, "scan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    draft = os.path.join(PROJ, "hookads.json")
    if not os.path.exists(draft):
        json.dump({"style": {"preset": "tiktok"}, "music": {"file": music[0] if music else "", "gain_db": -13, "start": 0}, "hooks": hooks, "demos": demos},
                  open(draft, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # contact sheets: one row per hook (4 frames) and one per demo (8 frames) so the texts can be written from a single look
    sheet = os.path.join(HERE, "sheet.py")
    for h in hooks: subprocess.run([sys.executable, sheet, ab(h["file"]), os.path.join(K, f"hook_{h['id']}.jpg"), "--n", "4", "--cols", "4", "--w", "200"], capture_output=True)
    for d in demos: subprocess.run([sys.executable, sheet, ab(d["file"]), os.path.join(K, f"demo_{d['id']}.jpg"), "--n", "8", "--cols", "8", "--w", "200"], capture_output=True)
    print(f"{len(hooks)} hooks × {len(demos)} demos = {len(hooks) * len(demos)} ads; music: {len(music)} file(s)\n→ edit {draft} (hook text, demo steps), sheets in {K}")

elif cmd == "build":
    cfg = json.load(open(os.path.join(PROJ, "hookads.json"), encoding="utf-8"))
    ONLY, LIMIT, JOBS, FORCE = opt("--only"), int(opt("--limit", 0)), int(opt("--jobs", 2)), "--force" in a
    OUT = os.path.join(PROJ, "out"); os.makedirs(OUT, exist_ok=True)
    style = cfg.get("style", {}).get("preset", "tiktok")
    # 1) caption PNGs, one per unique text
    texts = {}
    for h in cfg["hooks"]:
        if h.get("text"): texts.setdefault(("hook", h["text"]), None)
    for d in cfg["demos"]:
        for s in d.get("steps", []):
            if s.get("text"): texts.setdefault(("step", s["text"]), None)
    chunks, capdir = [], os.path.join(K, "caps")
    for i, (role, text) in enumerate(texts, 1):
        lang = "ar" if re.search(r"[؀-ۿ]", text) else "en"
        chunks.append({"id": i, "text": text, "lang": lang, "role": role}); texts[(role, text)] = i
    idx_file = os.path.join(K, "chunks.json")
    stamp = hashlib.md5(json.dumps(chunks, ensure_ascii=False).encode() + style.encode()).hexdigest()
    if FORCE or not os.path.exists(os.path.join(capdir, stamp)):
        json.dump(chunks, open(idx_file, "w", encoding="utf-8"), ensure_ascii=False)
        subprocess.run(["node", os.path.join(HERE, "captions.js"), idx_file, capdir, "--style", style, "--brand", PROJ], check=True)
        open(os.path.join(capdir, stamp), "w").close()
    # 2) matrix
    M = cfg.get("music") or {}; MF = ab(M["file"]) if M.get("file") else None
    jobs = [(h, d) for h in cfg["hooks"] for d in cfg["demos"] if not ONLY or ONLY in (h["id"], d["id"])]
    if LIMIT: jobs = jobs[:LIMIT]
    def build(h, d):
        out = os.path.join(OUT, f"{h['id']}_{d['id']}.mp4")
        if os.path.exists(out) and not FORCE: return out, "skip"
        hd, hau, _, _ = probe(ab(h["file"])); dd, dau, _, _ = probe(ab(d["file"]))
        ha, hb = (h.get("trim") or [0, hd])[:2]; hb = min(hb, hd)
        da, db = (d.get("trim") or [0, dd])[:2]; db = min(db, dd)
        sp = float(d.get("speed", 1.0)); HL = hb - ha; T = HL + (db - da) / sp
        fit = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1"
        inputs = ["-i", ab(h["file"]), "-i", ab(d["file"])]
        fc = [f"[0:v]trim=start={ha}:end={hb},setpts=PTS-STARTPTS,{fit}[hv]",
              f"[1:v]trim=start={da}:end={db},setpts=(PTS-STARTPTS)/{sp},{fit}[dv]", "[hv][dv]concat=n=2:v=1:a=0[v0]"]
        # captions: hook text over the hook, each step from its time until the next
        overlays, n, last = [], 1, "[v0]"
        caps = []
        if h.get("text"): caps.append((texts[("hook", h["text"])], 0.0, HL, 0.25))
        steps = sorted([s for s in d.get("steps", []) if s.get("text") and da <= s["t"] < db], key=lambda s: s["t"])
        for i, s in enumerate(steps):
            t0 = HL + (s["t"] - da) / sp; t1 = HL + (steps[i + 1]["t"] - da) / sp if i + 1 < len(steps) else T
            caps.append((texts[("step", s["text"])], t0, t1, s.get("y", 0.46)))
        for cid, t0, t1, y in caps:
            base = os.path.join(capdir, f"cap_{cid:04d}")
            for suf, (ss, ee) in (("_s", (t0, t0 + 2 / FPS)), ("", (t0 + 2 / FPS, t1))):
                inputs += ["-i", base + suf + ".png"]; n += 1
                fc.append(f"{last}[{n}:v]overlay=(W-w)/2:{y}*H-h/2:enable='between(t,{ss:.3f},{ee:.3f})'[v{n}]"); last = f"[v{n}]"
        # audio: hook voice (if any) then silence, music under everything, ducked while the hook speaks
        if hau and h.get("keep_audio", True):
            fc.append(f"[0:a]atrim=start={ha}:end={hb},asetpts=PTS-STARTPTS,apad=whole_dur={T},aformat=sample_rates=48000:channel_layouts=stereo,loudnorm=I=-16:TP=-1.5[voice]")
        else:
            fc.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{T}[voice]")
        if MF:
            inputs += ["-stream_loop", "-1", "-i", MF]; n += 1
            # the demo part has no voice, so the track carries the ad: -13 dB, and the sidechain pulls it down while the hook speaks
            fc.append(f"[{n}:a]atrim=start={float(M.get('start', 0))},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,volume={float(M.get('gain_db', -13))}dB[m0]")
            fc.append("[voice]asplit[vk][vo];[m0][vk]sidechaincompress=threshold=0.02:ratio=6:attack=40:release=500:makeup=1[mus];[vo][mus]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[aout]")
        else:
            fc.append("[voice]anull[aout]")
        cmdl = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc), "-map", last, "-map", "[aout]", "-t", f"{T:.3f}",
                "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
        r = subprocess.run(cmdl, capture_output=True, text=True)
        return out, "ok" if r.returncode == 0 else "ERR " + r.stderr[-300:]
    results = list(ThreadPoolExecutor(JOBS).map(lambda j: build(*j), jobs))
    json.dump([{"file": rel(o), "status": s} for o, s in results], open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8"), indent=1)
    for o, s in results: print(f"{s:6} {rel(o)}")
    print(f"{sum(1 for _, s in results if s == 'ok')} built, {sum(1 for _, s in results if s == 'skip')} skipped, {sum(1 for _, s in results if s.startswith('ERR'))} failed → {OUT}")
else:
    sys.exit(__doc__)
