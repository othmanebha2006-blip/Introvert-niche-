# Production pipeline (episode 1: "Your boyfriend wants to hang out")

1. `transcribe.py`: voice → timed lines (sherpa-onnx Whisper small.en + Silero VAD, models from the sherpa-onnx GitHub releases).
2. `cutout.py`: cuts every pose out of the character images in `../characters/` (transparent PNGs).
   `chars/cut/` holds the extra expressions painted on the high-res references (girlfriend "soft/regret", boyfriend "happy" and "surprised").
3. `scene.py`: Blender (`pip install bpy`) builds the living room, the foreground coffee table layer and the props, and renders them.
   Usage: `python3 scene.py -- <workdir> room_wide room_table room_med room_cu_a room_cu_b prop_basket ...`
4. `compose.py`: the shot list + caption timing. Composites characters onto renders, adds a 5 % slow push-in and
   word-by-word captions (Barlow Semi Condensed ExtraBold Italic, white, red active-word box), and pipes the frames to ffmpeg.
   Then mux the voice: `ffmpeg -i video_noaudio.mp4 -i voice.mp3 -map 0:v -map 1:a -c:v copy -c:a aac -shortest out.mp4`.

For a new episode: change `SEG` (lines + times from step 1) and `SHOTS` in `compose.py`, and add any new props to `scene.py`.
