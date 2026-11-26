# Car image prompts (for ChatGPT image generation)

Generate **one image per car**. Save each one with the **file name shown** and send them all to Claude. Claude then:
- crops each car;
- scales it to its real length (true scale is kept);
- finds the wheels so they still spin;
- swaps it into the video. Nothing else in the video changes.

## Rules for every image
These are already included in each prompt below:
- **Side view, front facing RIGHT.** The camera is level with the car, like a car configurator.
- **The whole car is in frame, with both wheels fully visible.** Nothing is cut off.
- **Transparent background** (PNG). If transparency doesn't work, ask for a pure white background.
- **No shadow on the ground, no text, no logo watermark, blank number plate.**
- **The same style for every car** (the style block below), so all the cars look like one set.

---

## Episode 1: Lexus

**IS.png**
```
Side-profile illustration of a 2024 Lexus IS 350 F SPORT sedan in Heat Blue metallic, exact real proportions and design details (spindle grille, slim L-shaped headlights, F SPORT wheels), pure side view at 0 degrees, front of the car facing RIGHT, camera level with the car, whole car in frame with both wheels fully visible. Style: realistic automotive illustration, clean thin black ink outlines, coloured-pencil and marker shading with soft hatching, white paper highlights on the body, tinted grey windows with the interior faintly visible, glossy realistic wheels. Transparent background, no ground shadow, no text, blank white number plate, high detail, 2048 px wide.
```

**ES.png**: same prompt, but replace the first line with:
`Side-profile illustration of a 2025 Lexus ES 350 sedan in Sonic Iridium silver, exact real proportions and design details,`

**LS.png**:
`Side-profile illustration of a 2024 Lexus LS 500 luxury sedan in Graphite Black, exact real proportions and design details,`

**RCF.png**:
`Side-profile illustration of a 2024 Lexus RC F coupe in Ultra White with orange brake calipers, exact real proportions and design details,`

**LC.png**:
`Side-profile illustration of a 2024 Lexus LC 500 coupe in Infrared red, exact real proportions and design details,`

**LFA.png**:
`Side-profile illustration of a 2012 Lexus LFA supercar in Pearl Yellow with its fixed rear wing, exact real proportions and design details,`

**UX.png**:
`Side-profile illustration of a 2025 Lexus UX 300h compact crossover in Copper Crest with black wheel-arch cladding, exact real proportions and design details,`

**NX.png**:
`Side-profile illustration of a 2024 Lexus NX 450h+ F SPORT SUV in Graphite Black, exact real proportions and design details,`

**RX.png**:
`Side-profile illustration of a 2024 Lexus RX 500h F SPORT Performance SUV in dark blue metallic, exact real proportions and design details,`

**GX.png**:
`Side-profile illustration of a 2024 Lexus GX 550 boxy off-road SUV in Nori Green Pearl with roof rails, exact real proportions and design details,`

**LX.png**:
`Side-profile illustration of a 2024 Lexus LX 600 full-size SUV in Sonic Quartz white with roof rails, exact real proportions and design details,`

---

## Episode 2: Mercedes-AMG

**A35.png**
```
Side-profile illustration of a 2024 Mercedes-AMG A 35 hatchback in Sun Yellow, exact real proportions and design details (AMG grille, AMG wheels, quad exhaust tips), pure side view at 0 degrees, front of the car facing RIGHT, camera level with the car, whole car in frame with both wheels fully visible. Style: realistic automotive illustration, clean thin black ink outlines, coloured-pencil and marker shading with soft hatching, white paper highlights on the body, tinted grey windows with the interior faintly visible, glossy realistic wheels. Transparent background, no ground shadow, no text, blank white number plate, high detail, 2048 px wide.
```

**C43.png**: same prompt, but replace the first line with:
`Side-profile illustration of a 2024 Mercedes-AMG C 43 sedan in Selenite Grey, exact real proportions and design details,`

**C63.png**:
`Side-profile illustration of a 2024 Mercedes-AMG C 63 S E PERFORMANCE sedan in Spectral Blue with red brake calipers, exact real proportions and design details,`

**C300.png**:
`Side-profile illustration of a 2024 Mercedes-Benz C 300 sedan with the AMG Line package (sporty bumpers, larger AMG-style wheels) in Polar White, exact real proportions and design details,`

**E53.png**:
`Side-profile illustration of a 2025 Mercedes-AMG E 53 HYBRID sedan in Obsidian Black, exact real proportions and design details,`

**S63.png**:
`Side-profile illustration of a 2024 Mercedes-AMG S 63 E PERFORMANCE sedan in Hyacinth Red metallic, exact real proportions and design details,`

**GT.png**:
`Side-profile illustration of a 2024 Mercedes-AMG GT 55 coupe in Green Hell Magno with its rear spoiler, exact real proportions and design details,`

**GLC63.png**:
`Side-profile illustration of a 2024 Mercedes-AMG GLC 63 S E PERFORMANCE SUV in High-Tech Silver with red brake calipers, exact real proportions and design details,`

**GLE53.png**:
`Side-profile illustration of a 2024 Mercedes-AMG GLE 53 SUV in Cavansite Blue with roof rails, exact real proportions and design details,`

**G63.png**:
`Side-profile illustration of a 2025 Mercedes-AMG G 63 in Night Black Magno with the side-exit exhausts and the spare wheel on the rear door, exact real proportions and design details,`

---

### Tips
- **Generate the first car, and if you like it, ask ChatGPT:** "Use exactly the same style for the next car". That keeps the whole set consistent.
- **If ChatGPT draws the car facing left,** say: "Flip it, the front must face right." Claude can also mirror it automatically, but the badges and text would come out reversed.
- **For a fully photo-realistic look** instead of the illustrated reference style, replace the "Style:" part with:
  `Style: photorealistic studio render, soft even studio lighting, realistic paint reflections.`
