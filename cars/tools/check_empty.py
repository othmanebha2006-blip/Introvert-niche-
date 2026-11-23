"""Find moments where the graphics area is (almost) empty, so a viewer never sees the presenter 'just talking'.
usage: python3 check_empty.py <episode dir> [step seconds]
Renders every `step` s, measures how much of the area between the header and the caption (y 120..900) differs
from the plain background, and prints the moments below the threshold."""
import sys, os, importlib.util
import numpy as np

ep = os.path.abspath(sys.argv[1]); step = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2
sys.argv = ["x"]
sys.path.insert(0, ep)
spec = importlib.util.spec_from_file_location("compose", os.path.join(ep, "compose.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
import cairo

surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, C.W, C.H)
ctx = cairo.Context(surf); C.background(ctx); C.header(ctx); surf.flush()
base = np.ndarray((C.H, C.W, 4), np.uint8, surf.get_data()).copy()[120:900, :, :3].astype(np.int16)

bad = []
t = 0.0
while t < C.DUR:
    f = int(t * C.FPS)
    C.render(f, surf); surf.flush()
    a = np.ndarray((C.H, C.W, 4), np.uint8, surf.get_data())[120:900, :, :3].astype(np.int16)
    cov = (np.abs(a - base).max(2) > 30).mean()
    if cov < 0.035:
        bad.append((round(t, 2), round(cov * 100, 1)))
    t += step
print("empty moments (time s, % covered):", bad if bad else "none")
