# "Your Boyfriend…" Series: Style Guide

A breakdown of the 3 reference videos (the "Your girlfriend…" low-poly series) and a
spec for remaking the same format with the roles flipped: **"Your boyfriend…"**.

> Uploads analysed: 4 files, but 2 were byte-identical (`…7704048419274280205_v3` and `_v3_1`),
> so there are **3 unique videos**: V1 "Why are you making that face" (91.0 s), V2 "Would you
> still love me if I was a worm" (112.7 s), V3 "Which outfit looks better" (87.3 s).
> All three are 720×1280, 30 fps, 9:16 vertical.

---

## 1. What the format is (one sentence)

A deadpan **second-person narrator** ("You…") tells a short story about a small, everyday
relationship moment that spirals into absurd logic. It plays over **still low-poly 3D renders**
of two characters, with **big word-by-word captions** that put a **red highlight box** on the
word being spoken. It ends on one dry punchline over a close-up of the annoyed "you" character.

---

## 2. Visual style

### 2.1 Render look
- **Low-poly 3D**, like a clay/toy render: faceted surfaces with visible polygon facets on heads, arms and clothes.
  Soft global lighting, no hard shadows, gentle ambient occlusion. Slightly matte, no reflections.
- Characters have **no nose, no ears, no visible mouth detail**. The face is just
  **2 black dot eyes, 2 short thick black eyebrow strokes, 1 short mouth line**.
  All emotion is carried by the **eyebrow angle** and the mouth line (flat, slight smile, slight frown).
- Hands are blocky mitten-like low-poly hands with separate fingers.
- Proportions: big round head (about 1/4 of body height), simple box torso, straight tube legs, chunky dark-grey shoes.
- Lighting: warm lamp glow (top-left) against cool blue walls. The **warm/cool contrast** is the signature look.

### 2.2 Exact palette (sampled from frames)
| Element | Hex |
|---|---|
| "You" character T-shirt (orange) | `#FF6E17` |
| "You" character pants (royal blue) | `#1E4FD4` |
| Partner T-shirt (purple) | `#7D4E9E` |
| Partner pants (dark teal) | `#214657` |
| Skin | `#FDB680` |
| Partner hair (brown) | `#60311D` |
| Shoes (dark grey) | `#554E4D` |
| Living-room wall (bright blue) | `#4886DA` |
| Sofa (navy/denim blue) | `#0F3BAD` → `#223E64` in shadow |
| Coffee table / picture frame (warm wood) | `#B46528` / `#AE5B1F` |
| Lamp glow | `#FFEDAF` |
| Cutaway "imagination" background | flat light sky-blue, about `#7AAAE0` |
| Caption highlight box (red) | about `#E00010`, darker edge `#A80000` |

**Colour-role rule:** orange tee + blue jeans = **YOU** (the POV character). Purple tee + teal pants = **PARTNER**.
Keep this rule in the boyfriend version so the format is instantly recognisable (see §6).

### 2.3 Sets (all reused across episodes)
1. **Living room** (V1, V3): bright-blue wall; a framed low-poly landscape print (blue/green mountains, beige sky,
   pale sun) centred on the wall; a 3-seat navy fabric sofa; a warm table lamp on a small wooden side table at the
   left; a light wooden coffee table in the foreground; a cream shaggy rug. V3 adds a white door at the far left (used
   for "she disappears into the bedroom").
2. **Bedroom at night** (V2): dark navy-blue wall, warm wooden headboard, two white pillows, navy duvet with soft
   folds, wooden nightstands with glowing lamps on both sides.
3. **"Imagination" cutaways**: an isolated object or hand on a **plain light-blue seamless background** (no room).
   These visualise hypotheticals: a worm in his palm, the worm in a glass tank on a wooden table, the worm peeking
   out of a jeans pocket, him next to a washing machine, him with a magnifying glass over 4 identical worms.

### 2.4 Shot types (camera vocabulary)
All shots are eye-level and centred. No dutch angles, no fancy moves.

