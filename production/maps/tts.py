"""Narration: Kokoro TTS (local, offline), one clip per beat, then timing for every beat.

usage: python3 tts.py <episode_dir> <kokoro_dir> [voice] [speed]
writes <episode_dir>/build/voice.wav and <episode_dir>/build/timing.json
"""
import json, sys, os, re
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

ep, kdir = sys.argv[1], sys.argv[2]
voice = sys.argv[3] if len(sys.argv) > 3 else "af_heart"
speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
out = os.path.join(ep, "build"); os.makedirs(out, exist_ok=True)
beats = json.load(open(os.path.join(ep, "script.json")))
k = Kokoro(os.path.join(kdir, "kokoro-v1.0.onnx"), os.path.join(kdir, "voices-v1.0.bin"))

SR = 24000
# spoken-only spellings; captions keep the real spelling
PRON = json.load(open(os.path.join(ep, "pronounce.json"))) if os.path.exists(os.path.join(ep, "pronounce.json")) else {}
LEAD = 0.35          # silence before the first word
GAP = 0.32           # pause between beats
SENT_GAP = 0.22      # pause between sentences inside a beat


def trim(a, thr=0.004):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    return a[max(0, idx[0] - 240): idx[-1] + 480]


pieces = [np.zeros(int(LEAD * SR), np.float32)]
t = LEAD
timing = []
for b in beats:
    sents = [s for s in re.split(r"(?<=[.?!])\s+", b["text"].strip()) if s]
    start = t
    words = []
    for si, s in enumerate(sents):
        spoken = s
        for kk, vv in PRON.items():
            spoken = spoken.replace(kk, vv)
        a, sr = k.create(spoken, voice=voice, speed=speed, lang="en-us")
        a = trim(a.astype(np.float32))
        dur = len(a) / sr
        # word timing: proportional to a syllable-ish weight, commas add a small pause weight
        toks = s.split()
        w = []
        for tok in toks:
            core = re.sub(r"[^A-Za-z0-9]", "", tok)
            wt = max(1.0, len(re.findall(r"[aeiouy]+", core.lower()))) + 0.35 + (0.9 if re.search(r"[,;:]$", tok) else 0)
            if re.fullmatch(r"\d+", core):
                wt = 1.2 * len(core)
            w.append(wt)
        W = sum(w); acc = 0.0
        for tok, wt in zip(toks, w):
            words.append(dict(w=tok, s=round(t + dur * acc / W, 3), e=round(t + dur * (acc + wt) / W, 3)))
            acc += wt
        pieces.append(a); t += dur
        if si < len(sents) - 1:
            pieces.append(np.zeros(int(SENT_GAP * SR), np.float32)); t += SENT_GAP
    timing.append(dict(id=b["id"], start=round(start, 3), end=round(t, 3), text=b["text"], words=words))
    pieces.append(np.zeros(int(GAP * SR), np.float32)); t += GAP
pieces.append(np.zeros(int(1.2 * SR), np.float32)); t += 1.2

audio = np.concatenate(pieces)
audio = audio / max(1e-6, np.abs(audio).max()) * 0.89
sf.write(os.path.join(out, "voice.wav"), audio, SR)
json.dump(dict(duration=round(t, 3), beats=timing), open(os.path.join(out, "timing.json"), "w"), indent=1)
print(f"voice {voice}: {t:.1f}s")
for b in timing:
    print(f"{b['start']:6.2f}-{b['end']:6.2f} {b['id']}")
