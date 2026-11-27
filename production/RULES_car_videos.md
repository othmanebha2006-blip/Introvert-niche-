# House rules: "Car Names Decoded" videos (@Mecmation)

These rules apply to every future video. They come from what worked in episode 2 (Mercedes-AMG) and from the reference samples.

## 0. Word timing (rule, 27 Nov 2026)
- **Always use forced alignment** (`force_align.py`, pocketsphinx with its bundled English model). It aligns the exact script text to the voice word by word.
- The old method (`align.py`, pause-based) drifted by up to 2 seconds on a voice with few pauses (Audi episode), so the visuals came before the voice.
- Names and numbers are spelled out the way they're spoken ("A6" = "a six", "TFSI" = "t f s i"), using the `REP` table in `force_align.py`.
- After aligning, compare against the voice before rendering.

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

## 4b. Explain once, no text cards (rule, 27 Nov 2026, from the user's notes on the Audi video)
- **Every idea gets one explanation only:** the voice says it, and the picture shows it with a car, a key, an icon or an animation. That's all.
- **No sentence cards** that repeat the idea in words. Examples of what is now banned:
  - "Q = SUV", "A = LOWER CARS", "HATCH · SALOON · ESTATE";
  - "NUMBER = POSITION IN THE RANGE", "HIGHER = BIGGER + PRICIER";
  - "COMPACT" / "LARGER" labels, and length labels repeated next to the cars.
- **What stays:**
  - the name's keys at the top (the letters and numbers being explained), circled at the moment they're spoken;
  - icons and animations (a pump, a plug, a battery, a staircase, a stamp);
  - a single word only when the picture can't show it (for example "RENN" / "SPORT" under the letters R S).
- The reference videos explain with few elements, so the viewer understands the idea at a glance. The video must not feel like code.
- In the pipeline: `compose2.TEXT_CARDS = False` (the default) switches off every `meaning()` card.

## 5. Captions (final rule, v4, 27 Nov 2026: matches the user's second sample exactly)
- Font: **Montserrat Black** (`production/fonts/Montserrat-Black.woff`), **ALL CAPS**, letter spacing tightened (-5.5%).
- Colours: **yellow fill `#F6E824`, thick black outline (≈10% of the text size), solid black shadow** offset down-right (≈7.5%).
- **1–3 words at a time:** words are joined if the chunk is 11 characters or fewer ("IF YOU", "WANT A", "THIS IS IT.", "AND THE"); longer words stand alone. A new chunk always starts after a comma or full stop.
- **Punctuation kept** ("COMING,", "THIS IS IT.").
- **No pop animation:** each chunk simply replaces the previous one. It stays until the next chunk, or disappears in a pause longer than 0.6 s.
- Text size 76 px (made a little smaller at the user's request), one line, centred above the character's head. The size shrinks automatically if the line is too wide.
- (Earlier styles, the white/black Helvetica of v3 and its inverted version, are no longer used.)

## 6. Sound (updated 27 Nov 2026)
- **A bass-heavy music bed plays the whole video**, about **12 dB under the voice**, with light ducking (25%). It never goes silent.
- **The same sound effects as before:**
  - a whoosh when a car enters or leaves;
  - a pop when a badge or card appears;
  - a stamp, a ding, an engine rev and a tyre squeal at key moments.
- **Effects volume is low** (peak at 12% of the mix, lowered at the user's request) so they never get in the way of the voice. The effects themselves stay the same; only their volume was turned down.