| Code | Shot | Use |
|---|---|---|
| **W** | Wide two-shot: both characters, full set, coffee table/bed foot in foreground | Opening hook, "stalemate" beats, partner asking something, time skips |
| **CU-Y** | Medium close-up of YOU: head + chest, cropped at the waist. Partner's shoulder sometimes visible at the frame edge | Narrator's inner thoughts, sarcastic lines, **always the last shot** |
| **CU-P** | Medium close-up of PARTNER: same framing | Partner's dialogue lines, worried looks |
| **M-Y** | Medium single of YOU: full seated body | Body-language beats ("you look away") |
| **INS** | Insert/cutaway on a light-blue void | Visualising hypotheticals or objects |
| **EMPTY** | Wide of the room with one character gone | "She disappears…", "Twenty minutes later…" |

Typical ratio per video: about 30 % W, 45 % CU-Y, 15 % CU-P, 10 % INS/other.

### 2.5 Motion
- Every shot is a **still image**. There is no lip-sync and no character animation.
- Each still has a **slow continuous push-in (Ken Burns)**, about 3–6 % scale over the shot, sometimes with a slight sideways drift.
  Measured frame-to-frame change is tiny and constant, so it's a smooth linear zoom.
- "Movement" is faked by **cutting to a new still with a different pose/expression**
  (for example, arms crossed, then palm-up gesture, then hand on forehead).

### 2.6 Editing rhythm
- **Hard cuts only.** No transitions, no zoom punches, no shakes, no stickers, no emojis.
- About **20–24 shots per video**, average shot length **4.2–4.7 s** (V1 ≈ 4.2 s, V2 ≈ 4.7 s, V3 ≈ 4.2 s).
- Cuts land at the start of a new sentence or right before a punch word.
- The same angle is often reused 2–3 times with a changed expression, which keeps continuity.
- Length: **87–113 s**.
- **No intro, no outro, no CTA, no logo.** The video ends on the punchline frame.

---

## 3. Captions (exact spec)

| Property | Value |
|---|---|
| Case | **ALL CAPS** |
| Font | Heavy, condensed, **italic** sans-serif. Closest free matches: **Barlow Semi Condensed ExtraBold Italic** or **Rubik Bold Italic** (CapCut: pick a bold italic sans and turn italic on) |
| Size | Cap height about 2 % of frame height. At 1080×1920 that's a font size of about **52–56 px** |
| Colour | White `#FFFFFF` |
| Shadow | Soft black drop shadow (about 70 % opacity, blur ~4 px, offset ~2 px down). **No hard outline** |
| Active-word highlight | Spoken word gets a **red rounded box** (`#E00010`, radius ~4 px, slightly darker edge). It moves word by word, synced to the voice, with a very short fade-in |
| Lines | **Max 2 lines**, about 3–6 words per caption page, centred |
| Page breaks | Split by **timing, not grammar**: "YOUR GIRLFRIEND ASKS / WHY YOU'RE MAKING" then "THAT FACE". Punch words get their own page: "FACE", "OFFENCE", "NORMAL", "ASLEEP.", "COUNT." |
| Position | Horizontally centred, **vertical centre at about 75 % of frame height** (y ≈ 1440 on 1920). Same spot in every shot, so it often sits over the character's chest/torso |
| Punctuation | V1 has none. V2/V3 keep periods, commas and question marks. Either is fine, just be consistent per video |
| Censoring | None. Swear words are written in full and also get the red box |

---

## 4. Audio

- **Narrator:** one voice reads everything, including the partner's dialogue (no "she said", no voice change).
  It's a deep male voice (median pitch about **93 Hz**, narrow range of 70–150 Hz), **completely flat and deadpan**,
  tired and dry, unhurried. About **2.2 words per second** with small pauses before punch words. It sounds like
  AI TTS (very even timbre and pacing).
- **Music:** a quiet, continuous, mellow **low pad/bass loop** under the whole video. It never stops (the audio never
  drops into silence), mixed well below the voice (about −18 to −24 dB under it). No noticeable sound effects.
