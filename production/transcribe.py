import sherpa_onnx, soundfile as sf, sys, json
M=sys.argv[1]; wav=sys.argv[2]
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f'{M}/sherpa-onnx-whisper-small.en/small.en-encoder.int8.onnx',decoder=f'{M}/sherpa-onnx-whisper-small.en/small.en-decoder.int8.onnx',tokens=f'{M}/sherpa-onnx-whisper-small.en/small.en-tokens.txt',language='en',task='transcribe',num_threads=4)
cfg=sherpa_onnx.VadModelConfig(); cfg.silero_vad.model=f'{M}/silero_vad.onnx'; cfg.silero_vad.min_silence_duration=0.15; cfg.silero_vad.min_speech_duration=0.1; cfg.silero_vad.threshold=0.4; cfg.sample_rate=16000
vad=sherpa_onnx.VoiceActivityDetector(cfg,buffer_size_in_seconds=120)
a,sr=sf.read(wav,dtype='float32'); out=[]
w=512
for i in range(0,len(a),w):
    vad.accept_waveform(a[i:i+w])
    while not vad.empty():
        seg=vad.front; s=rec.create_stream(); s.accept_waveform(sr,seg.samples); rec.decode_stream(s)
        st=seg.start/sr; en=st+len(seg.samples)/sr; t=s.result.text.strip()
        out.append(dict(start=round(st,2),end=round(en,2),text=t)); print(f'{st:6.2f}-{en:6.2f} {t}'); vad.pop()
vad.flush()
while not vad.empty():
    seg=vad.front; s=rec.create_stream(); s.accept_waveform(sr,seg.samples); rec.decode_stream(s)
    st=seg.start/sr; en=st+len(seg.samples)/sr; t=s.result.text.strip(); out.append(dict(start=round(st,2),end=round(en,2),text=t)); print(f'{st:6.2f}-{en:6.2f} {t}'); vad.pop()
json.dump(out,open(sys.argv[3],'w'),indent=1)
