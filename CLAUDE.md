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
  Key rules: everything drawn in code as vectors (no logos of real brands), the channel's presenter @Mecmation = the user's own animation clip `cars/character_mecmation/animation_reference.mov` used exactly as is (background keyed out, looped seamlessly frames 12-665 to the video length, `cars/lib/ref_presenter.py`),
  one big word caption at a time (yellow for keywords), badges and cars appear exactly on their spoken word, Kokoro voice bm_george at 1.22.
- **How to BUILD every car video (hook, script structure, shots per word):** follow `cars/REFERENCE_ANALYSIS.md`
  (analysis of the 3 reference videos the user gave). Quality/style/character stay ours. Key: 2.5 s hook
  "[Brand] [topic], explained in one minute." with the final complex badge shown up front with "?" (open loop), rule first,
  examples small->big, section signposts, one myth-bust, one surprising fact, "So a ... is ..." decodes the hook badge.
- **Car images:** reference cars are AI image-model illustrations, not code drawings. For every new script FIRST write
  `<episode>/IMAGE_PROMPTS.md` (style prompt + one prompt per needed image, file names, edit-prompts for versions) per
  `cars/CAR_ART_GUIDE.md`, then build the video from the images with `cars/lib/img_asset.py`.