- Loudness: about −19 dB mean, −2 dB peak.

**For the boyfriend version** (POV = the girlfriend), use a **flat, dry, deadpan female narrator**: low-ish,
slight vocal fry, zero excitement, same slow pacing. A deep male narrator reading "your boyfriend…" also works as
an ironic choice, but the female inner-monologue voice matches the POV better. Keep the same quiet pad music.

---

## 5. Writing formula (copy this structure exactly)

1. **Hook (wide shot):** `Your [girlfriend] + [does/asks something ordinary].` Present tense, second person.
   The keyword "GIRLFRIEND" (→ "BOYFRIEND") gets the first red highlight.
2. **Your inner reply (CU-Y):** a literal, logical answer that *should* end it.
   ("You're not making a face. That's just your fucking face.")
3. **Partner pushes (CU-P):** a short quoted question, read flatly with no dialogue tags. ("What's wrong?" "Nothing." "Then why do you look mad?")
4. **Escalation loop, 4–6 rounds:** every attempt to fix it makes it worse. The pattern is
   *You do X → now it means Y.* ("You look away, now you're avoiding the conversation. You look back, now you've got an attitude.")
5. **Legal/bureaucratic metaphors** for tiny domestic things. This is the signature joke engine:
   "committed a second offence", "performance notes", "need a lawyer", "being investigated for hypothetical worm homicide",
   "cross-examined over fabric", "entire interrogation", "your vote doesn't count".
6. **Profanity as rhythm:** "fucking" dropped mid-phrase **4–6 times per video**, always before the most mundane noun
   ("question of her fucking life", "fucking worm expert", "having a fucking head", "cross-examined over fucking fabric").
7. **Fake resolution:** it seems settled ("Okay. Good night." / "She's ready.").
8. **Twist + punchline (final CU-Y, angriest face):** one last turn, then a one-sentence verdict that sums up the absurdity:
   - "You've spent five minutes defending your face. Now you need a fucking lawyer for your eyebrows."
   - "You're about to fail a fucking worm identification test."
   - "You went through an entire interrogation to find out your vote doesn't count."

Length: **190–240 words** gives about 90–110 s at this pace. Sentences are short. Use lots of one-word replies ("Nothing." "Yes." "Sure." "Fuck.").

### Expression arc of the "you" character
Starts **neutral-annoyed** (one eyebrow angled down, flat mouth) → small **smirk** on "you smile / you say yes" beats →
**hand on forehead** when stressed → final shot **both eyebrows angled down hard** (angriest face of the video).
The partner stays **worried/innocent**: inner brows raised, small frown, hands in lap, arms crossed when suspicious,
palm-up hand when asking.

---

## 6. The flip: character designs for "Your boyfriend…"

POV switches to the girlfriend, so **she becomes the orange/blue "YOU" character** and the boyfriend becomes the purple/teal partner.

### YOU (girlfriend, POV, deadpan)
- Same low-poly toy style and the same blank face (dot eyes, thick brow strokes, mouth line).
- **Simple silhouette:** dark-brown hair in a **low messy bun or ponytail**, so the head stays as clean as the bald original.
- **Orange T-shirt `#FF6E17`, royal-blue jeans `#1E4FD4`, dark-grey chunky shoes.**
- Default expression: one eyebrow angled down, flat mouth: "unimpressed".

### PARTNER (boyfriend)
- Low-poly man, **short messy brown hair `#60311D`**, a bit taller and broader.
- **Purple T-shirt `#7D4E9E`, dark teal pants `#214657`**, dark-grey shoes.
- Default expression: earnest, eyebrows raised in the middle (innocent/confused), small frown or hopeful half-smile.

Keep both characters **100 % consistent** in every image: same hair, same clothes, same proportions.
Build a character sheet first (front, ¾, seated, close-up, 6 expressions) and use it as the reference image for every shot.

> Tip: design your own faces, hair and props rather than tracing the original creator's characters.
> Same format and style, but your channel owns its own cast. That also protects you from reuploads/claims.

