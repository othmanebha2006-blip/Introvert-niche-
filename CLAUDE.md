# Project notes

## Video types
- **TYPE ONE** (car builds explained in the Criminal-TikTok visual style): when the user asks for a "type one" / "type 1" video,
  follow `type_one/TYPE_ONE_RULES.md` exactly. These rules are locked: do not change them unless the user explicitly asks.
  Reference result: `type_one/examples/R34_GTT_type_one.mp4`. Tooling: `type_one/scripts/`.
  Key rules: use only the user's images (never add icons/images of your own; missing visuals = caption only or give the user a prompt),
  the narrator images are never altered (only eyes/brows move), every element appears exactly on its spoken word.
- **TYPE TWO** (sleeper car build, monkeymechanic layout, TYPE ONE narrator): when the user asks for a "type two" / "type 2" video,
  follow `type_two/TYPE_TWO_RULES.md` exactly. Locked rules: change only if the user explicitly asks.
  Reference result: `type_two/C300_W204/C300_W204_type_two.mp4`. Renderer: `type_two/scripts/render_type_two_c300.py`.
  Key rules: white background, one-word caption mid-screen, only the featured car (never the expensive comparison car, never the
  rear shot), no B-roll — dyno is sound only with an audio-driven car shake right after "wake it up", car shine strobe at start /
  result / end, typed foundation text, only the user's four SFX in `type_two/sfx/`, voice cleaned to -14 LUFS and only real
  silences shortened (never cut on Whisper word times), top half never empty, mods kept away from screen edges.

## General working rules (both types)
- Never add images, icons, clips or sounds of my own. Text and captions are the only things I create; for anything else give the user prompts.
- Give image prompts in a file, one standalone prompt per item, in the glossy render style of the R34 images.
- Measure, don't guess: check audio levels/silences and text widths before delivering, and say what was verified.
