# House rules: "Car Names Decoded" videos (@Mecmation)

These rules apply to every future video. They come from what worked in episode 2 (Mercedes-AMG) and from the reference samples.

## 1. Format
- 1080×1920, 30 fps, about 60–75 s, final loudness -14 LUFS (true peak -1 dB).
- Pale grey background with a grid (graph paper). Monospace header at the top: `CAR NAMES DECODED · #N` with the brand on the right, plus a section progress bar under it.

## 2. Character
- The @Mecmation character is **always shown full body**, from hat to shoes, below the caption.
- Lip-sync comes from the voice itself, using 5 mouth shapes plus random blinks and a slight body sway.

## 3. Cars
- **Realistic images generated in ChatGPT** (prompts in `CAR_IMAGE_PROMPTS.md`). Pure side view, front facing right, every car in the same style.
- **Check before importing:** the right body for the model, and the right badge (ChatGPT sometimes copies the previous car's badge).
- **Imported with `import_cars.py`:**
  - background removed;
  - car scaled to its real length, so sizes compare correctly;
  - wheel centre found from the rotational symmetry of the hub;
  - brake calipers stay still while the wheels turn.

## 4. Motion (from the reference analysis)
- **A car is never parked:**
  - wheels turning, with speed lines, road dashes and dust behind;
  - enters from the left, leaves to the right as the next car arrives.
- **Something new happens every 0.5–1 second**, tied to the word being spoken.
- **Props interact with the car:** a crown drops on the roof, a plug flies into the charge port, the car climbs a hill, a burnout, the rev counter climbs.
- **Hook:**
  - from the first frame, a car already moving;
  - the brand's name or logo flies in fast, with a yellow circle drawn around it;
  - the camera pulls back to the whole range.
- **Clear explanation:**
  - a decoder bar at the top showing the name, with the current part circled;
  - a "part = meaning" card under it.
- **Ending:** a cheat sheet that sums up the whole system, then "FOLLOW @Mecmation". The last frame matches the first, so the video loops.

## 5. Captions (new rule, v3)
- Font: **Helvetica/Arial Bold** (FreeSans Bold), **white fill, thick black outline (≈8.5% of the text size), solid black shadow** offset down-right (≈7%).
- **1–2 words at a time:** two short words are joined if together they are 7 characters or fewer ("in one", "and the"); longer words stand alone.
- **Words exactly as spoken:** the case and punctuation are kept ("minute,", "born,"). No uppercase, no colours.
- **No pop animation:** each chunk simply replaces the previous one. It stays until the next chunk, or disappears in a pause longer than 0.6 s.
- One line, centred above the character's head. The size shrinks automatically if the line is too wide.

## 6. Sound (new rule)
- **A bass-heavy music bed plays the whole video**, about **12 dB under the voice**, with light ducking (25%). It never goes silent.
- **Sound effects are soft and short:**
  - a whoosh when a car enters or leaves;
  - a soft pop when a badge or card appears;
  - a stamp, a ding and an engine rev only at key moments.
- **They stay well under the voice:** the voice always leads.