---

## 7. Three ready-to-produce scripts

Shot codes from §2.4. `/` marks where a caption page breaks. **Bold** words are good candidates for a held red highlight.

### Script A: "I'm not hungry" (living room, about 95 s, 215 words)

| # | Shot | Visual | Voice-over |
|---|---|---|---|
| 1 | W | Both on sofa, takeout bag on coffee table, she has fries + burger, he has nothing | Your **boyfriend** says / he's not hungry. |
| 2 | CU-P | Boyfriend, innocent face | You ask twice. / He says he already **ate**. |
| 3 | CU-Y | Her, unimpressed | He did not already eat. / He had a **fucking** granola bar / at **noon**. |
| 4 | W | Food on table, she starts eating | You order for one. |
| 5 | CU-P | Boyfriend looking at the fries | The food arrives. / He watches your fries / like they **owe him money**. |
| 6 | INS | One fry held in his blocky fingers on light-blue void | Then he takes one. / "Just one." |
| 7 | CU-Y | Her, one brow down | It's never just one. / One is a **free trial**. |
| 8 | W | He's holding 3 fries, she stares | He takes another one. / "They're really good." / You know. / That's why you **ordered** them. |
| 9 | CU-P | Boyfriend, hopeful half-smile | "Can I have a bite / of your burger?" |
| 10 | CU-Y | Her, flat mouth | You weren't aware / this was a **shared fucking meal**. |
| 11 | INS | Burger with a giant bite missing, light-blue void | You say one bite. / He unhinges his jaw / like a **snake**. |
| 12 | CU-Y | Her, hand on forehead | Half the burger / is now in **witness protection**. |
| 13 | W | He leans back, satisfied | "Wow, I guess / I was hungry." |
| 14 | CU-Y | Her, smirk-that-isn't-a-smile | Yes. / That's the **thing** / you asked about. / Twice. |
| 15 | CU-P | Boyfriend, innocent | He suggests next time / you order **more**. |
| 16 | CU-Y | Her, both brows down | You did order more. / You ordered **for you**. |
| 17 | W | Empty food wrappers, she has nothing left | Ten minutes later, / your food is **gone**. |
| 18 | CU-P | Boyfriend, sincere | And he asks / if **you're** still hungry. |
| 19 | CU-Y (final, angriest) | Her, both brows hard down | You've been **robbed** / by a man / who wasn't **fucking hungry**. |

### Script B: "Man flu" (bedroom at night, about 100 s, 225 words)

| # | Shot | Visual | Voice-over |
|---|---|---|---|
| 1 | W | Bedroom, he's buried under the duvet, she's sitting up | Your **boyfriend** has / a slight cold. |
| 2 | CU-P | Him, eyes half-closed, tissue in hand | According to him, / he is **dying**. |
| 3 | CU-Y | Her, one brow down | You check his temperature. / **Thirty-seven point two**. |
| 4 | CU-P | Him, weak hand raised | He asks you / to remember him / as he **was**. |
| 5 | CU-Y | Her, flat | He sneezed **twice**. |
| 6 | W | He's pointing weakly at the kitchen | He asks for soup. / Not that soup. / The soup his mom makes. / You are **not** his **fucking mom**. |
| 7 | INS | Bowl of soup on a wooden tray, light-blue void | You make soup anyway. |
| 8 | CU-P | Him, sad eyebrows | He says it's **good**. / "Not as good as—" |
| 9 | CU-Y | Her, both brows down | He should **finish** / that sentence / very carefully. |
| 10 | W | He's lying flat, arm over his eyes | Then he asks / where his **will** is. |
| 11 | CU-Y | Her, unimpressed | He doesn't have a will. / He has / a **PlayStation** / and **forty dollars**. |
| 12 | CU-P | Him, serious | He leaves you / the PlayStation. |
| 13 | CU-Y | Her, smirk | His cousin / gets the **forty dollars**. |
| 14 | W | She's under the duvet now too, sneezing once | Two days later, / **you** get the cold. |
| 15 | CU-Y | Her, red nose, blank face | You go to **work**. / You do the **groceries**. / You take out the trash. |
| 16 | CU-P | Him, concerned | He asks / why you're being / so **dramatic**. |
| 17 | CU-Y (final, angriest) | Her, both brows hard down | You just watched a man / survive a **fucking cold** / like it was a **war**. |

