"""Shorten the pauses in a voiceover so it flows: python3 tighten.py in.(mp3|wav) words.json out.wav
Silences below -40 dBFS that last >= 0.12 s are cut down to 0.07 s inside a sentence and 0.15 s after
a sentence end (word ending in . ? !). Leading/trailing silence trimmed to 0.05 s. 8 ms crossfade at each cut."""
import sys, json, subprocess, numpy as np, soundfile as sf
src, words_json, out = sys.argv[1:4]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
a = np.frombuffer(raw, np.float32).copy(); sr = 48000
W = json.load(open(words_json))
hop = sr // 100
db = 20 * np.log10(np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)]) + 1e-9)
low = db < -40
gaps = []; i = 0
while i < len(low):
    if low[i]:
        j = i
        while j < len(low) and low[j]: j += 1
        if j - i >= 12 or i == 0 or j == len(low): gaps.append((i * hop, j * hop))
        i = j
    else:
        i += 1
def sentence_end_before(t):
    prev = [w for w in W if w["e"] <= t + 0.05]
    return bool(prev) and prev[-1]["w"][-1:] in ".?!"
xf = int(0.008 * sr)
keep = []; pos = 0; cuts = []
for s, e in gaps:
    if s == 0: target = int(0.05 * sr)
    elif e >= len(a) - hop: target = int(0.05 * sr)
    else: target = int((0.15 if sentence_end_before(s / sr) else 0.07) * sr)
    if e - s <= target: continue
    mid = s + target // 2
    keep.append((pos, mid)); pos = e - (target - target // 2)
    cuts.append((s / sr, e / sr, target / sr))
keep.append((pos, len(a)))
pieces = [a[s:e] for s, e in keep if e > s]
outa = pieces[0]
for p in pieces[1:]:
    if len(outa) > xf and len(p) > xf:
        fade = np.linspace(0, 1, xf, dtype=np.float32)
        outa = np.concatenate([outa[:-xf], outa[-xf:] * (1 - fade) + p[:xf] * fade, p[xf:]])
    else:
        outa = np.concatenate([outa, p])
sf.write(out, outa, sr)
print(f"{len(cuts)} pauses shortened: {len(a)/sr:.2f}s -> {len(outa)/sr:.2f}s")
