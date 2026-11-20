import sys, json, numpy as np, soundfile as sf
sys.path.insert(0, sys.argv[1]); from script import S
from kokoro_onnx import Kokoro
k = Kokoro(sys.argv[2] + "/kokoro-v1.0.onnx", sys.argv[2] + "/voices-v1.0.bin")
VOICE, SPEED = sys.argv[3], float(sys.argv[4]); out = sys.argv[5]
sr = 24000; parts = [np.zeros(int(0.35 * sr))]; t = 0.35; timing = []; beat = -1
for cap, say in S:
    if cap == "BEAT":
        beat += 1; continue
    a, sr = k.create(say, voice=VOICE, speed=SPEED, lang="en-gb" if VOICE[0] == "b" else "en-us")
    # trim leading/trailing silence
    nz = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, nz[0] - 240): nz[-1] + 480]
    timing.append({"beat": beat, "text": cap, "start": round(t, 3), "end": round(t + len(a) / sr, 3)})
    gap = 0.12 if cap[-1] in ",?" else 0.2
    parts += [a, np.zeros(int(gap * sr))]; t += len(a) / sr + gap
parts.append(np.zeros(int(1.0 * sr)))
sf.write(out + ".wav", np.concatenate(parts), sr)
json.dump(timing, open(out + ".json", "w"), indent=1); print("total", round(t, 2))