### Script C: "Where's the ketchup?" (kitchen, new set, about 90 s, 200 words)
New set: same style, **blue wall, warm wood cabinets, white fridge**, a warm pendant lamp instead of a table lamp.

| # | Shot | Visual | Voice-over |
|---|---|---|---|
| 1 | W | He stands at the open fridge, she's on a chair at the table | Your **boyfriend** asks / where the ketchup is. |
| 2 | CU-Y | Her, flat | It's in the **fridge**. |
| 3 | INS | Open fridge, ketchup bottle front and centre at eye level, light-blue void | Where it has lived / for **two years**. |
| 4 | CU-P | Him, squinting into the fridge | He stands in front / of the open fridge / and **scans**. |
| 5 | CU-Y | Her, one brow down | Like he's looking at / a **fucking crime scene**. |
| 6 | CU-P | Him, palm up | "It's not here." |
| 7 | CU-Y | Her | It is here. / It's **red**. / It's the size of a **baby**. |
| 8 | W | He moves the milk, still not seeing it | He moves the milk. / Looks **behind** the milk. / Puts the milk **back**. |
| 9 | CU-P | Him, suspicious | "Did **you** move it?" |
| 10 | CU-Y | Her, both brows down | You are now a **suspect** / in the disappearance / of the ketchup. |
| 11 | W | She gets up and walks over | You get up. |
| 12 | INS | Her blocky hand grabbing the ketchup, one second | It takes **one second**. |
| 13 | CU-P | Him, genuinely amazed | He looks at you / like you just did / **magic**. |
| 14 | CU-P | Him, half-smile | "It wasn't there / **before**." |
| 15 | CU-Y | Her, flat | It was there **before**. / It was there / before **you** were. |
| 16 | W | He's at the table, holding mustard | Five minutes later / he asks / where the **mustard** is. |
| 17 | CU-Y (final, angriest) | Her, both brows hard down | You're running / a **fucking search and rescue** / for condiments. |

### More episode ideas (same formula)
- "Your boyfriend says 'I'm almost ready'" → he's still in the shower. "Almost" is a **legal grey area**.
- "Your boyfriend asks 'What do you want to eat?'" → rejects every option. You're **negotiating with a hostage-taker**.
- "Your boyfriend 'fixes' the sink without watching a tutorial" → now there's a **fountain**.
- "Your boyfriend says 'I'll be home in 10 minutes'" → 10 minutes is a **unit of time he invented**.
- "Your boyfriend asks if you'd still love him if he was a frog."
- "Your boyfriend picks the movie" → falls asleep in **minute 4**, then asks how it ended.
- "Your boyfriend is 'just resting his eyes'" → snoring, then denies it under **oath**.

---

## 8. Production workflow

1. **Script** (§5 formula, 190–240 words).
2. **Voice:** generate a deadpan TTS (e.g. ElevenLabs: a calm, flat, dry voice. Lower "stability" variation, no excitement,
   speed about 0.9). Export WAV. Add 0.2–0.4 s pauses before punch words.
3. **Shot list:** mark each line with W / CU-Y / CU-P / M-Y / INS / EMPTY (about 20 shots).
4. **Images:** generate stills at **1080×1920** using your character sheet as the reference (prompts in §9).
   Reuse the same "base" wide shot and edit only the expressions/poses for variety.
5. **Edit (CapCut / Premiere):**
   - Lay down the VO, then cut stills to the VO (hard cuts, ~3–6 s each).
   - Add a slow zoom on every clip: scale 100 % → 104–106 %, linear (CapCut: Animation → Combo/"Zoom in slow", or keyframes).
   - Add the music bed: soft lo-fi / ambient pad loop, ducked to about −20 dB under the voice, no SFX.
   - Captions: Auto-captions → style: ALL CAPS, bold italic sans, white, soft shadow, **"highlight active word" with a red box**
     (`#E00010`), max 2 lines, about 4 words per page, positioned at ~75 % height. Then fix page breaks so punch words stand alone.
