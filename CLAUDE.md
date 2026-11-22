# Project notes

## Video types
- **TYPE ONE** (car builds explained in the Criminal-TikTok visual style): when the user asks for a "type one" / "type 1" video,
  follow `type_one/TYPE_ONE_RULES.md` exactly. These rules are locked: do not change them unless the user explicitly asks.
  Reference result: `type_one/examples/R34_GTT_type_one.mp4`. Tooling: `type_one/scripts/`.
  Key rules: use only the user's images (never add icons/images of your own; missing visuals = caption only or give the user a prompt),
  the narrator images are never altered (only eyes/brows move), every element appears exactly on its spoken word.
- **BADGE DECODED / TYPE THREE** (car badge & model names explained, the Audi episode style): when the user asks for a
  "badge decoded" / "type three" / "type 3" video, or another video "like the Audi one", follow `cars/BADGE_DECODED_RULES.md` exactly.
  These rules are locked: do not change them unless the user explicitly asks.
  Reference result: `videos/cars_ep1_audi_badges_mecmation.mp4` (code: `cars/audi_ep1/`, shared drawing code: `cars/lib/`).
  Key rules: everything drawn in code as vectors (no logos of real brands), the channel's presenter @Mecmation = the user's exact image, never redrawn or altered (`cars/lib/mecmation_img.py` cuts it into original-pixel layers; only mouth, eyes, brows, a slight head tilt and the arms move, like `cars/character_mecmation/animation_reference.mov`; hand gestures chosen from the meaning of each phrase via `CUES`),
  one big word caption at a time (yellow for keywords), badges and cars appear exactly on their spoken word, Kokoro voice bm_george at 1.22.
