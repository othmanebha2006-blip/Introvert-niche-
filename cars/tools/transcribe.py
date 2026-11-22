"""Word-level timestamps for a voiceover (faster-whisper, Whisper small int8).
Usage: python3 transcribe.py voice.mp3 words.json [model_dir]
The model came from npm packages @skillninja/shortmovie-telop-model-p0..p3 (concatenate model.bin.part0..3 into model.bin)."""
import sys, json, subprocess, numpy as np
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
model_dir = sys.argv[3] if len(sys.argv) > 3 else 'model'
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                     capture_output=True, check=True).stdout
audio = np.frombuffer(raw, np.float32)
segs, _ = WhisperModel(model_dir, device='cpu', compute_type='int8').transcribe(audio, language='en', word_timestamps=True)
W = []
for s in segs:
    for w in s.words:
        t = w.word.strip()
        # merge pieces Whisper splits off: "4" ".2" -> "4.2", "GT" "-T" -> "GT-T"
        if W and (t[:1] == '-' or (t[:1] in '.,' and t[1:2].isdigit())):
            W[-1]['w'] += t; W[-1]['e'] = round(w.end, 2)
        else:
            W.append(dict(w=t, s=round(w.start, 2), e=round(w.end, 2)))
json.dump(W, open(out, 'w'))
print(len(W), 'words')