6. **Export** 1080×1920, 30 fps. No end card.

---

## 9. AI image prompts

**Master style block (paste at the start of every prompt):**
```
Low-poly 3D render, toy-like stylized characters with visible faceted polygons, soft global illumination,
warm table-lamp glow contrasting with cool blue walls, matte materials, gentle ambient occlusion, no outlines,
clean and cute but deadpan, vertical 9:16, centered eye-level camera.
Faces: big round heads, two small black dot eyes, two short thick black eyebrow strokes, one short straight mouth line,
no nose, no ears detail.
```

**Character sheet (do this first):**
```
[STYLE] Character turnaround sheet on plain light-blue background: a young woman with a simple dark-brown low bun,
peach skin, orange t-shirt, royal-blue jeans, chunky dark-grey shoes, blocky low-poly hands. Front, three-quarter,
seated, close-up. Expression row: unimpressed (one eyebrow angled down, flat mouth), annoyed (both brows angled down),
tiny smirk, eyes closed, hand on forehead, arms crossed.
```
```
[STYLE] Character turnaround sheet on plain light-blue background: a young man with short messy brown hair, peach skin,
purple t-shirt, dark teal pants, chunky dark-grey shoes. Front, three-quarter, seated, close-up. Expression row:
innocent (inner eyebrows raised), confused, hopeful half-smile, pouting, sad, palm-up asking gesture.
```

**Shot templates:**
- **W (living room):** `[STYLE] Wide shot of a cozy living room: bright blue wall, framed low-poly mountain landscape print centered on the wall, navy fabric three-seat sofa, warm lamp on a small wooden side table at left, light wooden coffee table in the foreground, cream shaggy rug. [WOMAN ref] sits on the right of the sofa, [MAN ref] on the left. She looks unimpressed at him; he looks innocent.`
- **CU-Y:** `[STYLE] Medium close-up, head and chest, of [WOMAN ref] sitting on the navy sofa, bright blue wall and bottom of the framed print behind her, slightly off-center, [EXPRESSION].`
- **CU-P:** same as CU-Y with [MAN ref].
- **INS:** `[STYLE] Isolated close-up of [OBJECT / blocky low-poly hand holding OBJECT] on a plain flat light sky-blue seamless background, nothing else.`
- **Bedroom W:** `[STYLE] Night bedroom, dark navy-blue wall, wooden headboard, two white pillows, navy duvet with soft folds, wooden nightstands with glowing lamps on both sides, front view from the foot of the bed. [MAN] left, [WOMAN] right, lying under the duvet.`

**Consistency tips:** always attach the character sheet as the reference/"character reference" image, keep the same seed or
style reference for every shot in a video, and generate expression variants from the same base image (inpaint the face only)
so the background never changes between cuts.

---

## 10. Final checklist before posting
- [ ] Hook line starts with "Your boyfriend…", over a wide shot, with "BOYFRIEND" highlighted red
- [ ] Second person, present tense, flat deadpan voice, partner's lines read with no tags
- [ ] 4–6 escalation rounds, at least 2 legal/bureaucratic metaphors
- [ ] "fucking" 4–6×, before mundane nouns
- [ ] 18–24 still shots, hard cuts, slow zoom on every shot
- [ ] Captions: ALL CAPS, white bold italic, red active-word box, max 2 lines, at ~75 % height
- [ ] Orange/blue = YOU, purple/teal = boyfriend, both 100 % consistent
- [ ] Quiet pad music under everything, no SFX
- [ ] Final shot = close-up of YOU, angriest face, one-line verdict, then the video just ends

---

