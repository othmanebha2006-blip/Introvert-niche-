"""Render an episode: frames (skia) -> ffmpeg, in parallel chunks, then mux narration + music + sfx.

usage: python3 render.py <episode_dir> [--preview t1,t2,...] [--from S --to E] [--workers N]
"""
import sys, os, json, importlib.util, subprocess, argparse, time
import numpy as np, skia

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E

ap = argparse.ArgumentParser()
ap.add_argument("ep"); ap.add_argument("--preview"); ap.add_argument("--from", dest="t0", type=float, default=0)
ap.add_argument("--to", dest="t1", type=float); ap.add_argument("--workers", type=int, default=4)
ap.add_argument("--chunk", type=int, default=-1); ap.add_argument("--out")
args = ap.parse_args()
EP = os.path.abspath(args.ep); BUILD = os.path.join(EP, "build")
timing = json.load(open(os.path.join(BUILD, "timing.json")))
DUR = timing["duration"]


def load_scene():
    spec = importlib.util.spec_from_file_location("shots", os.path.join(EP, "shots.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    geo = E.Geo(os.path.join(BUILD, "geo.pkl"))
    return mod.Scene(geo, timing)


def render_frame(sc, mr, caps, T, arr):
    surf = skia.Surface(arr)
    cv = surf.getCanvas()
    m, s = sc.cam.matrix(T)
    vint = sc.vint(T)
    mr.draw(cv, m, s, vint)
    d = E.Draw(cv, m, s, E.style_mix(vint), T)
    sc.overlay(d, T)
    mr.finish(cv, vint)
    sc.post(d, T)
    caps.draw(cv, T, sc.caption_alpha(T))
    return arr


def frames_to(path, frames):
    sc = load_scene(); mr = E.MapRenderer(sc.geo); caps = E.Captions(timing)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{E.W}x{E.H}",
                           "-r", str(E.FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
                           "-pix_fmt", "yuv420p", "-profile:v", "high", path], stdin=subprocess.PIPE)
    arr = np.zeros((E.H, E.W, 4), np.uint8)
    for i in frames:
        arr[:] = 0
        render_frame(sc, mr, caps, i / E.FPS, arr)
        ff.stdin.write(arr.tobytes())
    ff.stdin.close(); ff.wait()


if args.preview:
    sc = load_scene(); mr = E.MapRenderer(sc.geo); caps = E.Captions(timing)
    from PIL import Image
    os.makedirs(os.path.join(BUILD, "preview"), exist_ok=True)
    for t in [float(x) for x in args.preview.split(",")]:
        arr = np.zeros((E.H, E.W, 4), np.uint8)
        t1 = time.time(); render_frame(sc, mr, caps, t, arr)
        p = os.path.join(BUILD, "preview", f"t{t:06.2f}.png")
        Image.fromarray(arr[..., :3]).save(p); print(p, f"{time.time()-t1:.2f}s")
    sys.exit()

n_total = int(round(DUR * E.FPS))
f0 = int(args.t0 * E.FPS); f1 = int(args.t1 * E.FPS) if args.t1 else n_total
if args.chunk >= 0:
    frames_to(args.out, range(f0, f1)); sys.exit()

# parallel chunks
N = args.workers
edges = np.linspace(f0, f1, N + 1).astype(int)
procs = []
t_start = time.time()
for k in range(N):
    out = os.path.join(BUILD, f"chunk{k}.mp4")
    procs.append(subprocess.Popen([sys.executable, __file__, EP, "--from", str(edges[k] / E.FPS), "--to", str(edges[k + 1] / E.FPS),
                                   "--chunk", str(k), "--out", out]))
for p in procs:
    p.wait()
print(f"frames: {time.time()-t_start:.0f}s")
with open(os.path.join(BUILD, "chunks.txt"), "w") as f:
    for k in range(N):
        f.write(f"file 'chunk{k}.mp4'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(BUILD, "chunks.txt"),
                "-c", "copy", os.path.join(BUILD, "video_noaudio.mp4")], check=True)
print("video:", os.path.join(BUILD, "video_noaudio.mp4"))
