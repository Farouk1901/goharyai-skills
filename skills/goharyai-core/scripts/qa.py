# -*- coding: utf-8 -*-
# needs: faster_whisper
"""Pre-delivery check. Run it on every final file; fix what it flags before showing the video.

    qa.py <final.mp4> [--script script.txt] [--lang en|ar] [--min-lufs -18] [--max-lufs -13]

Checks: duration and size, loudness (EBU R128 integrated / true peak), black or frozen frames,
and — if --script is given — transcribes the final audio and reports the words that differ
(a cut that chopped a word, a mispronounced name). Exit code 1 when something fails.
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import difflib, json, os, re, subprocess, sys, tempfile

a = sys.argv[1:]
if not a: sys.exit(__doc__)
video = a[0]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
script, lang = opt("--script"), opt("--lang", "en")
LO, HI = float(opt("--min-lufs", -18)), float(opt("--max-lufs", -13))
fails = []

probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_type,width,height,r_frame_rate", "-of", "json", video]))
dur = float(probe["format"]["duration"]); v = next(s for s in probe["streams"] if s["codec_type"] == "video")
has_audio = any(s["codec_type"] == "audio" for s in probe["streams"])
print(f"file: {os.path.basename(video)}  {v['width']}x{v['height']}  {dur:.1f}s  {int(probe['format']['size']) / 1e6:.1f} MB  fps={v['r_frame_rate']}")
if not has_audio: fails.append("no audio track")

if has_audio:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", err); P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)
    if I:
        lufs, peak = float(I[-1]), float(P[-1]) if P else 0
        print(f"loudness: {lufs:.1f} LUFS  true peak {peak:.1f} dBTP")
        if not LO <= lufs <= HI: fails.append(f"loudness {lufs:.1f} LUFS outside {LO}..{HI}")
        if peak > -0.5: fails.append(f"true peak {peak:.1f} dBTP (clipping risk)")

err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-an", "-vf", "blackdetect=d=0.3:pic_th=0.98,freezedetect=n=-60dB:d=1.5", "-f", "null", "-"], capture_output=True, text=True).stderr
blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)
freezes = re.findall(r"freeze_start: ([\d.]+)", err)
if blacks: fails.append("black frames at " + ", ".join(f"{float(s):.1f}-{float(e):.1f}s" for s, e in blacks))
if freezes: print("frozen video (≥1.5 s) at " + ", ".join(f"{float(s):.1f}s" for s in freezes) + " — fine if intended (still card)")

if script and has_audio:
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([sys.executable, os.path.join(here, "transcribe.py"), video, tmp, "--lang", lang, "--model", "small" if lang == "en" else "medium"], check=True, capture_output=True)
    heard = [w["w"] for w in json.load(open(tmp, encoding="utf-8"))]; os.unlink(tmp)
    norm = lambda s: re.sub(r"[^\w']", "", s.lower())
    want = [norm(w) for w in open(script, encoding="utf-8").read().split() if norm(w)]
    got = [norm(w) for w in heard if norm(w)]
    sm = difflib.SequenceMatcher(a=want, b=got, autojunk=False)
    diffs = [(op, " ".join(want[i1:i2]), " ".join(got[j1:j2])) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
    ratio = sm.ratio()
    print(f"script match: {ratio * 100:.0f}%  ({len(diffs)} differences)")
    for op, w, g in diffs[:12]: print(f"  {op:8} script: '{w}'  heard: '{g}'")
    if ratio < 0.9: fails.append(f"script match {ratio * 100:.0f}% < 90% — listen for cut words or wrong names")

print("RESULT:", "✅ pass" if not fails else "❌ " + " | ".join(fails))
sys.exit(1 if fails else 0)