## Appendix: reconstructed scripts of the 3 originals (study material, don't reuse verbatim)
Read from the burned-in captions (audio transcription wasn't available). Shot codes in brackets.

**V1, "That face" (91 s, 20 cuts):** [W] Your girlfriend asks why you're making that face. [CU-Y] You're not making a face.
That's just your fucking face. [CU-P] "What's wrong?" "Nothing." "Then why do you look mad?" [CU-Y] You don't know. You weren't
supervising your eyebrows. [W] You tell her you're fine. [CU-P] Now she's looking at you harder. "Are you sure?" [CU-Y] You were,
before this fucking conversation. [W] You try to relax your face. [CU-Y] Unfortunately, relaxing your face looks exactly like your face.
[M-Y] So you smile. [W] "What's funny?" [M-Y] "Nothing." You stop smiling. [CU-P] "There, you did it again." [W, arms crossed] Apparently
your face has committed a second offence. You ask what she wants you to look like. [CU-P] "I don't know. Normal." [W] Great, you're
getting performance notes on having a fucking head. [M-Y] You look away, now you're avoiding the conversation. [W] You look back,
now you've got an attitude. At this point you actually are annoyed, [M-P] which is unfortunate because she notices immediately.
"See, I knew something was wrong." [CU-Y, angry] You've spent five minutes defending your face. Now you need a fucking lawyer for your eyebrows.

**V2, "Worm" (113 s, 23 cuts):** [W bed] Your girlfriend waits until you're almost asleep. [CU-P] Then she asks the most important question
of her fucking life. [INS hand+worm] "Would you still love me if I was a worm?" [CU-Y] You open one eye. "What?" [CU-P] "A worm. Would you
still love me?" [W] You say yes immediately. [CU-Y hand on forehead] You've learned things. [CU-P] "Would you keep me?" [CU-Y] Apparently
you're awake now. You say you'd put her in a little tank. [W] "A tank?" A nice tank. [INS tank] With dirt. [W] "So you'd just leave me in
there?" [CU-Y] You're not a fucking worm expert. [INS hand] You offer to carry her around [INS pocket] in your pocket. [W] "Sure.
[INS washing machine] What if you accidentally washed your pants?" [CU-Y] You're now being investigated for a hypothetical worm homicide.
[INS pocket] You say you'd check the pockets. [W] Every time. Every time she thinks about it. You close your eyes. "What if you met a
human girl?" [CU-Y] Fuck. [W] You say you wouldn't be interested. So you tell her you have a girlfriend. "Yes." [INS] And then show her a worm.
[CU-Y] You can already hear how this sounds. [W] You say you'd just stay home. [CU-P] "With me?" [W] With you. She smiles. Okay. Good night.
You're finally allowed to sleep. Then she rolls over. "Would you know it was me?" [INS magnifying glass + 4 worms] You're about to fail a
fucking worm identification test.

**V3, "Outfit" (87 s, 20 cuts):** [W] Your girlfriend asks which outfit looks better. [M-Y] You make the mistake of fucking answering.
The black one. [M-P] She looks at the red one. "What's wrong with this one?" [CU-Y] Nothing. You just like the black one better.
[W] "So this one looks bad." [CU-Y] You've somehow insulted a dress by complimenting a different dress. You explain that they both look good.
[W] "Then why did you pick the black one?" [CU-Y] Because she asked you to pick one. You keep that sentence inside your fucking head.
You say the red one looks great too. [M-P] "Fine, I'll wear this." [M-Y] You say, good choice. [W] She stops. "So now you like this one
better?" [CU-Y] You're being cross-examined over fucking fabric. You tell her she looks beautiful in either one. [M-P] She sighs.
[W] "You're no help." [EMPTY] She disappears into the bedroom, [W] comes back wearing something you've never seen before. "This one."
[CU-Y] You hesitate too long. [M-P arms crossed] "Never mind." [CU-Y] You haven't said a fucking word. [EMPTY] Twenty minutes later,
she's ready. [W, red dress] She's wearing the red one, the one she wanted before she fucking asked you. [CU-Y angry] You went through an
entire interrogation to find out your vote doesn't count.
