# Car Names Decoded #1: Lexus

Builds `videos/cars_ep1_lexus_names.mp4`: 1080×1920, 30 fps, about 76 s, mastered to -14 LUFS.

## Inputs
- `voiceover.mp3`: the voiceover.
- `script.txt`: the exact words of the voiceover. The word timing is aligned from this text.
- The @Mecmation character animation (white background, 1080×1920). Pass its path to `character.py`.

## Build
```bash
python3 align.py voiceover.mp3 script.txt words.json   # word timings (no ASR needed)
python3 cars.py build/svg                              # Lexus side profiles to true scale (SVG)
node render_svgs.js build/svg build/png 2              # SVG -> transparent PNG (Chromium)
python3 character.py <character.mp4> build/char        # pose cut-outs, mouth shapes, blink
python3 compose.py --frames 3,20,40                    # optional: check stills
python3 compose.py                                     # build/video_noaudio.mp4
python3 audio.py                                       # build/mix.wav (voice + SFX + ducked music)
ffmpeg -i build/video_noaudio.mp4 -i build/mix.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1:LRA=7" -c:a aac -b:a 256k -shortest ../../videos/cars_ep1_lexus_names.mp4
```

## How it works
- **Alignment** (`align.py`): the word timing comes from the voice's loudness. Each comma or full stop in the script is placed on a pause in the audio, using a dynamic-programming pass that keeps the speaking rate even. Each word inside a phrase gets time in proportion to its syllables. Accuracy is about ±0.15 s.
- **Cars** (`cars.py`): each model is drawn from its real published length, height, wheelbase and front overhang. Every hero shot uses one scale (0.172 px/mm), so the cars are true size relative to each other; the SUV line-up uses 0.15 px/mm. Real paint names are used (Heat Blue, Sonic Iridium, Infrared, Pearl Yellow, etc.). The F-performance cars get orange calipers.
- **To swap in better car art:** drop a side-view PNG with a transparent background, front facing right, at `build/png/<KEY>.png`. Keep the same length scale (0.4 px/mm), or update `meta.json`. Then re-run `compose.py`.
- **Character** (`character.py`): white is keyed out only where it is background; the teeth, the logo and the shoe stripes are kept. The 919 source frames reduce to 193 unique body poses. The lip-sync is chosen per frame from the voice's loudness, using five mouth shapes, plus random blinks.
- **Compositor** (`compose.py`): has the grid background, the header with a section progress bar, keycap badges, true-scale cars with spinning wheels, speed lines and a suspension settle, a dimension line, sketch icons, stamps, 1–3 word captions with the active word highlighted and colour-coded keywords, a cheat-sheet end card, and a loop back to the opening frame.
