# Car-badge explainer series ("Badge Decoded")

Everything is drawn in code as vectors (pycairo), so every frame is sharp at 1080x1920.

- `lib/ink.py`: hand-drawn ink lines that wobble slightly every few frames.
- `lib/car.py`: side-view cars (sedan, hatch, avant, fastback, suv, rally) with paint, RS/S/S line options and turning wheels.
- `lib/character.py`: the presenter (beanie, round glasses, teal hoodie) with poses, eyebrows, blinks and mouth shapes.
- `lib/widgets.py`: badges, chips, captions, icons, sound-effect events.
- `audi_ep1/script.py`: the voiceover lines. `voice.py` makes `voice.wav` + `voice.json` (sentence times) with Kokoro TTS (offline).
- `audi_ep1/compose.py`: the scenes. `python3 compose.py out.mp4` renders the video with voice and sound effects.
  `HANDLE=@name python3 compose.py out.mp4` sets the handle on the end card. `--preview 5 10 20` writes still PNGs.

Setup: `pip install pycairo kokoro-onnx soundfile`; fonts in `fonts/` copied to `~/.fonts`; Kokoro model files
(`kokoro-v1.0.onnx`, `voices-v1.0.bin`) from the thewh1teagle/kokoro-onnx GitHub release `model-files-v1.0`.
Voice: `python3 voice.py . <model dir> bm_george 1.22 voice`.
