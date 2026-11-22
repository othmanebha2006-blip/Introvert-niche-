# Map-explainer pipeline ("Why is X…?" history/geography shorts)

A format modelled on the animated map explainers: a calm narrator, a vintage map, glowing routes, small 3D icons,
date title cards and phrase captions. Everything is drawn as vectors in every frame at **1080×1920, 30 fps**,
so it stays sharp at any zoom level (the reference is 576×1024).

## Assets (downloaded once, not committed)
Put them in one folder and point `MAP_ASSETS` at it:
- `geo/`: Natural Earth GeoJSON (public domain), from `raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/`:
  `ne_10m_land, ne_10m_lakes, ne_10m_lakes_north_america, ne_10m_rivers_lake_centerlines, ne_10m_rivers_north_america,
  ne_10m_admin_0_boundary_lines_land, ne_10m_admin_1_states_provinces_lines, ne_10m_admin_1_states_provinces_lakes,
  ne_50m_land, ne_50m_lakes, ne_50m_admin_0_countries_lakes`
- `fonts/`: from google/fonts (OFL): `IMFeENrm28P.ttf`, `IMFeENit28P.ttf` (IM Fell English), `CormorantGaramond[wght].ttf`, `Inter[opsz,wght].ttf`
- `icons/`: Microsoft Fluent Emoji 3D PNGs (MIT license), from `microsoft/fluentui-emoji/main/assets/<Name>/3D/<name>_3d.png`
- `tts/`: Kokoro v1.0 (Apache-2.0): `kokoro-v1.0.onnx`, `voices-v1.0.bin` from the kokoro-onnx GitHub releases

Python packages: `pip install skia-python shapely pyproj kokoro-onnx soundfile scipy` (+ `apt-get install libegl1` for skia).

## Steps
```bash
export MAP_ASSETS=/path/to/assets
EP=ep1_ottawa
python3 tts.py $EP $MAP_ASSETS/tts af_heart 1.0            # narration + word timings  -> build/voice.wav, timing.json
python3 geo.py $MAP_ASSETS/geo $EP/build/geo.pkl -76 45     # projected map data, centred on lon/lat
./preview.sh $EP 3.5,20,41.5,90 $EP/build/sheet.jpg 4       # still frames to check the layout
python3 render.py $EP --workers 4                           # frames -> build/video_noaudio.mp4
python3 audio.py $EP                                        # music + sfx + ducking -> build/mix.wav
./finish.sh $EP ../../videos/<name>.mp4                     # mux + loudness -14 LUFS
```

## New episode
1. `script.json`: list of beats `{id, text}`. Target **230–270 words** (about 100 s). Short sentences, one idea per beat.
   `pronounce.json` fixes names the voice says wrong (spoken spelling only; captions keep the real one).
2. `shots.py`: a `Scene` class with
   - `shots`: camera moves `(start, duration, lon, lat, width_km, drift)`; use `self.w(beat, word)` to sync to a word
   - `vint(T)`: 0 = modern colour map, 1 = vintage parchment (the switch is the "going back in time" device)
   - `overlay(d, T)`: what appears when (dots, labels, arcs, glowing rivers/routes, regions, icons, titles, bars, cards)
   - `sfx`: `(time, kind, gain)`, kinds: pop, whoosh, rewind, fire, boom, ding, title, draw, paper
   Copy `ep1_ottawa/shots.py` and replace the beats; the toolkit is in `engine.py` (`Draw` class).
