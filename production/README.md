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

## Episode 2 pipeline ("I'll plan the date this time")
- `chars/clean/`: every character cutout re-matted with BiRefNet + alpha matting, eroded 2 px, feathered 1 px, white spill removed,
  trapped background holes cleared (`ep2/matte.py`). Verified: 0 white edge pixels on black/red (`../review/halo_test_*`).
- `ep2/scene2.py`: set builders (living room with the user's painting `tex/painting_inner.png`, car interior, mattress store, gas station) and props.
- `ep2/scene3.py`: renders the backgrounds (no characters) + foreground layers (coffee table, dashboard/wheel) + props.
- `ep2/compose3.py`: shot list. Places the user's exact character cutouts between background and foreground layers, adds props, slow zoom and captions (`captions_lib.py`).
- `ep2/chars3d.py`: experimental 3D character builder. NOT used (characters must stay the user's exact images); kept only because scene2 imports it.

### Episode 2 v2 (animated)
- `ep2/faces.py`: talk (open mouth) + blink (closed eyes) sprites painted on the clean cutouts, in the characters' own style.
- `ep2/puppet.py`: cut-out puppetry on the user's images (his arm: holding phone / raised / pointing). Saved in `ep2/pup/`.
- `ep2/compose4.py`: per-frame animation (voice-driven mouth flaps on quoted lines, blinks, breathing), per-scene lighting grade + rim light,
  drop/contact shadows, props in hand, eased push-in, captions.
