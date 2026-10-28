# -*- coding: utf-8 -*-
"""Final audio mix and loudness, two deliverables: with music and without.

    mix.py <video> <out_dir> [--voice voice.wav] [--music music.wav] [--sfx sfx.wav] [--bg -22] [--name final]

- voice defaults to the video's own audio track.
- music is ducked under the voice (sidechain) and sits --bg dB below it (default -22 dB: clearly audible, never competing).
- sfx is mixed at -6 dB.
- Output is normalised to -16 LUFS / -1.5 dBTP (social platforms), AAC 192 kbps.
Writes <out_dir>/<name>.mp4 and <name>_nomusic.mp4 (so a trending track can be added inside the app).
"""
import sys as _s; [x.reconfigure(encoding="utf-8", errors="replace") for x in (_s.stdout, _s.stderr) if hasattr(x, "reconfigure")]
import os, subprocess, sys

a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
video, outdir = a[0], a[1]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
voice, music, sfx = opt("--voice"), opt("--music"), opt("--sfx")
BG, name = float(opt("--bg", -22)), opt("--name", "final")
os.makedirs(outdir, exist_ok=True)

def build(with_music, out):
    inputs = ["-i", video]; idx = 1; chains = []
    if voice: inputs += ["-i", voice]; v = f"[{idx}:a]"; idx += 1
    else: v = "[0:a]"
    chains.append(f"{v}aformat=sample_rates=48000:channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=9[voice]")
    mix_in, nmix = ["[voice]"], 1
    if sfx:
        inputs += ["-i", sfx]; chains.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=-6dB[sfx]"); idx += 1
        mix_in.append("[sfx]"); nmix += 1
    if with_music and music:
        inputs += ["-stream_loop", "-1", "-i", music]
        chains.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={BG}dB[m0]"); idx += 1
        chains.append("[voice]asplit[vk][vo]"); mix_in[0] = "[vo]"
        chains.append("[m0][vk]sidechaincompress=threshold=0.02:ratio=6:attack=40:release=500:makeup=1[music]")
        mix_in.append("[music]"); nmix += 1
    chains.append("".join(mix_in) + f"amix=inputs={nmix}:duration=first:normalize=0,alimiter=limit=0.89[out]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-stats", *inputs, "-filter_complex", ";".join(chains), "-map", "0:v", "-map", "[out]",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True); print("→", out)

build(True, os.path.join(outdir, f"{name}.mp4"))
if music: build(False, os.path.join(outdir, f"{name}_nomusic.mp4"))
