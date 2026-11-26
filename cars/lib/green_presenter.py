"""Presenter from a green-screen clip of the user's character (any fps), frame-synced to its own audio.

The clip's time t is shown at video time t (frame = round(t * clip_fps)). The green is keyed out with a soft edge
and green spill is removed; nothing else in the character changes. After the clip ends the last frame is held.
Framing (head to knees, like the reference videos) is set with `scale`, `center_x`, `top_y` in clip pixels.
"""
import os, glob, math, subprocess
from concurrent.futures import ProcessPoolExecutor
import numpy as np, cairo
from PIL import Image

CROP_Y = (60, 1500)          # rows of the clip that are kept (head .. below the knees)


def _key_green(rgb):
    im = rgb.astype(np.float32)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    spill = g - np.maximum(r, b)                     # how green a pixel is
    alpha = 1.0 - np.clip((spill - 18.0) / 55.0, 0, 1)
    # despill: the character is grey/white/black, so green may not exceed the other channels
    g2 = np.minimum(g, np.maximum(r, b) + 4)
    out = np.dstack([r, g2, b, alpha * 255]).clip(0, 255).astype(np.uint8)
    return out


def _job(args):
    src, dst = args
    if os.path.exists(dst):
        return
    rgb = np.asarray(Image.open(src).convert("RGB"))[CROP_Y[0]:CROP_Y[1]]
    Image.fromarray(_key_green(rgb), "RGBA").save(dst, compress_level=1)


def prepare(clip, cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    raw = os.path.join(cache_dir, "raw")
    if not os.path.isdir(raw) or not os.listdir(raw):
        os.makedirs(raw, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", clip, "-vsync", "0", os.path.join(raw, "%05d.png")], check=True)
    srcs = sorted(glob.glob(os.path.join(raw, "*.png")))
    jobs = [(s, os.path.join(cache_dir, f"k_{i:05d}.png")) for i, s in enumerate(srcs)]
    with ProcessPoolExecutor() as ex:
        list(ex.map(_job, jobs, chunksize=8))
    return len(jobs)


class GreenPresenter:
    def __init__(self, clip, cache_dir, clip_fps=24.0, scale=0.73, center_x=520.0, top_y=110.0, jump=None):
        """jump=(j, i): when the clip is used for a longer voice, play to frame j then continue from the matching
        frame i (< j) - pick a pair that looks the same so the jump is invisible."""
        self.dir = cache_dir
        self.n = prepare(clip, cache_dir)
        self.fps, self.k, self.cx, self.top, self.jump = clip_fps, scale, center_x, top_y, jump

    def draw(self, ctx, f, x, head_top_screen, video_fps=30):
        idx = int(round(f / video_fps * self.fps))
        if self.jump and idx > self.jump[0]:
            idx -= self.jump[0] - self.jump[1]
        idx = min(idx, self.n - 1)
        surf = cairo.ImageSurface.create_from_png(os.path.join(self.dir, f"k_{idx:05d}.png"))
        k = self.k
        ctx.save()
        ctx.translate(x - self.cx * k, head_top_screen - (self.top - CROP_Y[0]) * k)
        ctx.scale(k, k)
        ctx.set_source_surface(surf, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_GOOD)
        ctx.paint()
        ctx.restore()
